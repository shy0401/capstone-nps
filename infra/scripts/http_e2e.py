"""Actual HTTP + Redis/PostgreSQL workers, used only after Docker readiness."""

import json
import os
import time
from pathlib import Path
import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]


def run():
    env = {**dotenv_values(ROOT / ".env"), **os.environ}
    base = env.get("E2E_BASE_URL", "http://127.0.0.1:8080") + "/api/v1"
    with httpx.Client(base_url=base, timeout=30, trust_env=False) as client:

        def login(username):
            r = client.post("/auth/login", json={"username": username, "password": env["SEED_PASSWORD"]})
            r.raise_for_status()
            client.headers["Authorization"] = "Bearer " + r.json()["access_token"]

        def wait(job):
            for _ in range(240):
                r = client.get("/jobs/" + job)
                r.raise_for_status()
                data = r.json()
                if data["state"] in {"SUCCEEDED", "WAITING_REVIEW"}:
                    return data
                if data["state"] in {"FAILED", "CANCELLED"}:
                    raise RuntimeError(data["error_code"])
                time.sleep(0.5)
            raise TimeoutError("Golden job deadline exceeded")

        login("demo-user")
        project = client.get("/projects").json()[0]
        fixture = ROOT / "tests/golden/fixtures/synthetic.docx"
        if not fixture.is_file():
            raise FileNotFoundError(f"Bundled synthetic Golden fixture is missing: {fixture}")
        with fixture.open("rb") as file:
            r = client.post(
                f"/projects/{project['id']}/documents",
                files={"file": ("synthetic.docx", file, "application/octet-stream")},
            )
        r.raise_for_status()
        uploaded = r.json()
        wait(uploaded["job"]["id"])
        result = client.post(f"/documents/{uploaded['document_id']}/analyze")
        result.raise_for_status()
        plan_id = wait(result.json()["id"])["result"]["plan_id"]
        assert client.post(f"/slide-plans/{plan_id}/generate-ppt").status_code == 409
        login("demo-reviewer")
        client.post(
            f"/slide-plans/{plan_id}/approve", json={"version": 1, "decision": "approve"}
        ).raise_for_status()
        ppt = wait(client.post(f"/slide-plans/{plan_id}/generate-ppt").json()["id"])
        assert ppt["result"]["qa_status"] == "PASS"
        client.post(
            f"/artifacts/{ppt['result']['artifact_id']}/approve", json={"version": 1, "decision": "approve"}
        ).raise_for_status()
        video = wait(client.post(f"/slide-plans/{plan_id}/generate-video").json()["id"])
        assert video["result"]["qa_status"] == "PASS"
        result = {
            "status": "PASS",
            "transport": "actual HTTP",
            "ppt": ppt["result"],
            "video": video["result"],
        }
        output = ROOT / "test-results/docker-golden.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("Docker HTTP Golden E2E PASS")


if __name__ == "__main__":
    run()
