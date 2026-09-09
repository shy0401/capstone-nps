import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)


def docker_binary():
    found = shutil.which("docker")
    if not found and os.name == "nt":
        candidate = (
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/DockerDesktop/resources/bin/docker.exe"
        )
        if candidate.exists():
            found = str(candidate)
    return found


def command(args, **kwargs):
    result = subprocess.run(args, **kwargs)
    if result.returncode:
        raise SystemExit(result.returncode)


def capture_command(args, *, timeout):
    """Docker emits UTF-8 even when the Windows locale defaults to CP949."""
    try:
        return subprocess.run(
            args, capture_output=True, encoding="utf-8", errors="replace", timeout=timeout
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return subprocess.CompletedProcess(args, 1, "", str(exc))


def compose_status(ps):
    failed = {"status": "FAIL", "published_ports": None}
    if ps.returncode:
        return {**failed, "reason": (ps.stderr or ps.stdout or "Docker Compose ps failed").strip()[:1000]}
    try:
        output = (ps.stdout or "").strip()
        # Compose versions emit either a JSON array or newline-delimited objects.
        rows = json.loads(output) if output.startswith("[") else [
            json.loads(line) for line in output.splitlines() if line.strip()
        ]
        if not isinstance(rows, list) or any(not isinstance(r, dict) or "Service" not in r for r in rows):
            raise ValueError("Expected Compose service objects")
        publishes = {r["Service"]: r.get("Publishers", []) for r in rows if r.get("Publishers")}
        outside = [
            name
            for name, ports in publishes.items()
            if name != "edge" and any(p.get("PublishedPort") for p in ports)
        ]
    except (ValueError, TypeError, AttributeError) as exc:
        return {**failed, "reason": f"Invalid Docker Compose status output: {exc}"}
    result = {
        "status": "PASS" if rows and not outside else "FAIL",
        "published_ports": publishes,
        "service_count": len(rows),
    }
    if not rows:
        result["reason"] = "No running Compose services found"
    elif outside:
        result["reason"] = "Non-edge services publish ports: " + ", ".join(outside)
    return result


def docker_gate(start=False):
    docker = docker_binary()
    result = {"status": "BLOCKED", "reason": "Docker executable unavailable", "published_ports": None}
    if docker:
        check = capture_command([docker, "info", "--format", "{{.ServerVersion}}"], timeout=15)
        # Docker Desktop can return 0 despite printing a daemon startup error.
        healthy = (
            check.returncode == 0
            and (check.stdout or "").strip()
            and "error" not in ((check.stdout or "") + (check.stderr or "")).lower()
        )
        if not healthy:
            result["reason"] = (check.stderr or check.stdout or "Docker daemon unavailable").strip()[:1000]
        else:
            if start:
                command(
                    [
                        docker,
                        "compose",
                        "-f",
                        "compose.yml",
                        "-f",
                        "compose.dev.yml",
                        "up",
                        "-d",
                        "--build",
                        "--wait",
                    ],
                    timeout=1800,
                )
            ps = capture_command(
                [docker, "compose", "-f", "compose.yml", "-f", "compose.dev.yml", "ps", "--format", "json"],
                timeout=30,
            )
            result = compose_status(ps)
    (ROOT / "test-results").mkdir(exist_ok=True)
    (ROOT / "test-results/docker-result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return result


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "help"
    if action == "bootstrap":
        command([sys.executable, "infra/scripts/bootstrap.py"])
    elif action == "up":
        raise SystemExit(0 if docker_gate(start=True)["status"] == "PASS" else 2)
    elif action == "down":
        command([docker_binary() or "docker", "compose", "down"])
    elif action in {"test", "security-test"}:
        command(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/security" if action == "security-test" else "tests",
                "--cov=nps",
                "--cov-report=term-missing",
                f"--junitxml=test-results/{action}.xml",
            ]
        )
    elif action == "e2e":
        if docker_gate(start=True)["status"] != "PASS":
            raise SystemExit(2)
        command([sys.executable, "infra/scripts/http_e2e.py"])
    elif action == "golden":
        command([sys.executable, "-m", "pytest", "tests/golden", "--junitxml=test-results/golden.xml"])
    elif action == "offline-test":
        venv = ROOT / ".offline-venv"
        command([sys.executable, "-m", "venv", str(venv)])
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        wheelhouse = ROOT / "release/wheelhouse" / ("windows" if os.name == "nt" else "linux-amd64")
        command(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--no-index",
                "--require-hashes",
                "--find-links",
                str(wheelhouse),
                "-r",
                "requirements.lock",
            ],
            stdout=subprocess.DEVNULL,
        )
        command([str(python), "infra/scripts/offline_smoke.py"])
        # Full release gate cannot be replaced by the dependency subgate.
        raise SystemExit(2)
    elif action == "bundle":
        command([sys.executable, "infra/scripts/bundle.py"])
    elif action == "offline-container-test":
        command([sys.executable, "infra/scripts/offline_docker_gate.py"])
    elif action == "docker-check":
        raise SystemExit(0 if docker_gate()["status"] == "PASS" else 2)
    else:
        print(
            "bootstrap | up | down | test | golden | e2e | security-test | offline-test | bundle | docker-check"
        )


if __name__ == "__main__":
    main()
