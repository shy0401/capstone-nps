import json
import time
from pathlib import Path
from nps.auth import issue_access


def test_metadata_api_latency_p95(client, users):
    headers = {"Authorization": "Bearer " + issue_access(users["demo-user"])}
    samples = []
    for _ in range(40):
        start = time.perf_counter()
        assert client.get("/api/v1/projects", headers=headers).status_code == 200
        samples.append(time.perf_counter() - start)
    p95 = sorted(samples)[37]
    result = {
        "p95_seconds": p95,
        "samples": len(samples),
        "target_seconds": 2,
        "status": "PASS" if p95 < 2 else "FAIL",
        "scope": "single-client metadata endpoint on host TestClient/SQLite; not institution load SLA",
    }
    out = Path("test-results")
    out.mkdir(exist_ok=True)
    (out / "performance.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    assert p95 < 2
