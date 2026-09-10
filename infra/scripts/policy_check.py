"""Checks source supply/network policy; runtime evidence is reported separately."""

import json
import re
import os
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]


def source_files():
    ignored = {
        ".venv",
        "node_modules",
        "dist",
        ".git",
        "storage",
        "release-bundle",
        "wheelhouse",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        "test-results",
        ".tools",
        ".offline-venv",
        ".idea",
        "secrets",
    }
    files = []
    for directory, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in ignored and not d.endswith(".egg-info")]
        files.extend(
            Path(directory) / n
            for n in names
            if (not n.startswith(".env") or n == ".env.example")
            and n != ".coverage"
            and not n.endswith((".pyc", ".db", ".tsbuildinfo", ".key", ".pem"))
        )
    return files


def check():
    issues = []
    compose = yaml.safe_load((ROOT / "compose.yml").read_text(encoding="utf-8"))
    published = {name: svc.get("ports", []) for name, svc in compose["services"].items() if svc.get("ports")}
    if set(published) != {"edge"}:
        issues.append("EDGE_ONLY_VIOLATION")
    for svc in compose["services"].values():
        if ":latest" in svc.get("image", "") or ":" not in svc.get("image", ""):
            issues.append("UNPINNED_IMAGE")
    for name in ["app_net", "ai_net", "data_net"]:
        if not compose["networks"][name].get("internal"):
            issues.append("INTERNAL_NETWORK_REQUIRED:" + name)
    for file in source_files():
        if file.suffix not in {".py", ".ts", ".tsx", ".json", ".yml", ".yaml", ".toml", ".md", ".txt"}:
            continue
        content = file.read_text(encoding="utf-8-sig", errors="replace")
        if re.search(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", content):
            issues.append("PRIVATE_KEY:" + file.relative_to(ROOT).as_posix())
        if re.search(r"(?:sk-[a-zA-Z0-9]{30,}|ghp_[a-zA-Z0-9]{30,})", content):
            issues.append("CREDENTIAL_PATTERN:" + file.relative_to(ROOT).as_posix())
    return {
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "static_published_ports": published,
        "runtime_published_ports": "NOT_VERIFIED_WITHOUT_RUNNING_DOCKER",
        "secret_scan_scope": "source files; injected .env excluded",
    }


if __name__ == "__main__":
    result = check()
    (ROOT / "test-results").mkdir(exist_ok=True)
    (ROOT / "test-results/security-policy.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
