"""No-build/no-pull, isolated-volume container golden and no-egress probe.

Requires preloaded images and a real ClamAV database. Does not delete volumes.
Clean physical host / previous-release rollback remains separate required evidence.
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from manage import docker_binary

ROOT = Path(__file__).resolve().parents[2]


def run():
    docker = docker_binary()
    project = "nps-offline-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    compose = [
        docker or "docker",
        "compose",
        "-p",
        project,
        "-f",
        "compose.yml",
        "-f",
        "compose.offline.yml",
        "-f",
        "infra/compose/compose.offline-test.yml",
    ]
    calls = []

    def command(args, timeout=300):
        result = subprocess.run(
            args, capture_output=True, encoding="utf-8", errors="replace", timeout=timeout, cwd=ROOT
        )
        calls.append({"operation": " ".join(args[:5]), "exit_code": result.returncode})
        if result.returncode:
            raise RuntimeError(
                "OFFLINE_CONTAINER_COMMAND_FAILED: " + (result.stderr or result.stdout)[-1500:]
            )
        return result.stdout

    outcome = {"status": "BLOCKED", "project": project}
    try:
        command(compose + ["up", "-d", "--no-build", "--pull", "never", "--wait"], timeout=600)
        # Seed only synthetic test accounts into this new isolated verification project.
        seed = "from nps.seed import seed; from nps.db import SessionLocal; from nps.config import settings; db=SessionLocal(); seed(db,settings().seed_password); db.close()"
        command(compose + ["exec", "-T", "api", "python", "-c", seed])
        egress = "import socket,sys\ntry:\n socket.create_connection(('example.com',443),3)\nexcept OSError:\n sys.exit(0)\nelse:\n sys.exit(1)"
        command(compose + ["exec", "-T", "api", "python", "-c", egress])
        command(compose + ["exec", "-T", "api", "python", "infra/scripts/clamav_smoke.py"])
        command(compose + ["exec", "-T", "api", "python", "infra/scripts/http_e2e.py"], timeout=600)
        command(
            compose
            + ["restart", "api", "doc-worker", "llm-worker", "ppt-worker", "image-worker", "video-worker"]
        )
        command(compose + ["up", "-d", "--no-build", "--pull", "never", "--wait"])
        outcome = {
            "status": "PASS",
            "project": project,
            "no_pull": True,
            "no_build": True,
            "isolated_new_volumes": True,
            "egress_probe": "DENIED",
            "golden": "PASS",
            "restart": "PASS",
            "clean_physical_host": "NOT_VERIFIED",
            "previous_release_rollback": "NOT_VERIFIED",
        }
    except (RuntimeError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
        outcome["reason"] = str(exc)
    finally:
        if docker:
            try:
                subprocess.run(compose + ["down"], capture_output=True, timeout=60, cwd=ROOT)
            except subprocess.TimeoutExpired:
                pass
        outcome["operations"] = calls
        (ROOT / "test-results/offline-container-result.json").write_text(
            json.dumps(outcome, indent=2), encoding="utf-8"
        )
    print(json.dumps(outcome, indent=2))
    return outcome["status"] == "PASS"


if __name__ == "__main__":
    raise SystemExit(0 if run() else 2)
