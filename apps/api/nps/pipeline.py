"""Step implementations with durable checkpoints and version-specific review gates."""

from sqlalchemy import func, select
from nps.auth import audit
from nps.config import settings
from nps.chunking import chunk_document
from nps.contracts import NormalizedDocument, SlidePlanContract
from nps.errors import DomainError
from nps.jobs import PIPELINES, enqueue, transition
from nps.llm import LLMClient
from nps.models import (
    Chunk,
    Document,
    DocumentVersion,
    GenerationJob,
    JobStep,
    ParseResult,
    Project,
    SlidePlan,
    Template,
    User,
)
from nps.parsers import safe_parse
from nps.plans import require_approved, save_slides, validate_plan
from nps.storage import storage
from nps.upload import security_scan


def result_for(db, job, name):
    step = db.scalar(select(JobStep).where(JobStep.job_id == job.id, JobStep.step_type == name))
    return step.output if step and step.state == "SUCCEEDED" else {}


def llm_payload(db, job):
    version_id = job.payload["version_id"]
    parse = db.scalar(select(ParseResult).where(ParseResult.document_version_id == version_id))
    if not parse:
        raise DomainError("PARSE_REQUIRED", 409)
    return {
        "normalized": parse.data,
        "document_title": db.get(Document, job.payload["document_id"]).title,
        "chunks": [c.data for c in db.scalars(select(Chunk).where(Chunk.version_id == version_id))],
    }


def do_step(db, job, step, cancelled):
    user = db.get(User, job.requested_by)
    if step == "SECURITY_SCAN":
        result = security_scan(job.payload)
        if job.kind == "design_reference":
            return result
        if job.kind == "template":
            from pptx import Presentation

            try:
                Presentation(storage.path(result["storage_key"]))
            except Exception:
                raise DomainError("TEMPLATE_INVALID", 422) from None
            template = Template(
                name=job.payload["name"],
                version="1.0",
                official_flag=False,
                config=job.payload["config"],
                storage_key=result["storage_key"],
            )
            db.add(template)
            db.flush()
            audit(db, user, "TEMPLATE_CHANGE", template.id, job.project_id)
            return {"template_id": template.id, "scan_mode": result["scan_mode"]}
        doc = db.get(Document, job.payload["document_id"])
        db.refresh(doc, with_for_update=True)
        number = (
            db.scalar(select(func.max(DocumentVersion.version)).where(DocumentVersion.document_id == doc.id))
            or 0
        ) + 1
        duplicates = db.scalar(
            select(DocumentVersion)
            .join(Document, Document.id == DocumentVersion.document_id)
            .where(Document.project_id == job.project_id, DocumentVersion.sha256 == result["sha256"])
        )
        version = DocumentVersion(
            document_id=doc.id,
            version=number,
            size=job.payload["size"],
            mime=job.payload["mime"],
            extension=job.payload["extension"],
            **result,
        )
        db.add(version)
        db.flush()
        doc.current_version_id = version.id
        audit(
            db,
            user,
            "DOCUMENT_UPLOAD",
            doc.id,
            job.project_id,
            detail={"version": number, "mode": result["scan_mode"]},
        )
        return {
            "document_id": doc.id,
            "version_id": version.id,
            "duplicate": duplicates is not None,
            "scan_mode": result["scan_mode"],
        }
    if step == "PARSE":
        version = db.get(DocumentVersion, job.payload["version_id"])
        if not version or version.scan_status != "CLEAN":
            raise DomainError("DOC_NOT_CLEAN", 409)
        existing = db.scalar(select(ParseResult).where(ParseResult.document_version_id == version.id))
        if existing:
            return {"parse_result_id": existing.id, "reused": True}
        parsed = safe_parse(storage.path(version.storage_key), version.extension)
        data = parsed.model_dump(mode="json")
        parse = ParseResult(
            document_version_id=version.id, data=data, storage_key=storage.write_json("parsed", data)
        )
        db.add(parse)
        db.flush()
        return {"parse_result_id": parse.id, "warnings": parsed.warnings}
    if step == "CHUNK":
        version = db.get(DocumentVersion, job.payload["version_id"])
        parse = db.scalar(select(ParseResult).where(ParseResult.document_version_id == version.id))
        if not parse:
            raise DomainError("PARSE_REQUIRED", 409)
        existing = db.scalars(select(Chunk).where(Chunk.version_id == version.id)).all()
        if existing:
            return {"chunk_count": len(existing), "reused": True}
        project = db.get(Project, job.project_id)
        chunks = chunk_document(
            NormalizedDocument.model_validate(parse.data),
            version.document_id,
            version.id,
            project.security_class,
        )
        for chunk in chunks:
            db.add(
                Chunk(
                    id=str(chunk.chunk_id),
                    version_id=version.id,
                    parse_result_id=parse.id,
                    data=chunk.model_dump(mode="json"),
                )
            )
        storage.write_json("chunks", [c.model_dump(mode="json") for c in chunks])
        return {"chunk_count": len(chunks)}
    tasks = {
        "LLM_SUMMARY": "document_summary",
        "LLM_KEY_MESSAGES": "key_messages",
        "LLM_OUTLINE": "slide_outline",
        "LLM": "slide_plan",
        "LLM_VISUAL": "visual_plan",
    }
    if step in tasks:
        payload = llm_payload(db, job)
        payload["previous_stages"] = {s: result_for(db, job, s) for s in tasks if s != step}
        output = LLMClient().generate(tasks[step], payload)
        if step == "LLM":
            output = SlidePlanContract.model_validate(output).model_dump(mode="json")
        else:
            from nps.llm import StageOutput

            output = StageOutput.model_validate(output).model_dump(mode="json")
        return {"data": output}
    if step == "DESIGN_LEARN":
        from nps.theme_extract import safe_extract

        scan = result_for(db, job, "SECURITY_SCAN")
        existing = next(
            (
                t
                for t in db.scalars(select(Template).where(Template.org_id == user.org_id))
                if t.config.get("reference_sha256") == scan["sha256"]
            ),
            None,
        )
        if existing:
            return {"template_id": existing.id, "reused": True, "learning": "style-memory"}
        policy = safe_extract(storage.path(scan["storage_key"]))
        policy.update(reference_sha256=scan["sha256"], scan_mode=scan["scan_mode"], tags=[])
        template = Template(
            name=job.payload["name"],
            version="2.0",
            org_id=user.org_id,
            config=policy,
            storage_key=scan["storage_key"],
            official_flag=False,
        )
        db.add(template)
        db.flush()
        audit(
            db, user, "DESIGN_REFERENCE_LEARNED", template.id, job.project_id, detail={"mode": "style-memory"}
        )
        return {"template_id": template.id, "learning": "style-memory", "slides": policy["reference_slides"]}
    if step == "PLAN_VALIDATE":
        data = result_for(db, job, "LLM")["data"]
        from nps.themes import attach_theme

        attach_theme(db, db.get(Project, job.project_id), data)
        plan = SlidePlan(
            id=data["plan_id"], project_id=job.project_id, document_id=job.payload["document_id"], data=data
        )
        validate_plan(db, plan)
        db.add(plan)
        db.flush()
        save_slides(db, plan)
        return {"plan_id": plan.id}
    plan = db.get(SlidePlan, job.payload["plan_id"], populate_existing=True)
    require_approved(plan)
    if job.payload["plan_version"] != plan.version:
        raise DomainError("PLAN_VERSION_CHANGED", 409)
    validate_plan(db, plan)
    if step == "IMAGE":
        from nps.comfy import generate_visuals

        return generate_visuals(db, job, plan, cancelled)
    if step in {"PPT", "PPT_QA"}:
        from nps.ppt import render_step, qa_step

        return render_step(db, job, plan, cancelled) if step == "PPT" else qa_step(db, job, plan)
    if step in {"VIDEO", "FINAL_QA"}:
        from nps.video import render_step, qa_step

        return render_step(db, job, plan, cancelled) if step == "VIDEO" else qa_step(db, job, plan)
    raise DomainError("STEP_UNSUPPORTED", 422)


