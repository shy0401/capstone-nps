import importlib.util
import json


def test_edge_only_and_no_secrets():
    spec = importlib.util.spec_from_file_location("policy", "infra/scripts/policy_check.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.check()["status"] == "PASS"


def test_bundle_checksum_detects_tamper(tmp_path):
    import hashlib

    spec = importlib.util.spec_from_file_location("verify", "infra/scripts/verify_bundle.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    content = json.dumps(
        {
            k: "1"
            for k in [
                "release",
                "images",
                "model_manifest",
                "workflow",
                "prompt_pack",
                "schema_version",
                "template_version",
                "db_revision",
                "sbom",
            ]
        }
    )
    (tmp_path / "release-manifest.yaml").write_text(content, encoding="utf-8")
    (tmp_path / "checksums.sha256").write_text(
        hashlib.sha256(content.encode()).hexdigest() + "  release-manifest.yaml\n", encoding="utf-8"
    )
    assert module.verify(tmp_path)["status"] == "PASS"
    assert module.verify(tmp_path, require_ready=True)["status"] == "FAIL"
    (tmp_path / "release-manifest.yaml").write_text(content + " ", encoding="utf-8")
    assert module.verify(tmp_path)["status"] == "FAIL"
