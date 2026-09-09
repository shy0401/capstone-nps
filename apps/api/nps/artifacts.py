from uuid import UUID
from fastapi import APIRouter, Header
from fastapi.responses import FileResponse
from sqlalchemy import select
from nps.api import Actor, DB, ReviewInput, serialize
from nps.auth import audit, authorize_project
from nps.contracts import Contract
from nps.errors import DomainError
from nps.jobs import create_job, snapshot
from nps.models import Approval, Artifact, ArtifactVersion, Review, SlidePlan
from nps.plans import require_approved
from nps.storage import storage
from nps.work_api import scoped

router = APIRouter(prefix="/api/v1")


def eligible(version):
    return (
        version.qa_status == "PASS"
        and version.approval_status == "APPROVED"
        and version.provenance.get("official_template", False)
        and not version.provenance.get("mock", True)
        and not version.provenance.get("video_mock", False)
    )


def version_public(version):
    data = serialize(version)
    provenance = dict(data["provenance"])
    provenance.pop("qa_key", None)
    if "storyboard" in provenance:
        provenance["storyboard"] = {
            **provenance["storyboard"],
            "scenes": [
                {k: v for k, v in s.items() if k not in {"storage_key", "preview_key"}}
                for s in provenance["storyboard"]["scenes"]
            ],
        }
    data["provenance"] = provenance
    return {**data, "official_eligible": eligible(version)}


@router.get("/projects/{project_id}/artifacts")
def artifact_list(project_id: UUID, db: DB, user: Actor):
    authorize_project(db, user, str(project_id))
    return [
        {**serialize(a), "current_version": version_public(db.get(ArtifactVersion, a.current_version_id))}
        for a in db.scalars(select(Artifact).where(Artifact.project_id == str(project_id)))
        if a.current_version_id
    ]


@router.get("/artifacts/{artifact_id}")
def detail(artifact_id: UUID, db: DB, user: Actor):
    artifact = scoped(db, user, Artifact, artifact_id)
    return {
        **serialize(artifact),
        "versions": [
            version_public(v)
            for v in db.scalars(
                select(ArtifactVersion)
                .where(ArtifactVersion.artifact_id == artifact.id)
                .order_by(ArtifactVersion.version.desc())
            )
        ],
    }


@router.get("/artifacts/{artifact_id}/download")
def download(artifact_id: UUID, db: DB, user: Actor, version_id: UUID | None = None):
    artifact = scoped(db, user, Artifact, artifact_id)
    version = db.get(ArtifactVersion, str(version_id) if version_id else artifact.current_version_id)
    if not version or version.artifact_id != artifact.id:
        raise DomainError("AUTH_FORBIDDEN", 403)
    audit(
        db, user, "ARTIFACT_DOWNLOAD", artifact.id, artifact.project_id, detail={"version": version.version}
    )
    db.commit()
    suffix = ".pptx" if artifact.type == "PPTX" else ".mp4"
    return FileResponse(
        storage.path(version.storage_key),
        filename=f"{version.approval_status}-v{version.version}{suffix}",
        media_type="video/mp4"
        if suffix == ".mp4"
        else "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "X-Artifact-State": version.approval_status,
            "X-Official-Eligible": str(eligible(version)).lower(),
        },
    )


def review(db, user, artifact, data, approval=False):
    version = db.get(ArtifactVersion, artifact.current_version_id)
    if data.version != version.version:
        raise DomainError("VERSION_CONFLICT", 409)
    if data.decision == "approve" and version.qa_status != "PASS":
        raise DomainError("QA_FAILED", 409)
    db.add(
        Review(
            project_id=artifact.project_id,
            target_type="artifact",
            target_id=version.id,
            version=version.version,
            reviewer_id=user.id,
            decision=data.decision,
            comment=data.comment,
        )
    )
    if data.decision == "approve":
        version.approval_status = "APPROVED" if approval else "REVIEWED"
        if approval:
            db.add(
                Approval(
                    project_id=artifact.project_id,
                    target_type="artifact",
                    target_id=version.id,
                    version=version.version,
                    approver_id=user.id,
                )
            )
    else:
        version.approval_status = "DRAFT"
    audit(
        db,
        user,
        "APPROVE" if approval else "REVIEW",
        version.id,
        artifact.project_id,
        detail={"version": version.version},
    )
    db.commit()
    return version_public(version)


@router.post("/artifacts/{artifact_id}/reviews")
def review_artifact(artifact_id: UUID, data: ReviewInput, db: DB, user: Actor):
    return review(db, user, scoped(db, user, Artifact, artifact_id, roles={"Reviewer"}), data)


@router.post("/artifacts/{artifact_id}/approve")
def approve_artifact(artifact_id: UUID, data: ReviewInput, db: DB, user: Actor):
    return review(db, user, scoped(db, user, Artifact, artifact_id, roles={"Reviewer"}), data, approval=True)


class RegenerateInput(Contract):
    slide_id: UUID


@router.post("/artifacts/{artifact_id}/regenerate", status_code=202)
def regenerate(
    artifact_id: UUID,
    data: RegenerateInput,
    db: DB,
    user: Actor,
    idempotency_key: str | None = Header(default=None),
):
    artifact = scoped(db, user, Artifact, artifact_id)
    plan = db.get(SlidePlan, artifact.plan_id)
    require_approved(plan)
    if artifact.type == "MP4":
        candidates = db.scalars(
            select(Artifact).where(Artifact.plan_id == plan.id, Artifact.type == "PPTX")
        ).all()
        if not any(
            (v := db.get(ArtifactVersion, a.current_version_id))
            and v.approval_status in {"REVIEWED", "APPROVED"}
            and v.provenance.get("plan_version") == plan.version
            for a in candidates
        ):
            raise DomainError("PPT_REVIEW_REQUIRED", 409)
    if str(data.slide_id) not in {s["slide_id"] for s in plan.data["slides"]}:
        raise DomainError("SLIDE_NOT_FOUND", 404)
    job = create_job(
        db,
        user,
        artifact.project_id,
        "ppt" if artifact.type == "PPTX" else "video",
        {
            "plan_id": plan.id,
            "plan_version": plan.version,
            "artifact_id": artifact.id,
            "slide_id": str(data.slide_id),
        },
        idempotency_key,
    )
    return snapshot(db, job)
