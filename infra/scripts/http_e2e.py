"""Real HTTP Golden on a running Compose stack; generated synthetic data only."""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]


def run():
    env = {**dotenv_values(ROOT / ".env"), **os.environ}
    base = env.get("E2E_BASE_URL", "http://127.0.0.1:8080") + "/api/v1"
    output_dir = ROOT / "test-results"
    output_dir.mkdir(parents=True, exist_ok=True)
    with httpx.Client(base_url=base, timeout=30, trust_env=False) as client:

        def request(method, path, **kwargs):
            response = client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()

        def login(username):
            token = request(
                "POST", "/auth/login", json={"username": username, "password": env["SEED_PASSWORD"]}
            )
            client.headers["Authorization"] = "Bearer " + token["access_token"]
            return request("GET", "/me")

        def wait(job, expected="SUCCEEDED"):
            deadline = time.monotonic() + 180
            while time.monotonic() < deadline:
                data = request("GET", "/jobs/" + job)
                if data["state"] == expected:
                    return data
                if data["state"] in {"FAILED", "CANCELLED"}:
                    raise RuntimeError(f"{data['step']}: {data['error_code']}")
                time.sleep(0.5)
            raise TimeoutError("Golden job deadline exceeded")

        reviewer = login("demo-reviewer")
        login("demo-user")
        project = request(
            "POST",
            "/projects",
            json={
                "name": "Synthetic Docker Golden " + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S"),
                "description": "Automated synthetic-only acceptance run",
                "security_class": "synthetic",
            },
        )
        request(
            "POST", f"/projects/{project['id']}/members", json={"user_id": reviewer["id"], "role": "Reviewer"}
        )
        results = []
        for extension in ["pdf", "docx", "xlsx", "hwpx", "hwp"]:
            login("demo-user")
            fixture = ROOT / "tests/golden/fixtures" / ("synthetic." + extension)
            with fixture.open("rb") as file:
                uploaded = request(
                    "POST",
                    f"/projects/{project['id']}/documents",
                    files={"file": (fixture.name, file, "application/octet-stream")},
                )
            wait(uploaded["job"]["id"])
            analysis = request("POST", f"/documents/{uploaded['document_id']}/analyze")
            plan_id = wait(analysis["id"], "WAITING_REVIEW")["result"]["plan_id"]
            for kind in ["ppt", "video", "images"]:
                assert client.post(f"/slide-plans/{plan_id}/generate-{kind}").status_code == 409
            parsed = request("GET", f"/documents/{uploaded['document_id']}/parse-result")
            assert request("GET", f"/documents/{uploaded['document_id']}/chunks")
            result = {
                "format": extension,
                "plan_id": plan_id,
                "parse": "PASS",
                "review_gate": "PASS",
                "parser_version": parsed["parser_version"],
            }
            if extension in {"docx", "hwp"}:
                login("demo-reviewer")
                request("POST", f"/slide-plans/{plan_id}/approve", json={"version": 1, "decision": "approve"})
                for kind in ["ppt", "video"]:
                    job = request("POST", f"/slide-plans/{plan_id}/generate-{kind}")
                    artifact = wait(job["id"])["result"]
                    assert artifact["qa_status"] == "PASS"
                    artifact_id = artifact["artifact_id"]
                    request(
                        "POST",
                        f"/artifacts/{artifact_id}/approve",
                        json={"version": 1, "decision": "approve"},
                    )
                    response = client.get(f"/artifacts/{artifact_id}/download")
                    response.raise_for_status()
                    suffix = "pptx" if kind == "ppt" else "mp4"
                    sample = output_dir / "samples" / f"docker-{extension}.{suffix}"
                    sample.parent.mkdir(parents=True, exist_ok=True)
                    sample.write_bytes(response.content)
                    assert sample.stat().st_size > 1000
                    result[kind] = {**artifact, "download_bytes": sample.stat().st_size, "review": "PASS"}
                    login("other-user")
                    assert client.get(f"/artifacts/{artifact_id}/download").status_code == 403
                    login("demo-reviewer")
            login("other-user")
            assert client.get(f"/documents/{uploaded['document_id']}").status_code == 403
            result["idor"] = "PASS"
            results.append(result)
            print(f"Docker Golden {extension}: PASS", flush=True)
        result = {
            "status": "PASS",
            "transport": "actual HTTP",
            "project_id": project["id"],
            "formats_passed": len(results),
            "results": results,
            "fixture_policy": "synthetic-only",
        }
        (output_dir / "docker-golden.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result


if __name__ == "__main__":
    run()
