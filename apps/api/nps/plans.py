from sqlalchemy import select
from nps.auth import audit
from nps.chunking import validate_evidence
from nps.contracts import SemanticChunk, SlidePlanContract
from nps.errors import DomainError
from nps.models import Approval, Chunk, Review, Slide


def validate_plan(db, plan):
    parsed = SlidePlanContract.model_validate(plan.data)
    chunks = [
        SemanticChunk.model_validate(c.data)
        for c in db.scalars(
            select(Chunk).where(Chunk.version_id.in_([str(v) for v in parsed.document_versions]))
        )
    ]
    return validate_evidence(parsed, chunks)


def require_approved(plan):
    if plan.status != "APPROVED" or plan.approved_version != plan.version:
        raise DomainError("PLAN_REVIEW_REQUIRED", 409)


def save_slides(db, plan):
    for slide in plan.data["slides"]:
        existing = db.scalar(
            select(Slide).where(
                Slide.plan_id == plan.id,
                Slide.slide_id == slide["slide_id"],
                Slide.version == slide["version"],
            )
        )
        if not existing:
            db.add(Slide(plan_id=plan.id, slide_id=slide["slide_id"], version=slide["version"], data=slide))


def update_plan(db, user, plan, data):
    if (
        str(data.plan_id) != plan.id
        or data.document_versions != SlidePlanContract.model_validate(plan.data).document_versions
    ):
        raise DomainError("PLAN_IDENTITY_IMMUTABLE", 422)
    old_slides = {s["slide_id"]: s for s in plan.data["slides"]}
    updated = data.model_dump(mode="json")
    updated["mock"], updated["provenance"] = plan.data["mock"], plan.data["provenance"]
    for slide in updated["slides"]:
        old = old_slides.get(slide["slide_id"])
        if old:
            compare = {k: v for k, v in slide.items() if k != "version"}
            slide["version"] = old["version"] + (compare != {k: v for k, v in old.items() if k != "version"})
        else:
            slide["version"] = 1
    plan.data = updated
    validate_plan(db, plan)
    plan.version += 1
    plan.status, plan.approved_version = "DRAFT", None
    save_slides(db, plan)
    audit(db, user, "PLAN_UPDATE", plan.id, plan.project_id, detail={"version": plan.version})
    return plan


def review_plan(db, user, plan, data):
    if data.version != plan.version:
        raise DomainError("VERSION_CONFLICT", 409)
    validate_plan(db, plan)
    db.add(
        Review(
            project_id=plan.project_id,
            target_type="plan",
            target_id=plan.id,
            version=plan.version,
            reviewer_id=user.id,
            decision=data.decision,
            comment=data.comment,
        )
    )
    if data.decision == "approve":
        plan.status, plan.approved_version = "APPROVED", plan.version
        db.add(
            Approval(
                project_id=plan.project_id,
                target_type="plan",
                target_id=plan.id,
                version=plan.version,
                approver_id=user.id,
            )
        )
    else:
        plan.status, plan.approved_version = "REJECTED", None
    audit(
        db, user, "PLAN_" + data.decision.upper(), plan.id, plan.project_id, detail={"version": plan.version}
    )
