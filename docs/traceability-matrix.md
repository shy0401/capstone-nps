# SRS 요구사항 추적표

전체 수용 완료를 주장하지 않는다. 아래 구현 경로와 시험은 관련 증거이며, 범위별 제한은 implementation-status.md를 함께 확인한다.

| SRS ID | 우선순위 | 구현 | 시험/증거 | 현재 상태 |
|---|---|---|---|---|
| FR-IAM-001 | MUST | auth.py / api.py | tests/security/test_authz.py | 구현 · 호스트 부분 검증 |
| FR-IAM-002 | MUST | auth.py / api.py | tests/security/test_authz.py | 어댑터/기본 경로 구현 · 실제 환경/복잡 형식 추가 검증 필요 |
| FR-IAM-003 | MUST | auth.py / api.py | tests/security/test_authz.py | 구현 · 호스트 부분 검증 |
| FR-IAM-004 | MUST | auth.py / api.py | tests/security/test_authz.py | 구현 · 호스트 부분 검증 |
| FR-IAM-005 | MUST | auth.py / api.py | tests/security/test_authz.py | 구현 · 호스트 부분 검증 |
| FR-IAM-006 | MUST | auth.py / api.py | tests/security/test_authz.py | 구현 · 호스트 부분 검증 |
| FR-IAM-007 | SHOULD | auth.py / api.py | tests/security/test_authz.py | 구현 · 호스트 부분 검증 |
| FR-PRJ-001 | MUST | api.py | tests/integration/test_auth_api.py | 구현 · 호스트 부분 검증 |
| FR-PRJ-002 | MUST | api.py | tests/integration/test_auth_api.py | 구현 · 호스트 부분 검증 |
| FR-DOC-001 | MUST | upload.py / work_api.py | tests/golden/test_golden.py | 구현 · 호스트 부분 검증 |
| FR-DOC-002 | MUST | upload.py / work_api.py | tests/golden/test_golden.py | 구현 · 호스트 부분 검증 |
| FR-DOC-003 | MUST | upload.py / work_api.py | tests/golden/test_golden.py | 구현 · 호스트 부분 검증 |
| FR-DOC-004 | MUST | upload.py / work_api.py | tests/golden/test_golden.py | 구현 · 호스트 부분 검증 |
| FR-DOC-005 | MUST | upload.py / work_api.py | tests/golden/test_golden.py | 구현 · 호스트 부분 검증 |
| FR-DOC-006 | MUST | upload.py / work_api.py | tests/golden/test_golden.py | 구현 · 호스트 부분 검증 |
| FR-DOC-007 | SHOULD | upload.py / work_api.py | tests/golden/test_golden.py | 구현 · 호스트 부분 검증 |
| FR-PARSE-001 | MUST | parsers.py / parse_runner.py | tests/unit/test_parsers.py | 구현 · 호스트 부분 검증 |
| FR-PARSE-002 | MUST | parsers.py / parse_runner.py | tests/unit/test_parsers.py | 어댑터/기본 경로 구현 · 실제 환경/복잡 형식 추가 검증 필요 |
| FR-PARSE-003 | MUST | parsers.py / parse_runner.py | tests/unit/test_parsers.py | 어댑터/기본 경로 구현 · 실제 환경/복잡 형식 추가 검증 필요 |
| FR-PARSE-004 | MUST | parsers.py / parse_runner.py | tests/unit/test_parsers.py | 구현 · 호스트 부분 검증 |
| FR-PARSE-005 | MUST | parsers.py / parse_runner.py | tests/unit/test_parsers.py | 구현 · 호스트 부분 검증 |
| FR-CHUNK-001 | MUST | chunking.py | tests/unit/test_parsers.py | 구현 · 호스트 부분 검증 |
| FR-CHUNK-002 | MUST | chunking.py | tests/unit/test_parsers.py | 구현 · 호스트 부분 검증 |
| FR-CHUNK-003 | MUST | chunking.py | tests/unit/test_parsers.py | 구현 · 호스트 부분 검증 |
| FR-EVD-001 | MUST | chunking.py / plans.py | tests/unit/test_llm.py | 구현 · 호스트 부분 검증 |
| FR-EVD-002 | MUST | chunking.py / plans.py | tests/unit/test_llm.py | 구현 · 호스트 부분 검증 |
| FR-EVD-003 | SHOULD | chunking.py / plans.py | tests/unit/test_llm.py | 구현 · 호스트 부분 검증 |
| FR-LLM-001 | MUST | llm.py / adapter_api.py | tests/unit/test_llm.py | 구현 · 호스트 부분 검증 |
| FR-LLM-002 | MUST | llm.py / adapter_api.py | tests/unit/test_llm.py | 구현 · 호스트 부분 검증 |
| FR-LLM-003 | MUST | llm.py / adapter_api.py | tests/unit/test_llm.py | 구현 · 호스트 부분 검증 |
| FR-LLM-004 | MUST | llm.py / adapter_api.py | tests/unit/test_llm.py | 구현 · 호스트 부분 검증 |
| FR-LLM-005 | MUST | llm.py / adapter_api.py | tests/unit/test_llm.py | 구현 · 호스트 부분 검증 |
| FR-LLM-006 | MUST | llm.py / adapter_api.py | tests/unit/test_llm.py | 구현 · 호스트 부분 검증 |
| FR-LLM-007 | MUST | llm.py / adapter_api.py | tests/unit/test_llm.py | 구현 · 호스트 부분 검증 |
| FR-LLM-008 | SHOULD | llm.py / adapter_api.py | tests/unit/test_llm.py | 구현 · 호스트 부분 검증 |
| FR-LLM-009 | SHOULD | llm.py / adapter_api.py | tests/unit/test_llm.py | 구현 · 호스트 부분 검증 |
| FR-VIS-001 | MUST | comfy.py | tests/unit/test_comfy.py | 구현 · 호스트 부분 검증 |
| FR-VIS-002 | MUST | comfy.py | tests/unit/test_comfy.py | 구현 · 호스트 부분 검증 |
| FR-VIS-003 | MUST | comfy.py | tests/unit/test_comfy.py | 구현 · 호스트 부분 검증 |
| FR-VIS-004 | MUST | comfy.py | tests/unit/test_comfy.py | 구현 · 호스트 부분 검증 |
| FR-VIS-005 | MUST | comfy.py | tests/unit/test_comfy.py | 구현 · 호스트 부분 검증 |
| FR-VIS-006 | MUST | comfy.py | tests/unit/test_comfy.py | 어댑터/기본 경로 구현 · 실제 환경/복잡 형식 추가 검증 필요 |
| FR-VIS-007 | SHOULD | comfy.py | tests/unit/test_comfy.py | 구현 · 호스트 부분 검증 |
| FR-VIS-008 | SHOULD | comfy.py | tests/unit/test_comfy.py | 구현 · 호스트 부분 검증 |
| FR-PPT-001 | MUST | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 구현 · 호스트 부분 검증 |
| FR-PPT-002 | MUST | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 구현 · 호스트 부분 검증 |
| FR-PPT-003 | MUST | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 구현 · 호스트 부분 검증 |
| FR-PPT-004 | MUST | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 구현 · 호스트 부분 검증 |
| FR-PPT-005 | MUST | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 구현 · 호스트 부분 검증 |
| FR-PPT-006 | MUST | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 구현 · 호스트 부분 검증 |
| FR-PPT-007 | MUST | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 구현 · 호스트 부분 검증 |
| FR-PPT-008 | MUST | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 구현 · 호스트 부분 검증 |
| FR-PPT-009 | MUST | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 구현 · 호스트 부분 검증 |
| FR-PPT-010 | SHOULD | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 구현 · 호스트 부분 검증 |
| FR-PPT-011 | SHOULD | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 구현 · 호스트 부분 검증 |
| FR-PPT-012 | MUST | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 구현 · 호스트 부분 검증 |
| FR-VID-001 | MUST | video.py | tests/unit/test_video.py | 구현 · 호스트 부분 검증 |
| FR-VID-002 | MUST | video.py | tests/unit/test_video.py | 구현 · 호스트 부분 검증 |
| FR-VID-003 | MUST | video.py | tests/unit/test_video.py | 구현 · 호스트 부분 검증 |
| FR-VID-004 | MUST | video.py | tests/unit/test_video.py | 구현 · 호스트 부분 검증 |
| FR-VID-005 | MUST | video.py | tests/unit/test_video.py | 구현 · 호스트 부분 검증 |
| FR-VID-006 | MUST | video.py | tests/unit/test_video.py | 구현 · 호스트 부분 검증 |
| FR-VID-007 | SHOULD | video.py | tests/unit/test_video.py | 구현 · 호스트 부분 검증 |
| FR-VID-008 | SHOULD | video.py | tests/unit/test_video.py | 구현 · 호스트 부분 검증 |
| FR-JOB-001 | MUST | jobs.py / worker.py / pipeline.py | tests/integration/test_jobs.py | 구현 · 호스트 부분 검증 |
| FR-JOB-002 | MUST | jobs.py / worker.py / pipeline.py | tests/integration/test_jobs.py | 구현 · 호스트 부분 검증 |
| FR-JOB-003 | MUST | jobs.py / worker.py / pipeline.py | tests/integration/test_jobs.py | 구현 · 호스트 부분 검증 |
| FR-JOB-004 | MUST | jobs.py / worker.py / pipeline.py | tests/integration/test_jobs.py | 구현 · 호스트 부분 검증 |
| FR-JOB-005 | MUST | jobs.py / worker.py / pipeline.py | tests/integration/test_jobs.py | 구현 · 호스트 부분 검증 |
| FR-JOB-006 | MUST | jobs.py / worker.py / pipeline.py | tests/integration/test_jobs.py | 구현 · 호스트 부분 검증 |
| FR-JOB-007 | MUST | jobs.py / worker.py / pipeline.py | tests/integration/test_jobs.py | 어댑터/기본 경로 구현 · 실제 환경/복잡 형식 추가 검증 필요 |
| FR-JOB-008 | SHOULD | jobs.py / worker.py / pipeline.py | tests/integration/test_jobs.py | 구현 · 호스트 부분 검증 |
| FR-REV-001 | MUST | plans.py / artifacts.py | tests/golden/test_golden.py | 구현 · 호스트 부분 검증 |
| FR-REV-002 | MUST | plans.py / artifacts.py | tests/golden/test_golden.py | 구현 · 호스트 부분 검증 |
| FR-REV-003 | MUST | plans.py / artifacts.py | tests/golden/test_golden.py | 구현 · 호스트 부분 검증 |
| FR-ART-001 | MUST | artifacts.py / storage.py | tests/golden/test_golden.py | 구현 · 호스트 부분 검증 |
| FR-ART-002 | MUST | artifacts.py / storage.py | tests/golden/test_golden.py | 구현 · 호스트 부분 검증 |
| FR-ART-003 | MUST | artifacts.py / storage.py | tests/golden/test_golden.py | 구현 · 호스트 부분 검증 |
| FR-ART-004 | MUST | artifacts.py / storage.py | tests/golden/test_golden.py | 구현 · 호스트 부분 검증 |
| FR-ART-005 | SHOULD | artifacts.py / storage.py | tests/golden/test_golden.py | 구현 · 호스트 부분 검증 |
| SEC-IAM-001 | MUST | auth.py / api.py | tests/security/test_authz.py | 구현 · 호스트 부분 검증 |
| SEC-IAM-002 | MUST | auth.py / api.py | tests/security/test_authz.py | 구현 · 호스트 부분 검증 |
| SEC-IAM-003 | MUST | auth.py / api.py | tests/security/test_authz.py | 구현 · 호스트 부분 검증 |
| SEC-NET-001 | MUST | compose*.yml | infra/scripts/policy_check.py | 구현 · 호스트 부분 검증 |
| SEC-NET-002 | MUST | compose*.yml | infra/scripts/policy_check.py | 구현 · 호스트 부분 검증 |
| SEC-NET-003 | MUST | compose*.yml | infra/scripts/policy_check.py | 구현 · 호스트 부분 검증 |
| SEC-DATA-001 | MUST | storage.py / auth.py | tests/security/test_gates.py | 구현 · 호스트 부분 검증 |
| SEC-DATA-002 | MUST | storage.py / auth.py | tests/security/test_gates.py | 구현 · 호스트 부분 검증 |
| SEC-DATA-003 | MUST | storage.py / auth.py | tests/security/test_gates.py | 구현 · 호스트 부분 검증 |
| SEC-FILE-001 | MUST | upload.py | tests/security/test_upload.py | 구현 · 호스트 부분 검증 |
| SEC-FILE-002 | MUST | upload.py | tests/security/test_upload.py | 구현 · 호스트 부분 검증 |
| SEC-FILE-003 | MUST | upload.py | tests/security/test_upload.py | 구현 · 호스트 부분 검증 |
| SEC-LLM-001 | MUST | llm.py / adapter_api.py | tests/unit/test_llm.py | 구현 · 호스트 부분 검증 |
| SEC-LLM-002 | MUST | llm.py / adapter_api.py | tests/unit/test_llm.py | 구현 · 호스트 부분 검증 |
| SEC-SECRET-001 | MUST | .gitignore / config.py | infra/scripts/policy_check.py | 구현 · 호스트 부분 검증 |
| SEC-AUDIT-001 | MUST | auth.py | tests/integration/test_audit.py | 구현 · 호스트 부분 검증 |
| SEC-AUDIT-002 | MUST | auth.py | tests/integration/test_audit.py | 구현 · 호스트 부분 검증 |
| SEC-SUPPLY-001 | MUST | infra/scripts/bundle.py | tests/unit/test_release_policy.py | 부분 구현 · Docker/최종 릴리스 Gate BLOCKED |
| SEC-SUPPLY-002 | MUST | infra/scripts/bundle.py | tests/unit/test_release_policy.py | 부분 구현 · Docker/최종 릴리스 Gate BLOCKED |
| SEC-OFFLINE-001 | MUST | infra/scripts/manage.py | test-results/offline-result.json | 부분 구현 · Docker/최종 릴리스 Gate BLOCKED |
| SEC-OFFLINE-002 | MUST | infra/scripts/manage.py | test-results/offline-result.json | 부분 구현 · Docker/최종 릴리스 Gate BLOCKED |
| NFR-PERF-001 | MUST | work_api.py | tests/integration/test_performance.py | 구현 · 호스트 부분 검증 |
| NFR-PERF-002 | TBD | work_api.py | tests/integration/test_performance.py | 기관 확인 필요 |
| NFR-REL-001 | MUST | jobs.py | tests/integration/test_resilience.py | 구현 · 호스트 부분 검증 |
| NFR-REL-002 | MUST | jobs.py | tests/integration/test_resilience.py | 구현 · 호스트 부분 검증 |
| NFR-MNT-001 | MUST | prompts / workflows / migrations / packages | infra/scripts/export_contracts.py | 구현 · 호스트 부분 검증 |
| NFR-PORT-001 | MUST | config.py / compose.yml | infra/scripts/policy_check.py | 구현 · 호스트 부분 검증 |
| NFR-OBS-001 | MUST | main.py / jobs.py | tests/integration/test_jobs.py | 구현 · 호스트 부분 검증 |
| NFR-ACC-001 | SHOULD | apps/web/src | apps/web/tests/workspace.spec.ts | 구현 · 호스트 부분 검증 |
| NFR-KO-001 | MUST | parsers.py / rendering.py | tests/golden/test_golden.py | 구현 · 호스트 부분 검증 |
