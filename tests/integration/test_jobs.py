from unittest.mock import patch
import fakeredis
import pytest
from sqlalchemy import select
from nps.auth import issue_access
from nps.errors import DomainError
from nps.jobs import cancel_job, claim, create_job, heartbeat, retry_job
from nps.models import Project, JobStep
from nps.pipeline import run_until_terminal


@pytest.fixture
def queue():
    r = fakeredis.FakeRedis(decode_responses=True)
    with patch("nps.jobs.broker", return_value=r):
        yield r


def test_cancel_retry_resume_and_idempotency(db, users, queue):
    user = users["demo-user"]
    project = db.scalar(select(Project).where(Project.owner_id == user.id))
    job = create_job(db, user, project.id, "analyze", {}, "one")
    assert create_job(db, user, project.id, "analyze", {}, "one").id == job.id
    cancel_job(db, user, job)
    assert job.state == "CANCELLED"
    retry_job(db, user, job, "PARSE")
    calls = []

    def handler(db, job, step, cancelled):
        calls.append(step)
        if step == "CHUNK":
            raise DomainError("INJECTED_FAILURE")
        return {}

    run_until_terminal(db, job.id, handler)
    assert job.state == "FAILED"
    assert calls == ["PARSE", "CHUNK"]
    retry_job(db, user, job, "CHUNK")
    run_until_terminal(db, job.id, lambda *args: {})
    assert job.state == "WAITING_REVIEW"
    assert (
        db.scalar(select(JobStep).where(JobStep.job_id == job.id, JobStep.step_type == "PARSE")).attempts == 1
    )


def test_worker_heartbeat_and_queue_routing(db, users, queue):
    user = users["demo-user"]
    project = db.scalar(select(Project).where(Project.owner_id == user.id))
    job = create_job(db, user, project.id, "analyze", {})
    assert claim(db, "document", "worker-1") is None
    heartbeat("worker-1", "document", "cpu", 0)
    assert claim(db, "video", "worker-1") is None
    assert claim(db, "document", "worker-1").id == job.id


def test_qa_failed_artifact_requires_review(db, users, queue):
    user = users["demo-user"]
    project = db.scalar(select(Project).where(Project.owner_id == user.id))
    job = create_job(db, user, project.id, "ppt", {})
    run_until_terminal(db, job.id, lambda db, job, step, cancelled: {"qa_status": "FAIL"})
    assert job.state == "WAITING_REVIEW"
    assert job.result["qa_status"] == "FAIL"


def test_ws_equals_rest_and_idor(client, db, users, queue):
    user = users["demo-user"]
    project = db.scalar(select(Project).where(Project.owner_id == user.id))
    job = create_job(db, user, project.id, "upload", {})
    token = issue_access(user)
    with client.websocket_connect(f"/ws/v1/jobs/{job.id}") as ws:
        ws.send_json({"access_token": token})
        event = ws.receive_json()
        rest = client.get(f"/api/v1/jobs/{job.id}", headers={"Authorization": "Bearer " + token}).json()
        assert event == rest
    other = issue_access(users["other-user"])
    assert (
        client.get(f"/api/v1/jobs/{job.id}", headers={"Authorization": "Bearer " + other}).status_code == 403
    )
