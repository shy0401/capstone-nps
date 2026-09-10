import importlib.util
import json
import shutil
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
import fakeredis
import pytest
from sqlalchemy import select
from nps.auth import issue_access
from nps.comfy import MockComfyAdapter
from nps.llm import MockLLMAdapter
from nps.models import ArtifactVersion, AuditEvent, DocumentVersion, SlidePlan
from nps.pipeline import run_until_terminal
from nps.storage import storage, sha256_file


@pytest.fixture
def fixture_dir(tmp_path):
    spec = importlib.util.spec_from_file_location("golden_fixtures", "infra/scripts/generate_fixtures.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.generate(tmp_path / "fixtures")
    return tmp_path / "fixtures"


@pytest.fixture
def adapters():
    r = fakeredis.FakeRedis(decode_responses=True)
    with (
        patch("nps.jobs.broker", return_value=r),
        patch("nps.pipeline.LLMClient.generate", side_effect=MockLLMAdapter().generate),
        patch("nps.comfy.ComfyClient.generate", side_effect=MockComfyAdapter().generate),
    ):
        yield


def auth(user):
    return {"Authorization": "Bearer " + issue_access(user)}


def check(result, status=200):
    assert result.status_code == status, result.text
    return result.json()


def upload_analyze(client, db, users, fixture_dir, ext):
    headers = auth(users["demo-user"])
    project = check(client.get("/api/v1/projects", headers=headers))[0]
    path = fixture_dir / ("synthetic" + ext)
    result = check(
        client.post(
            f"/api/v1/projects/{project['id']}/documents",
            headers=headers,
            files={"file": ("합성문서" + ext, path.read_bytes(), "application/octet-stream")},
        ),
        202,
    )
    document_id = result["document_id"]
    assert client.post(f"/api/v1/documents/{document_id}/analyze", headers=headers).status_code == 409
    upload_job = run_until_terminal(db, result["job"]["id"])
    assert upload_job.state == "SUCCEEDED", upload_job.error_code
    version = db.get(DocumentVersion, upload_job.result["version_id"])
    assert version.scan_mode == "mock" and sha256_file(storage.path(version.storage_key)) == version.sha256
    analysis = check(client.post(f"/api/v1/documents/{document_id}/analyze", headers=headers), 202)
    job = run_until_terminal(db, analysis["id"])
    assert job.state == "WAITING_REVIEW", (job.step, job.error_code)
    return project, document_id, job.result["plan_id"]


@pytest.mark.parametrize("ext", [".pdf", ".docx", ".xlsx", ".hwpx", ".hwp"])
def test_golden_upload_parse_plan(client, db, users, fixture_dir, adapters, ext):
    _, doc, plan_id = upload_analyze(client, db, users, fixture_dir, ext)
    h = auth(users["demo-user"])
    plan = check(client.get(f"/api/v1/slide-plans/{plan_id}", headers=h))
    assert plan["data"]["mock"]
    for kind in ["ppt", "video", "images"]:
        assert client.post(f"/api/v1/slide-plans/{plan_id}/generate-{kind}", headers=h).status_code == 409
    check(client.get(f"/api/v1/documents/{doc}/parse-result", headers=h))
    assert check(client.get(f"/api/v1/documents/{doc}/chunks", headers=h))


def test_prototype_pass_preserves_scope_validation_and_real_approval(
    client, db, users, fixture_dir, adapters, monkeypatch
):
    from nps.config import settings
    from nps.models import Approval, GenerationJob

    project, doc, plan_id = upload_analyze(client, db, users, fixture_dir, ".hwp")
    monkeypatch.setattr(settings(), "review_mode", "prototype-pass")
    h, other = auth(users["demo-user"]), auth(users["other-user"])
    assert check(client.get("/api/v1/me", headers=h))["review_mode"] == "prototype-pass"
    jobs = []
    for kind in ["ppt", "video", "images"]:
        url = f"/api/v1/slide-plans/{plan_id}/generate-{kind}"
        assert client.post(url, headers=other).status_code == 403
        job = check(client.post(url, headers=h), 202)
        jobs.append(job["id"])
        assert db.get(GenerationJob, job["id"]).payload["review_mode"] == "prototype-pass"
    plan = db.get(SlidePlan, plan_id)
    assert plan.status == "VALIDATED" and plan.approved_version is None
    assert not db.scalars(select(Approval)).all()
    assert (
        len(db.scalars(select(AuditEvent).where(AuditEvent.action == "PROTOTYPE_REVIEW_BYPASS")).all()) == 3
    )
    # Evidence validation still applies even when human review is bypassed.
    original = plan.data
    invalid = json.loads(json.dumps(original))
    invalid["slides"][0]["source_refs"][0]["chunk_id"] = str(uuid4())
    plan.data = invalid
    db.commit()
    assert client.post(f"/api/v1/slide-plans/{plan_id}/generate-ppt", headers=h).status_code == 422
    plan.data = original
    db.commit()
    # Switching back to strict also blocks already queued unapproved generation.
    monkeypatch.setattr(settings(), "review_mode", "strict")
    job = run_until_terminal(db, jobs[0])
    assert job.state == "FAILED" and job.error_code == "PLAN_REVIEW_REQUIRED"


def test_prototype_analysis_completes_without_review(client, db, users, fixture_dir, adapters, monkeypatch):
    from nps.config import settings

    _, doc, _ = upload_analyze(client, db, users, fixture_dir, ".docx")
    monkeypatch.setattr(settings(), "review_mode", "prototype-pass")
    job = check(client.post(f"/api/v1/documents/{doc}/analyze", headers=auth(users["demo-user"])), 202)
    result = run_until_terminal(db, job["id"])
    assert result.state == "SUCCEEDED" and result.result["plan_id"]


def test_golden_review_ppt_video_version_audit(client, db, users, fixture_dir, adapters):
    project, doc, plan_id = upload_analyze(client, db, users, fixture_dir, ".docx")
    h, rh, other = auth(users["demo-user"]), auth(users["demo-reviewer"]), auth(users["other-user"])
    assert (
        client.post(
            f"/api/v1/slide-plans/{plan_id}/approve", headers=h, json={"decision": "approve", "version": 1}
        ).status_code
        == 403
    )
    check(
        client.post(
            f"/api/v1/slide-plans/{plan_id}/approve", headers=rh, json={"decision": "approve", "version": 1}
        )
    )
    job_data = check(
        client.post(
            f"/api/v1/slide-plans/{plan_id}/generate-ppt", headers={**h, "Idempotency-Key": str(uuid4())}
        ),
        202,
    )
    job = run_until_terminal(db, job_data["id"])
    assert job.state == "SUCCEEDED", (job.step, job.error_code)
    assert job.result["qa_status"] == "PASS"
    ppt_id = job.result["artifact_id"]
    assert client.post(f"/api/v1/slide-plans/{plan_id}/generate-video", headers=h).status_code == 409
    approved = check(
        client.post(
            f"/api/v1/artifacts/{ppt_id}/approve", headers=rh, json={"decision": "approve", "version": 1}
        )
    )
    assert approved["official_eligible"] is False
    video_job = check(client.post(f"/api/v1/slide-plans/{plan_id}/generate-video", headers=h), 202)
    video_job = run_until_terminal(db, video_job["id"])
    assert video_job.state == "SUCCEEDED", (video_job.step, video_job.error_code)
    assert video_job.result["qa_status"] == "PASS"
    video_id = video_job.result["artifact_id"]
    # Exercise every object class against an unrelated organization.
    for path in [
        f"/documents/{doc}",
        f"/documents/{doc}/versions",
        f"/documents/{doc}/parse-result",
        f"/documents/{doc}/chunks",
        f"/slide-plans/{plan_id}",
        f"/jobs/{job.id}",
        f"/artifacts/{ppt_id}",
        f"/artifacts/{ppt_id}/download",
    ]:
        assert client.get("/api/v1" + path, headers=other).status_code == 403, path
    assert (
        client.get(
            f"/api/v1/artifacts/{ppt_id}/download?version_id={video_job.result['version_id']}", headers=h
        ).status_code
        == 403
    )
    for artifact_id in [ppt_id, video_id]:
        assert client.get(f"/api/v1/artifacts/{artifact_id}/download", headers=h).status_code == 200
    # Save verified synthetic samples for the handoff.
    samples = Path("test-results/samples")
    samples.mkdir(parents=True, exist_ok=True)
    for kind, completed in [("pptx", job), ("mp4", video_job)]:
        version = db.get(ArtifactVersion, completed.result["version_id"])
        shutil.copyfile(storage.path(version.storage_key), samples / ("golden-synthetic." + kind))
        (samples / (kind + "-qa_report.json")).write_text(
            json.dumps(version.qa_report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    # Edit one slide, reapprove plan, regenerate same artifact: no parse/LLM, old approval not inherited.
    plan = db.get(SlidePlan, plan_id, populate_existing=True)
    data = json.loads(json.dumps(plan.data))
    data["slides"][0]["title"] = "검토 후 합성 제목"
    original_versions = [s["version"] for s in data["slides"]]
    updated = check(client.patch(f"/api/v1/slide-plans/{plan_id}", headers=h, json=data))
    assert updated["status"] == "DRAFT" and updated["approved_version"] is None
    assert updated["data"]["slides"][0]["version"] == original_versions[0] + 1
    assert [s["version"] for s in updated["data"]["slides"]][1:] == original_versions[1:]
    check(
        client.post(
            f"/api/v1/slide-plans/{plan_id}/approve", headers=rh, json={"decision": "approve", "version": 2}
        )
    )
    regen = check(
        client.post(
            f"/api/v1/artifacts/{ppt_id}/regenerate",
            headers=h,
            json={"slide_id": data["slides"][0]["slide_id"]},
        ),
        202,
    )
    regen_job = run_until_terminal(db, regen["id"])
    assert regen_job.state == "SUCCEEDED", regen_job.error_code
    artifact = check(client.get(f"/api/v1/artifacts/{ppt_id}", headers=h))
    assert artifact["versions"][0]["version"] == 2
    assert artifact["versions"][0]["approval_status"] == "DRAFT"
    assert artifact["versions"][1]["approval_status"] == "APPROVED"
    actions = {event.action for event in db.scalars(select(AuditEvent))}
    assert {
        "DOCUMENT_UPLOAD",
        "PLAN_APPROVE",
        "ARTIFACT_GENERATE",
        "ARTIFACT_DOWNLOAD",
        "APPROVE",
        "PLAN_UPDATE",
    } <= actions
    report = {
        "status": "PASS",
        "transport": "FastAPI TestClient + SQLAlchemy SQLite + deterministic Redis adapter",
        "gpu": False,
        "real_parsers": True,
        "ppt_qa": "PASS",
        "mp4_ffprobe": "PASS",
        "container_e2e": "separate docker-golden.json / prototype-generation.json evidence",
    }
    (samples.parent / "golden-result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
