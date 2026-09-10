"""Durable DB outbox with Redis queue hints, leases, routing and bounded retries."""

import hashlib
import json
from datetime import timedelta
import redis
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from nps.auth import audit
from nps.config import settings
from nps.db import utcnow, uid
from nps.errors import DomainError
from nps.models import GenerationJob, JobStep

PIPELINES = {
    "upload": ["SECURITY_SCAN"],
    "analyze": [
        "PARSE",
        "CHUNK",
        "LLM_SUMMARY",
        "LLM_KEY_MESSAGES",
        "LLM_OUTLINE",
        "LLM",
        "LLM_VISUAL",
        "PLAN_VALIDATE",
    ],
    "plan": ["LLM_SUMMARY", "LLM_KEY_MESSAGES", "LLM_OUTLINE", "LLM", "LLM_VISUAL", "PLAN_VALIDATE"],
    "ppt": ["IMAGE", "PPT", "PPT_QA"],
    "image": ["IMAGE"],
    "video": ["VIDEO", "FINAL_QA"],
    "template": ["SECURITY_SCAN"],
}
ROUTING = {
    "SECURITY_SCAN": "document",
    "PARSE": "document",
    "CHUNK": "document",
    "LLM_SUMMARY": "llm",
    "LLM_KEY_MESSAGES": "llm",
    "LLM_OUTLINE": "llm",
    "LLM": "llm",
    "LLM_VISUAL": "llm",
    "PLAN_VALIDATE": "llm",
    "IMAGE": "image",
    "PPT": "ppt",
    "PPT_QA": "ppt",
    "VIDEO": "video",
    "FINAL_QA": "video",
}
TERMINAL = {"SUCCEEDED", "FAILED", "CANCELLED", "WAITING_REVIEW"}
TRANSITIONS = {
    "QUEUED": {"RUNNING", "CANCELLED"},
    "RETRYING": {"RUNNING", "CANCELLED"},
    "RUNNING": {"QUEUED", "SUCCEEDED", "FAILED", "CANCELLED", "WAITING_REVIEW", "RETRYING"},
    "FAILED": {"RETRYING"},
    "CANCELLED": {"RETRYING"},
    "WAITING_REVIEW": set(),
    "SUCCEEDED": set(),
}


def broker():
    return redis.Redis.from_url(
        settings().redis_url, decode_responses=True, socket_timeout=2, socket_connect_timeout=2
    )


def transition(job, state):
    if state != job.state and state not in TRANSITIONS.get(job.state, set()):
        raise DomainError("JOB_INVALID_TRANSITION", 409)
    job.state, job.seq = state, job.seq + 1


def enqueue(job):
    # DB row is the durable outbox. A failed Redis write cannot lose the job.
    try:
        broker().zadd("q_" + ROUTING[job.step], {job.id: -job.priority * 1e12 + job.created_at.timestamp()})
    except redis.RedisError:
        pass


def create_job(db, user, project_id, kind, payload, key=None):
    if kind in {"ppt", "video", "image"}:
        payload = {**payload, "review_mode": settings().review_mode}
    key = key or uid()
    if len(key) > 100:
        raise DomainError("IDEMPOTENCY_INVALID", 422)
    fingerprint = hashlib.sha256(
        json.dumps({"kind": kind, "payload": payload}, sort_keys=True).encode()
    ).hexdigest()
    existing = db.scalar(
        select(GenerationJob).where(
            GenerationJob.project_id == project_id,
            GenerationJob.requested_by == user.id,
            GenerationJob.idempotency_key == key,
        )
    )
    if existing:
        if existing.fingerprint != fingerprint:
            raise DomainError("IDEMPOTENCY_CONFLICT", 409)
        return existing
    job = GenerationJob(
        project_id=project_id,
        requested_by=user.id,
        kind=kind,
        state="QUEUED",
        step=PIPELINES[kind][0],
        payload=payload,
        idempotency_key=key,
        fingerprint=fingerprint,
    )
    db.add(job)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return create_job(db, user, project_id, kind, payload, key)
    for step in PIPELINES[kind]:
        db.add(JobStep(job_id=job.id, step_type=step))
    audit(db, user, "JOB_CREATE", job.id, project_id)
    if payload.get("review_mode") == "prototype-pass":
        audit(
            db,
            user,
            "PROTOTYPE_REVIEW_BYPASS",
            job.id,
            project_id,
            detail={"plan_id": payload["plan_id"], "plan_version": payload["plan_version"]},
        )
    db.commit()
    enqueue(job)
    return job


