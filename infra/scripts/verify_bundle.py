import hashlib
import json
import sys
from pathlib import Path
import yaml


def verify(root, require_ready=False):
    root = Path(root).resolve()
    issues = []
    listed = set()
    for line in (root / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            issues.append("MISSING_OR_UNSAFE:" + name)
            continue
        with path.open("rb") as f:
            actual = hashlib.file_digest(f, "sha256").hexdigest()
        if actual != digest:
            issues.append("CHECKSUM_MISMATCH:" + name)
        listed.add(name)
    expected = {
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and p.name != "checksums.sha256"
    }
    if listed != expected:
        issues.append("CHECKSUM_COVERAGE_MISMATCH")
    manifest = yaml.safe_load((root / "release-manifest.yaml").read_text(encoding="utf-8"))
    for field in [
        "release",
        "images",
        "model_manifest",
        "workflow",
        "prompt_pack",
        "schema_version",
        "template_version",
        "db_revision",
        "sbom",
    ]:
        if field not in manifest:
            issues.append("MANIFEST_FIELD:" + field)
    if require_ready and not manifest.get("release_ready"):
        issues.append("RELEASE_NOT_READY")
    return {
        "status": "PASS" if not issues else "FAIL",
        "files_verified": len(listed),
        "release_ready": manifest.get("release_ready", False),
        "issues": issues,
    }


if __name__ == "__main__":
    result = verify(sys.argv[1], "--require-ready" in sys.argv)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
