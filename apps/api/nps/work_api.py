import asyncio
import json
from uuid import UUID
from fastapi import APIRouter, File, Header, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from sqlalchemy import select
from nps.api import Actor, DB, ReviewInput, serialize
from nps.auth import audit, authorize_project, org_scope, require_admin, user_from_token
from nps.config import settings
from nps.contracts import Contract, SlidePlanContract
from nps.db import SessionLocal
from nps.errors import DomainError
from nps.jobs import broker, cancel_job, create_job, retry_job, snapshot
from nps.models import (
    Artifact,
    ArtifactVersion,
    Chunk,
    Document,
    DocumentVersion,
    GenerationJob,
    ParseResult,
    Project,
    SlidePlan,
)
from nps.plans import require_approved, review_plan, update_plan, validate_plan
from nps.storage import storage
from nps.upload import quarantine_upload

router = APIRouter(prefix="/api/v1")
ws_router = APIRouter()


def scoped(db, user, model, ident, roles=None, owner=False):
    row = db.get(model, str(ident))
    if not row:
        raise DomainError("RESOURCE_NOT_FOUND", 404)
    authorize_project(db, user, row.project_id, roles, owner)
    return row


@router.get("/projects/{project_id}/documents")
def documents(project_id: UUID, db: DB, user: Actor):
    authorize_project(db, user, str(project_id))
    return [
        serialize(d)
        for d in db.scalars(
            select(Document).where(Document.project_id == str(project_id), Document.deleted.is_(False))
        )
    ]


@router.post("/projects/{project_id}/documents", status_code=202)
async def upload(project_id: UUID, db: DB, user: Actor, file: UploadFile = File()):
    project = authorize_project(db, user, str(project_id))
    filename = file.filename
    payload = await quarantine_upload(file)
    doc = Document(project_id=project.id, title=filename)
    db.add(doc)
    db.flush()
    payload["document_id"] = doc.id
    job = create_job(db, user, project.id, "upload", payload)
    return {"document_id": doc.id, "scan_status": "PENDING", "job": snapshot(db, job)}


@router.post("/documents/{document_id}/versions", status_code=202)
async def upload_version(document_id: UUID, db: DB, user: Actor, file: UploadFile = File()):
    doc = scoped(db, user, Document, document_id)
    payload = await quarantine_upload(file)
    payload["document_id"] = doc.id
    job = create_job(db, user, doc.project_id, "upload", payload)
    return {"document_id": doc.id, "scan_status": "PENDING", "job": snapshot(db, job)}


@router.get("/documents/{document_id}")
def document_detail(document_id: UUID, db: DB, user: Actor):
    doc = scoped(db, user, Document, document_id)
    if doc.deleted:
        raise DomainError("RESOURCE_NOT_FOUND", 404)
    version = db.get(DocumentVersion, doc.current_version_id) if doc.current_version_id else None
    return {**serialize(doc), "current_version": serialize(version) if version else None}


@router.get("/documents/{document_id}/versions")
def document_versions(document_id: UUID, db: DB, user: Actor):
    doc = scoped(db, user, Document, document_id)
    return [
        serialize(v)
        for v in db.scalars(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == doc.id)
            .order_by(DocumentVersion.version)
        )
    ]


@router.get("/documents/{document_id}/download")
def document_download(document_id: UUID, db: DB, user: Actor, version_id: UUID | None = None):
    doc = scoped(db, user, Document, document_id)
    version = db.get(DocumentVersion, str(version_id) if version_id else doc.current_version_id)
    if not version or version.document_id != doc.id:
        raise DomainError("AUTH_FORBIDDEN", 403)
    audit(db, user, "DOCUMENT_DOWNLOAD", doc.id, doc.project_id)
    db.commit()
    return FileResponse(
        storage.path(version.storage_key), filename=f"document-{version.version}{version.extension}"
    )


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: UUID, db: DB, user: Actor):
    doc = scoped(db, user, Document, document_id, owner=True)
    doc.deleted = True
    audit(db, user, "DOCUMENT_DELETE", doc.id, doc.project_id)
    db.commit()