def execute_step(db, job_id, handler=None):
    job = db.get(GenerationJob, job_id)
    if job.state in {"QUEUED", "RETRYING"}:
        transition(job, "RUNNING")
    if job.state != "RUNNING":
        return
    step_name = job.step
    record = db.scalar(select(JobStep).where(JobStep.job_id == job.id, JobStep.step_type == step_name))
    record.state, record.attempts = "RUNNING", record.attempts + 1
    db.commit()

    def cancelled():
        # Independent query observes cancellation committed by API during rendering.
        value = db.scalar(select(GenerationJob.cancel_requested).where(GenerationJob.id == job_id))
        if value:
            raise DomainError("JOB_CANCELLED", 409)

    try:
        cancelled()
        output = (handler or do_step)(db, job, step_name, cancelled)
        cancelled()
        # Recheck approval/version after slow work before committing generated output.
        if "plan_id" in job.payload:
            plan = db.get(SlidePlan, job.payload["plan_id"], populate_existing=True)
            require_approved(plan)
            if plan.version != job.payload["plan_version"]:
                raise DomainError("PLAN_VERSION_CHANGED", 409)
        record.output, record.state, record.error_code = output, "SUCCEEDED", None
        pipeline = PIPELINES[job.kind]
        completed = pipeline.index(step_name) + 1
        job.progress = int(completed / len(pipeline) * 100)
        if completed == len(pipeline):
            needs_review = (
                job.kind in {"analyze", "plan"} and not settings().prototype_review_pass
            ) or output.get("qa_status") == "FAIL"
            transition(job, "WAITING_REVIEW" if needs_review else "SUCCEEDED")
            job.result = output
        else:
            job.step = pipeline[completed]
            transition(job, "QUEUED")
        job.worker_id, job.lease_until = None, None
        db.commit()
        if step_name == "SECURITY_SCAN":
            storage.path(job.payload["quarantine_key"]).unlink(missing_ok=True)
        if job.state == "QUEUED":
            enqueue(job)
    except Exception as exc:
        db.rollback()
        job = db.get(GenerationJob, job_id, populate_existing=True)
        record = db.scalar(select(JobStep).where(JobStep.job_id == job_id, JobStep.step_type == step_name))
        code = exc.code if isinstance(exc, DomainError) else "STEP_FAILED"
        record.state, record.error_code = "FAILED", code
        job.error_code = code
        transition(job, "CANCELLED" if code == "JOB_CANCELLED" else "FAILED")
        job.worker_id, job.lease_until = None, None
        db.commit()


def run_until_terminal(db, job_id, handler=None):
    """Test harness: identical real step handlers; production workers dispatch one step."""
    from nps.jobs import TERMINAL

    for _ in range(30):
        job = db.get(GenerationJob, job_id, populate_existing=True)
        if job.state in TERMINAL:
            return job
        execute_step(db, job_id, handler)
    raise RuntimeError("pipeline did not terminate")
