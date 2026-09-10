import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import argparse
import tomllib
from datetime import datetime, timezone
from pathlib import Path
import yaml
from manage import docker_binary, docker_gate
from policy_check import source_files
from verify_bundle import verify

ROOT = Path(__file__).resolve().parents[2]
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def build():
    # Versioned directory prevents overwriting evidence or an earlier release.
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "release/release-bundle" / ("capstone-" + VERSION + "-" + stamp)
    out.mkdir(parents=True)
    for name in [
        "images",
        "models",
        "comfy",
        "wheelhouse",
        "frontend",
        "licenses",
        "TEST_RESULTS",
        "source",
        "infra/nginx",
        "infra/scripts",
    ]:
        (out / name).mkdir(parents=True, exist_ok=True)
    for path in source_files():
        rel = path.relative_to(ROOT)
        if rel.parts[0] == "release":
            continue
        dest = out / "source" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
    for name in ["compose.yml", "compose.prod.yml", "compose.offline.yml", "compose.dev.yml"]:
        shutil.copy2(ROOT / name, out / name)
    shutil.copy2(ROOT / ".env.example", out / "env.example")
    shutil.copy2(ROOT / "docs/INSTALL_ROLLBACK.md", out / "INSTALL_ROLLBACK.md")
    shutil.copytree(ROOT / "infra/nginx", out / "infra/nginx", dirs_exist_ok=True)
    shutil.copy2(ROOT / "infra/scripts/verify_bundle.py", out / "infra/scripts/verify_bundle.py")
    shutil.copytree(ROOT / "workflows/comfy", out / "comfy", dirs_exist_ok=True)
    shutil.copy2(ROOT / "services/llm-adapter/model-manifest.json", out / "models/llm-manifest.json")
    if (ROOT / "apps/web/dist").exists():
        shutil.copytree(ROOT / "apps/web/dist", out / "frontend", dirs_exist_ok=True)
    if (ROOT / "release/wheelhouse").exists():
        shutil.copytree(ROOT / "release/wheelhouse", out / "wheelhouse", dirs_exist_ok=True)
    evidence_suffixes = {".json", ".xml", ".png", ".pptx", ".mp4", ".txt"}
    for path in (ROOT / "test-results").rglob("*"):
        if path.is_file() and path.suffix in evidence_suffixes and path.stat().st_size > 0:
            destination = out / "TEST_RESULTS" / path.relative_to(ROOT / "test-results")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
    docker = docker_binary()
    state = docker_gate()
    images, missing, os_packages = {}, [], []
    if state["status"] == "PASS":
        response = subprocess.run(
            [docker, "compose", "-f", "compose.yml", "-f", "compose.prod.yml", "config", "--images"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        tags = sorted(set(response.stdout.splitlines()))
        for tag in tags:
            inspection = subprocess.run(
                [docker, "image", "inspect", tag], capture_output=True, encoding="utf-8", errors="replace"
            )
            if inspection.returncode:
                missing.append("image:" + tag)
            else:
                metadata = json.loads(inspection.stdout)[0]
                images[tag] = {"id": metadata["Id"], "repo_digests": metadata.get("RepoDigests", [])}
                query = "if command -v dpkg-query >/dev/null; then dpkg-query -W -f='${Package}\\t${Version}\\n'; else apk list --installed; fi"
                inventory = subprocess.run(
                    [docker, "run", "--rm", "--network", "none", "--entrypoint", "sh", tag, "-c", query],
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                )
                if inventory.returncode:
                    missing.append("Container OS package inventory: " + tag)
                else:
                    for line in inventory.stdout.splitlines():
                        if not line.strip():
                            continue
                        name, _, version = line.partition("\t")
                        os_packages.append(
                            {
                                "SPDXID": "SPDXRef-OS-" + str(len(os_packages)),
                                "name": name,
                                "versionInfo": version or "see package name",
                                "downloadLocation": "NOASSERTION",
                                "filesAnalyzed": False,
                                "licenseConcluded": "NOASSERTION",
                                "licenseDeclared": "NOASSERTION",
                                "copyrightText": "NOASSERTION",
                                "comment": "image: " + tag,
                            }
                        )
        if len(images) == len(tags):
            subprocess.run([docker, "save", "-o", str(out / "images/runtime.tar"), *tags], check=True)
    else:
        missing += ["Docker image tar + built image digest (Docker unavailable)"]
    missing += [
        "Institutional approval of ClamAV signature freshness/update policy",
        "Clean-host no-egress installation and rollback evidence",
    ]
    # Runtime imports the bundled source, which may be newer than an editable
    # distribution left in the developer's venv. Describe the released source.
    packages = os_packages + [
        {
            "SPDXID": "SPDXRef-App",
            "name": "capstone-nps",
            "versionInfo": VERSION,
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False,
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": "NOASSERTION",
            "copyrightText": "NOASSERTION",
            "comment": "Bundled application source at git " + git_sha(),
        }
    ]
    catalog = json.loads((ROOT / "templates/catalog.json").read_text(encoding="utf-8"))
    shutil.copy2(ROOT / "templates/vendor/reveal/LICENSE", out / "licenses/reveal-theme-MIT.txt")
    for theme in catalog:
        if theme.get("source_sha256"):
            packages.append(
                {
                    "SPDXID": "SPDXRef-Theme-" + theme["slug"],
                    "name": theme["name"],
                    "versionInfo": theme["source_commit"],
                    "downloadLocation": theme["source_url"],
                    "filesAnalyzed": False,
                    "licenseConcluded": "MIT",
                    "licenseDeclared": "MIT",
                    "copyrightText": "See licenses/reveal-theme-MIT.txt",
                    "checksums": [{"algorithm": "SHA256", "checksumValue": theme["source_sha256"]}],
                    "comment": theme["adaptation"],
                }
            )
    for index, dist in enumerate(
        sorted(importlib.metadata.distributions(), key=lambda d: d.metadata.get("Name", ""))
    ):
        name = dist.metadata.get("Name", "unknown")
        if name.lower().replace("_", "-") == "capstone-nps":
            continue
        spdx_id = "SPDXRef-Python-" + str(index)
        license_value = dist.metadata.get("License-Expression") or "NOASSERTION"
        packages.append(
            {
                "SPDXID": spdx_id,
                "name": name,
                "versionInfo": dist.version,
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "licenseConcluded": license_value,
                "licenseDeclared": license_value,
                "copyrightText": "NOASSERTION",
            }
        )
        license_files = [
            p for p in (dist.files or []) if "license" in str(p).lower() or "copying" in str(p).lower()
        ]
        for i, relative in enumerate(license_files):
            source = Path(dist.locate_file(relative))
            if source.is_file():
                target = out / "licenses" / name / f"{i}-{source.name}"
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
    npm = json.loads((ROOT / "apps/web/package-lock.json").read_text(encoding="utf-8"))
    for index, (name, data) in enumerate(npm["packages"].items()):
        if not name:
            continue
        packages.append(
            {
                "SPDXID": "SPDXRef-Npm-" + str(index),
                "name": name,
                "versionInfo": data.get("version", "unknown"),
                "downloadLocation": data.get("resolved", "NOASSERTION"),
                "filesAnalyzed": False,
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": data.get("license", "NOASSERTION"),
                "copyrightText": "NOASSERTION",
            }
        )
    sbom = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "capstone-nps-development-bundle",
        "documentNamespace": "https://spdx.org/spdxdocs/capstone-nps-" + stamp,
        "creationInfo": {
            "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "creators": ["Tool: capstone-nps-bundle-" + VERSION],
        },
        "packages": packages,
        "relationships": [
            {
                "spdxElementId": "SPDXRef-DOCUMENT",
                "relationshipType": "DESCRIBES",
                "relatedSpdxElement": p["SPDXID"],
            }
            for p in packages
        ],
        "documentComment": "Python/npm inventory plus available built-container OS packages. NOASSERTION is not license clearance.",
    }
    (out / "SBOM.spdx.json").write_text(json.dumps(sbom, indent=2), encoding="utf-8")
    (out / "licenses/PROJECT-NOTICE.txt").write_text(
        "Project source ownership/distribution remains subject to the capstone agreement. No open-source license is inferred. Dependency licenses are included separately.",
        encoding="utf-8",
    )
    manifest = {
        "release": "capstone-v" + VERSION,
        "profile": "cpu-mock-prototype",
        "prototype_golden": read_status("docker-golden.json", "status"),
        "clamav_integration": read_status("clamav-result.json", "status"),
        "release_ready": False,
        "status": "INCOMPLETE_DEVELOPMENT_BUNDLE",
        "app_git_sha": git_sha(),
        "images": images,
        "missing_materials": missing,
        "model_manifest": {
            "path": "models/llm-manifest.json",
            "sha256": digest(out / "models/llm-manifest.json"),
        },
        "workflow": {"version": "wf-image-1.0", "sha256": digest(ROOT / "workflows/comfy/wf-image-v1.json")},
        "prompt_pack": {"version": "prompt-slide-2.0", "sha256": digest(ROOT / "prompts/slide-v1.json")},
        "schema_version": "1.0",
        "template_version": "2.0",
        "design_library": {
            "bundled_themes": len(catalog),
            "catalog_sha256": digest(ROOT / "templates/catalog.json"),
            "learning": "style-features-2.0; no weight training",
        },
        "db_revision": "a21_theme_scope",
        "sbom": "SBOM.spdx.json",
        "offline_golden_test": read_status("offline-container-result.json", "status"),
        "host_golden_test": read_status("golden-result.json", "status"),
        "host_dependency_subgate": read_status("offline-result.json", "host_dependency_subgate"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_policy": "synthetic-only",
    }
    (out / "release-manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    checksums = [
        digest(p) + "  " + p.relative_to(out).as_posix() for p in sorted(out.rglob("*")) if p.is_file()
    ]
    (out / "checksums.sha256").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    verification = verify(out)
    (ROOT / "test-results/bundle-result.json").write_text(
        json.dumps({**verification, "path": str(out), "missing_materials": missing}, indent=2),
        encoding="utf-8",
    )
    (ROOT / "release/latest-bundle.txt").write_text(str(out), encoding="utf-8")
    print(json.dumps({**verification, "path": str(out), "missing_materials": missing}, indent=2))
    return out


def git_sha():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, encoding="utf-8", errors="replace"
    )
    return result.stdout.strip() if result.returncode == 0 else "UNCOMMITTED_WORKSPACE"


def read_status(name, key):
    path = ROOT / "test-results" / name
    return json.loads(path.read_text(encoding="utf-8")).get(key, "NOT_RUN") if path.exists() else "NOT_RUN"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--development", action="store_true", help="Package a clearly non-production development snapshot"
    )
    args = parser.parse_args()
    out = build()
    result = verify(out, require_ready=not args.development)
    # Default command remains a strict release gate; explicit dev packaging checks integrity only.
    raise SystemExit(0 if result["status"] == "PASS" else 2)