def analyze_start(db, user, doc, kind, key):
    if doc.deleted or not doc.current_version_id:
        raise DomainError("DOC_NOT_CLEAN", 409)
    version = db.get(DocumentVersion, doc.current_version_id)
    if version.scan_status != "CLEAN":
        raise DomainError("DOC_NOT_CLEAN", 409)
    job = create_job(db, user, doc.project_id, kind, {"document_id": doc.id, "version_id": version.id}, key)
    return snapshot(db, job)


@router.post("/documents/{document_id}/analyze", status_code=202)
def analyze(document_id: UUID, db: DB, user: Actor, idempotency_key: str | None = Header(default=None)):
    return analyze_start(db, user, scoped(db, user, Document, document_id), "analyze", idempotency_key)


@router.post("/documents/{document_id}/slide-plans", status_code=202)
def new_plan(document_id: UUID, db: DB, user: Actor, idempotency_key: str | None = Header(default=None)):
    return analyze_start(db, user, scoped(db, user, Document, document_id), "plan", idempotency_key)


@router.get("/documents/{document_id}/parse-result")
def parse_result(document_id: UUID, db: DB, user: Actor):
    doc = scoped(db, user, Document, document_id)
    result = db.scalar(select(ParseResult).where(ParseResult.document_version_id == doc.current_version_id))
    if not result:
        raise DomainError("PARSE_REQUIRED", 409)
    return result.data


@router.get("/documents/{document_id}/chunks")
def chunks(document_id: UUID, db: DB, user: Actor):
    doc = scoped(db, user, Document, document_id)
    return [c.data for c in db.scalars(select(Chunk).where(Chunk.version_id == doc.current_version_id))]


@router.get("/documents/{document_id}/slide-plans")
def plans(document_id: UUID, db: DB, user: Actor):
    doc = scoped(db, user, Document, document_id)
    return [serialize(p) for p in db.scalars(select(SlidePlan).where(SlidePlan.document_id == doc.id))]


@router.get("/slide-plans/{plan_id}")
def plan_detail(plan_id: UUID, db: DB, user: Actor):
    return serialize(scoped(db, user, SlidePlan, plan_id))


@router.patch("/slide-plans/{plan_id}")
def plan_edit(plan_id: UUID, data: SlidePlanContract, db: DB, user: Actor):
    plan = scoped(db, user, SlidePlan, plan_id)
    project = db.get(Project, plan.project_id)
    if user.role != "Reviewer" and user.id != project.owner_id:
        raise DomainError("AUTH_FORBIDDEN", 403)
    update_plan(db, user, plan, data)
    db.commit()
    return serialize(plan)


@router.post("/slide-plans/{plan_id}/validate")
def plan_validate(plan_id: UUID, db: DB, user: Actor):
    return validate_plan(db, scoped(db, user, SlidePlan, plan_id))


@router.post("/slide-plans/{plan_id}/approve")
def plan_approve(plan_id: UUID, data: ReviewInput, db: DB, user: Actor):
    plan = scoped(db, user, SlidePlan, plan_id, roles={"Reviewer"})
    review_plan(db, user, plan, data)
    db.commit()
    return serialize(plan)


def generation(db, user, plan, kind, key):
    require_approved(plan)
    validate_plan(db, plan)
    if kind == "video" and not settings().prototype_review_pass:
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
    job = create_job(db, user, plan.project_id, kind, {"plan_id": plan.id, "plan_version": plan.version}, key)
    return snapshot(db, job)


@router.post("/slide-plans/{plan_id}/generate-ppt", status_code=202)
def generate_ppt(plan_id: UUID, db: DB, user: Actor, idempotency_key: str | None = Header(default=None)):
    return generation(db, user, scoped(db, user, SlidePlan, plan_id), "ppt", idempotency_key)