def snapshot(db, job):
    steps = list(db.scalars(select(JobStep).where(JobStep.job_id == job.id)))
    ordered = {s.step_type: s for s in steps}
    return {
        "job_id": job.id,
        "id": job.id,
        "project_id": job.project_id,
        "kind": job.kind,
        "document_id": job.payload.get("document_id"),
        "state": job.state,
        "step": job.step,
        "progress": job.progress,
        "seq": job.seq,
        "ts": job.updated_at.isoformat(),
        "error_code": job.error_code,
        "result": job.result,
        "retry_count": job.retry_count,
        "mock": {
            "llm": settings().llm_mode == "mock",
            "comfy": settings().comfy_mode == "mock",
            "scan": settings().scan_mode == "mock",
        },
        "steps": [
            {
                "step": name,
                "state": ordered[name].state,
                "attempts": ordered[name].attempts,
                "error_code": ordered[name].error_code,
            }
            for name in PIPELINES[job.kind]
        ],
    }


def cancel_job(db, user, job):
    if job.state in TERMINAL:
        raise DomainError("JOB_NOT_CANCELLABLE", 409)
    job.cancel_requested = True
    if job.state in {"QUEUED", "RETRYING"}:
        transition(job, "CANCELLED")
    else:
        job.seq += 1
    audit(db, user, "JOB_CANCEL", job.id, job.project_id)
    db.commit()
    return job


def retry_job(db, user, job, resume=None):
    if job.state not in {"FAILED", "CANCELLED"}:
        raise DomainError("JOB_NOT_RETRYABLE", 409)
    if job.retry_count >= 3:
        raise DomainError("JOB_RETRY_EXHAUSTED", 409)
    pipeline = PIPELINES[job.kind]
    resume = resume or job.step
    if resume not in pipeline:
        raise DomainError("JOB_RESUME_INVALID", 422)
    steps = {s.step_type: s for s in db.scalars(select(JobStep).where(JobStep.job_id == job.id))}
    # Cannot skip an unsuccessful prerequisite, nor erase an approved checkpoint.
    if any(steps[s].state != "SUCCEEDED" for s in pipeline[: pipeline.index(resume)]):
        raise DomainError("JOB_RESUME_PREREQUISITE", 409)
    if steps[resume].state == "SUCCEEDED":
        raise DomainError("JOB_RESUME_COMPLETED_STEP", 409)
    job.step, job.resume_from_step = resume, resume
    job.retry_count += 1
    job.cancel_requested, job.error_code, job.worker_id, job.lease_until = False, None, None, None
    transition(job, "RETRYING")
    audit(db, user, "JOB_RETRY", job.id, job.project_id, detail={"step": resume})
    db.commit()
    enqueue(job)
    return job


def claim(db, queue, worker_id, capability="cpu", free_vram=0):
    # A worker can only claim while its heartbeat/capability is present in Redis.
    r = broker()
    raw = r.get("worker:" + worker_id)
    if raw is None:
        return None
    heartbeat = json.loads(raw)
    if heartbeat["queue"] != queue or heartbeat["capability"] != capability:
        return None
    steps = [name for name, value in ROUTING.items() if value == queue]
    jobs = db.scalars(
        select(GenerationJob)
        .where(
            GenerationJob.state.in_(["QUEUED", "RETRYING"]),
            GenerationJob.step.in_(steps),
            GenerationJob.required_capability == capability,
            GenerationJob.estimated_vram_mb <= min(free_vram, heartbeat["free_vram_mb"]),
        )
        .order_by(GenerationJob.priority.desc(), GenerationJob.created_at)
        .limit(20)
    ).all()
    for job in jobs:
        if job.cancel_requested:
            transition(job, "CANCELLED")
            db.commit()
            continue
        result = db.execute(
            update(GenerationJob)
            .where(GenerationJob.id == job.id, GenerationJob.state.in_(["QUEUED", "RETRYING"]))
            .values(
                state="RUNNING",
                worker_id=worker_id,
                seq=GenerationJob.seq + 1,
                lease_until=utcnow() + timedelta(seconds=settings().worker_lease_seconds),
            )
        )
        db.commit()
        if result.rowcount:
            db.refresh(job)
            r.zrem("q_" + queue, job.id)
            return job
    return None


def heartbeat(worker_id, queue, capability, free_vram):
    broker().set(
        "worker:" + worker_id,
        json.dumps(
            {
                "worker_id": worker_id,
                "queue": queue,
                "capability": capability,
                "free_vram_mb": free_vram,
                "ts": utcnow().isoformat(),
            }
        ),
        ex=20,
    )


def recover_expired(db):
    for job in db.scalars(
        select(GenerationJob).where(GenerationJob.state == "RUNNING", GenerationJob.lease_until < utcnow())
    ):
        job.error_code = "WORKER_LOST"
        transition(job, "FAILED")
        step = db.scalar(select(JobStep).where(JobStep.job_id == job.id, JobStep.step_type == job.step))
        step.state, step.error_code = "FAILED", "WORKER_LOST"
        job.worker_id, job.lease_until = None, None
    db.commit()
