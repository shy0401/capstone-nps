"""Create a requirement-by-requirement index from the supplied SRS, without asserting untested compliance."""

import html
import json
import re
import shutil
from pathlib import Path
from policy_check import source_files

ROOT = Path(__file__).resolve().parents[2]


def clean(text):
    return re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", " ", text))).strip()


def main():
    source = (ROOT.parent / "01_연금술사_SRS_명세서_v1.0.html").read_text(encoding="utf-8")
    rows = []
    for row in re.findall(r"<tr>(.*?)</tr>", source, re.S):
        cells = [clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
        if cells and re.fullmatch(r"(?:FR|SEC|NFR)-[A-Z]+-\d+", cells[0]):
            rows.append(dict(zip(["id", "priority", "requirement", "acceptance", "target"], cells)))
    (ROOT / "docs/requirements.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    mapping = {
        "IAM": ("auth.py / api.py", "tests/security/test_authz.py"),
        "PRJ": ("api.py", "tests/integration/test_auth_api.py"),
        "DOC": ("upload.py / work_api.py", "tests/golden/test_golden.py"),
        "PARSE": ("parsers.py / parse_runner.py", "tests/unit/test_parsers.py"),
        "CHUNK": ("chunking.py", "tests/unit/test_parsers.py"),
        "EVD": ("chunking.py / plans.py", "tests/unit/test_llm.py"),
        "LLM": ("llm.py / adapter_api.py", "tests/unit/test_llm.py"),
        "VIS": ("comfy.py", "tests/unit/test_comfy.py"),
        "PPT": ("ppt.py", "tests/unit/test_ppt.py + PowerPoint smoke"),
        "VID": ("video.py", "tests/unit/test_video.py"),
        "JOB": ("jobs.py / worker.py / pipeline.py", "tests/integration/test_jobs.py"),
        "REV": ("plans.py / artifacts.py", "tests/golden/test_golden.py"),
        "ART": ("artifacts.py / storage.py", "tests/golden/test_golden.py"),
        "NET": ("compose*.yml", "infra/scripts/policy_check.py"),
        "FILE": ("upload.py", "tests/security/test_upload.py"),
        "DATA": ("storage.py / auth.py", "tests/security/test_gates.py"),
        "SECRET": (".gitignore / config.py", "infra/scripts/policy_check.py"),
        "AUDIT": ("auth.py", "tests/integration/test_audit.py"),
        "SUPPLY": ("infra/scripts/bundle.py", "tests/unit/test_release_policy.py"),
        "OFFLINE": ("infra/scripts/manage.py", "test-results/offline-result.json"),
        "PERF": ("work_api.py", "tests/integration/test_performance.py"),
        "REL": ("jobs.py", "tests/integration/test_resilience.py"),
        "MNT": ("prompts / workflows / migrations / packages", "infra/scripts/export_contracts.py"),
        "PORT": ("config.py / compose.yml", "infra/scripts/policy_check.py"),
        "OBS": ("main.py / jobs.py", "tests/integration/test_jobs.py"),
        "ACC": ("apps/web/src", "apps/web/tests/workspace.spec.ts"),
        "KO": ("parsers.py / rendering.py", "tests/golden/test_golden.py"),
    }
    lines = [
        "# SRS 요구사항 추적표",
        "",
        "전체 수용 완료를 주장하지 않는다. 아래 구현 경로와 시험은 관련 증거이며, 범위별 제한은 implementation-status.md를 함께 확인한다.",
        "",
        "| SRS ID | 우선순위 | 구현 | 시험/증거 | 현재 상태 |",
        "|---|---|---|---|---|",
    ]
    for req in rows:
        group = req["id"].split("-")[1]
        code, test = mapping.get(group, ("docs/tbd-register.md", "미실행"))
        status = "구현 · 호스트 부분 검증"
        if group in {"OFFLINE", "SUPPLY"}:
            status = "부분 구현 · Docker/최종 릴리스 Gate BLOCKED"
        if req["priority"] == "TBD":
            status = "기관 확인 필요"
        if req["id"] in {"FR-PARSE-002", "FR-PARSE-003", "FR-IAM-002", "FR-VIS-006", "FR-JOB-007"}:
            status = "어댑터/기본 경로 구현 · 실제 환경/복잡 형식 추가 검증 필요"
        lines.append(f"| {req['id']} | {req['priority']} | {code} | {test} | {status} |")
    (ROOT / "docs/traceability-matrix.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    shutil.copy2(ROOT.parent / "02_Codex6_Astra_Prototype_Master_Prompt.txt", ROOT / "docs/MasterPrompt.md")
    files = sorted(p.relative_to(ROOT).as_posix() for p in source_files())
    generated = sorted(
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / "test-results").rglob("*")
        if p.is_file() and p.suffix not in {".log"}
    )
    (ROOT / "docs/file-tree.txt").write_text(
        "capstone-nps/\n"
        + "\n".join("  " + p for p in files)
        + "\n\nGENERATED VALIDATION ARTIFACTS\n"
        + "\n".join("  " + p for p in generated)
        + "\n\nLocal .env contains injected secrets and is deliberately not listed by content.\nInstalled .venv/.offline-venv/node_modules caches are excluded.\nRelease Bundle complete payload list: checksums.sha256.\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "requirements": len(rows),
                "must": sum(r["priority"] == "MUST" for r in rows),
                "source_files": len(files),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
