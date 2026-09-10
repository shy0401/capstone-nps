from datetime import timedelta
from unittest.mock import patch
import fakeredis
from sqlalchemy import select
from nps.db import utcnow
from nps.jobs import create_job, heartbeat, claim, recover_expired, retry_job
from nps.models import Project, JobStep
from nps.pipeline import execute_step


def test_expired_worker_lease_and_other_queue_survives(db, users):
    r = fakeredis.FakeRedis(decode_responses=True)
    user = users["demo-user"]
    project = db.scalar(select(Project).where(Project.owner_id == user.id))
    with patch("nps.jobs.broker", return_value=r):
        lost = create_job(db, user, project.id, "analyze", {})
        heartbeat("dead", "document", "cpu", 0)
        claim(db, "document", "dead")
        lost.lease_until = utcnow() - timedelta(seconds=1)
        db.commit()
        r.delete("worker:dead")
        recover_expired(db)
        db.refresh(lost)
        assert lost.state == "FAILED" and lost.error_code == "WORKER_LOST"
        retry_job(db, user, lost, "PARSE")
        healthy = create_job(db, user, project.id, "video", {})
        heartbeat("healthy", "image", "cpu", 0)
        assert claim(db, "image", "healthy").id == healthy.id


def test_running_cancel_is_observed_between_steps(db, users):
    user = users["demo-user"]
    project = db.scalar(select(Project).where(Project.owner_id == user.id))
    with patch("nps.jobs.broker", return_value=fakeredis.FakeRedis(decode_responses=True)):
        job = create_job(db, user, project.id, "analyze", {})

        def handler(db, job, step, cancelled):
            job.cancel_requested = True
            db.commit()
            cancelled()

        execute_step(db, job.id, handler)
        assert job.state == "CANCELLED"
        assert (
            db.scalar(select(JobStep).where(JobStep.job_id == job.id, JobStep.step_type == "CHUNK")).attempts
            == 0
        )