@router.post("/slide-plans/{plan_id}/generate-video", status_code=202)
def generate_video(plan_id: UUID, db: DB, user: Actor, idempotency_key: str | None = Header(default=None)):
    return generation(db, user, scoped(db, user, SlidePlan, plan_id), "video", idempotency_key)


@router.post("/slide-plans/{plan_id}/generate-images", status_code=202)
def generate_images(plan_id: UUID, db: DB, user: Actor, idempotency_key: str | None = Header(default=None)):
    return generation(db, user, scoped(db, user, SlidePlan, plan_id), "image", idempotency_key)


@router.get("/projects/{project_id}/jobs")
def jobs(project_id: UUID, db: DB, user: Actor):
    authorize_project(db, user, str(project_id))
    return [
        snapshot(db, j)
        for j in db.scalars(
            select(GenerationJob)
            .where(GenerationJob.project_id == str(project_id))
            .order_by(GenerationJob.created_at.desc())
            .limit(100)
        )
    ]


@router.get("/jobs/{job_id}")
def job_detail(job_id: UUID, db: DB, user: Actor):
    return snapshot(db, scoped(db, user, GenerationJob, job_id))


@router.post("/jobs/{job_id}/cancel")
def job_cancel(job_id: UUID, db: DB, user: Actor):
    return snapshot(db, cancel_job(db, user, scoped(db, user, GenerationJob, job_id)))


class RetryInput(Contract):
    resume_from_step: str | None = None


@router.post("/jobs/{job_id}/retry", status_code=202)
def job_retry(job_id: UUID, data: RetryInput, db: DB, user: Actor):
    return snapshot(db, retry_job(db, user, scoped(db, user, GenerationJob, job_id), data.resume_from_step))


@router.get("/admin/queues")
def queues(db: DB, user: Actor):
    require_admin(user)
    try:
        r = broker()
        workers = [json.loads(r.get(k)) for k in r.scan_iter("worker:*") if r.get(k)]
    except Exception:
        raise DomainError("QUEUE_UNAVAILABLE", 503) from None
    allowed = select(Project.id).where(Project.org_id.in_(org_scope(db, user)))
    rows = db.scalars(select(GenerationJob).where(GenerationJob.project_id.in_(allowed))).all()
    return {
        "workers": workers,
        "counts": {state: sum(j.state == state for j in rows) for state in {j.state for j in rows}},
    }


@router.post("/admin/templates", status_code=202)
async def template_upload(project_id: UUID, db: DB, user: Actor, file: UploadFile = File()):
    require_admin(user, system=True)
    project = authorize_project(db, user, str(project_id))
    name = file.filename
    payload = await quarantine_upload(file, template=True)
    if payload["extension"] != ".pptx":
        raise DomainError("TEMPLATE_INVALID", 422)
    payload.update(name=name, config=json.loads(settings().template_policy.read_text(encoding="utf-8")))
    return snapshot(db, create_job(db, user, project.id, "template", payload))


@ws_router.websocket("/ws/v1/jobs/{job_id}")
async def job_socket(websocket: WebSocket, job_id: UUID):
    origin = websocket.headers.get("origin")
    if origin and origin not in settings().allowed_origins.split(","):
        await websocket.close(code=4403)
        return
    await websocket.accept()
    try:
        # Authenticate in first frame so tokens never enter URLs/access logs.
        auth = await asyncio.wait_for(websocket.receive_json(), timeout=5)
        token = auth.get("access_token", "")
        last_seq = -1
        while True:
            with SessionLocal() as db:
                user = user_from_token(db, token)
                job = scoped(db, user, GenerationJob, job_id)
                event = snapshot(db, job)
            if event["seq"] != last_seq:
                await websocket.send_json(event)
                last_seq = event["seq"]
            # Receive disconnect promptly while preserving state polling cadence.
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=0.25)
            except asyncio.TimeoutError:
                pass
    except DomainError as exc:
        await websocket.close(code=4401 if exc.status == 401 else 4403)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
