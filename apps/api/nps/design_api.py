from uuid import UUID
from fastapi import APIRouter, File, UploadFile
from nps.api import Actor, DB, serialize
from nps.auth import authorize_project
from nps.jobs import create_job, snapshot
from nps.themes import visible_templates
from nps.upload import quarantine_upload
from nps.errors import DomainError

router = APIRouter(prefix="/api/v1")


@router.get("/design-library")
def library(db: DB, user: Actor):
    return {
        "learning_method": "style-memory-retrieval",
        "model_fine_tuned": False,
        "themes": [
            serialize(t)
            for t in visible_templates(db, user.org_id)
            if t.config.get("design_engine") == "editorial-2"
        ],
    }


@router.post("/projects/{project_id}/design-references", status_code=202)
async def reference_upload(project_id: UUID, db: DB, user: Actor, file: UploadFile = File()):
    project = authorize_project(db, user, str(project_id))
    name = file.filename or "참고 PPT"
    payload = await quarantine_upload(file, template=True)
    if payload["extension"] != ".pptx":
        from nps.storage import storage

        storage.path(payload["quarantine_key"]).unlink(missing_ok=True)
        raise DomainError("THEME_PPTX_REQUIRED", 422)
    payload.update(name=name[:120], org_id=project.org_id)
    job = create_job(db, user, project.id, "design_reference", payload)
    return {"job": snapshot(db, job), "status": "QUARANTINED"}
