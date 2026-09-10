"""Windows Docker output decoding and failure reporting regressions."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "infra/scripts/manage.py"
spec = importlib.util.spec_from_file_location("nps_manage_test", SCRIPT)
manage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manage)


def test_capture_utf8_and_invalid_bytes():
    result = manage.capture_command(
        [sys.executable, "-c", "import os; os.write(1, bytes.fromhex('e29c93')); os.write(2, b'\\xff')"],
        timeout=10,
    )
    assert result.returncode == 0
    assert result.stdout == "\u2713"
    assert result.stderr == "\ufffd"


@pytest.mark.parametrize("format", ["array", "jsonl"])
def test_compose_json_formats(format):
    rows = [
        {"Service": "edge", "State": "running", "Publishers": [{"PublishedPort": 8080}]},
        {"Service": "api", "State": "running", "Health": "healthy"},
    ]
    output = json.dumps(rows, indent=2) if format == "array" else "\n".join(map(json.dumps, rows))
    result = manage.compose_status(subprocess.CompletedProcess([], 0, output, ""))
    assert result["status"] == "PASS"
    assert result["service_count"] == 2


@pytest.mark.parametrize("output", [None, "", "not JSON", '[{"unexpected": true}]'])
def test_bad_or_empty_compose_output_is_failure(output):
    result = manage.compose_status(subprocess.CompletedProcess([], 0, output, ""))
    assert result["status"] == "FAIL"
    assert result["reason"]


def test_compose_failure_preserves_original_error():
    result = manage.compose_status(subprocess.CompletedProcess([], 1, None, "Docker engine unavailable"))
    assert result["status"] == "FAIL"
    assert result["reason"] == "Docker engine unavailable"


def test_published_database_fails_gate():
    output = json.dumps([{"Service": "postgres", "Publishers": [{"PublishedPort": 5432}]}])
    assert manage.compose_status(subprocess.CompletedProcess([], 0, output, ""))["status"] == "FAIL"


@pytest.mark.parametrize("state,health", [("exited", ""), ("running", "unhealthy"), ("running", "starting")])
def test_nonhealthy_service_fails_gate(state, health):
    output = json.dumps([{"Service": "api", "State": state, "Health": health}])
    result = manage.compose_status(subprocess.CompletedProcess([], 0, output, ""))
    assert result["status"] == "FAIL"
    assert "not running/healthy" in result["reason"]


def test_daemon_timeout_returns_blocked(tmp_path, monkeypatch):
    monkeypatch.setattr(manage, "ROOT", tmp_path)
    monkeypatch.setattr(manage, "docker_binary", lambda: "docker")

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 15)

    monkeypatch.setattr(manage.subprocess, "run", timeout)
    result = manage.docker_gate()
    assert result["status"] == "BLOCKED"
    assert "timed out" in result["reason"]


def test_missing_service_fails_gate():
    output = json.dumps([{"Service": "edge", "State": "running"}])
    result = manage.compose_status(subprocess.CompletedProcess([], 0, output, ""), {"edge", "api"})
    assert result["status"] == "FAIL"
    assert "Missing Compose services: api" == result["reason"]


def test_other_profile_orphan_does_not_fail_current_profile():
    output = json.dumps(
        [
            {"Service": "edge", "State": "running"},
            {"Service": "clamav", "State": "exited"},
        ]
    )
    result = manage.compose_status(subprocess.CompletedProcess([], 0, output, ""), {"edge"})
    assert result["status"] == "PASS"
    assert result["service_count"] == 1


def test_orphan_external_port_still_fails_gate():
    output = json.dumps(
        [
            {"Service": "edge", "State": "running"},
            {"Service": "extra", "State": "running", "Publishers": [{"PublishedPort": 9000}]},
        ]
    )
    assert manage.compose_status(subprocess.CompletedProcess([], 0, output, ""), {"edge"})["status"] == "FAIL"
