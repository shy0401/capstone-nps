# SRS 요구사항 대조 · v0.1.2

MUST: PASS 73 / PARTIAL 21 / FAIL 0 / TBD 1. 기본 구현과 시험 범위이며 전체 운영 승인 판정이 아니다.

**검토 요구의 PASS는 strict 모드 기준이다.** 현재 dev는 사용자 요청에 따라 prototype-pass이며 사람의 검토/승인을 생략한다. 이 예외는 prod/offline에서 허용하지 않는다. 승인 기록을 자동 생성하지 않으며 QA·RBAC·원문 근거 검증은 유지한다.

| ID | 우선순위 | 판정 | 구현 | 시험/증거 | 남은 범위 |
|---|---|---|---|---|---|
| FR-IAM-001 | MUST | PASS | auth.py / api.py | tests/security/test_authz.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-IAM-002 | MUST | PARTIAL | auth.py / api.py | tests/security/test_authz.py | Local Provider와 교체 경계 구현. 실제 OIDC/SAML/LDAP Provider는 기관 방식 확정 후 구현/검증 필요. |
| FR-IAM-003 | MUST | PASS | auth.py / api.py | tests/security/test_authz.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-IAM-004 | MUST | PASS | auth.py / api.py | tests/security/test_authz.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-IAM-005 | MUST | PASS | auth.py / api.py | tests/security/test_authz.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-IAM-006 | MUST | PASS | auth.py / api.py | tests/security/test_authz.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-IAM-007 | SHOULD | PASS | api.py / auth.py / apps/web/src/settings.tsx | tests/integration/test_auth_api.py | 조직 scope 사용자 목록, 역할/활성 UI, 변경 전후 역할·활성 및 행위자·시간 감사로그. |
| FR-PRJ-001 | MUST | PASS | api.py / apps/web/src/settings.tsx | tests/integration/test_auth_api.py / prototype-generation.spec.ts | 프로젝트 생성/조회/설정 UI와 소유자 scope. 이름·설명·보안등급·템플릿 수정, 생성자 조직 귀속. |
| FR-PRJ-002 | MUST | PASS | api.py | tests/integration/test_auth_api.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-DOC-001 | MUST | PASS | upload.py / work_api.py | tests/golden/test_golden.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-DOC-002 | MUST | PASS | upload.py / work_api.py | tests/golden/test_golden.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-DOC-003 | MUST | PASS | upload.py / work_api.py | tests/golden/test_golden.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-DOC-004 | MUST | PASS | upload.py / work_api.py | tests/golden/test_golden.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-DOC-005 | MUST | PASS | upload.py / work_api.py | tests/golden/test_golden.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-DOC-006 | MUST | PASS | upload.py / work_api.py | tests/golden/test_golden.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-DOC-007 | SHOULD | PARTIAL | upload.py / work_api.py | tests/golden/test_golden.py | 선택 요구: 기본 경로 구현, 전수 수용 시험 미완료. |
| FR-PARSE-001 | MUST | PASS | parsers.py / parse_runner.py | tests/unit/test_parsers.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-PARSE-002 | MUST | PARTIAL | parsers.py / parse_runner.py | tests/unit/test_parsers.py | 5종 공통 모델. HWP는 본문/셀 문단을 추출하며 표·이미지·페이지 배치 복원은 미지원. |
| FR-PARSE-003 | MUST | PARTIAL | parsers.py / parse_runner.py | tests/unit/test_parsers.py | DOCX/XLSX/HWPX 기본 표 구조 보존. HWP 표는 셀 문단만 추출하고 복잡 병합 충실도 제한. |
| FR-PARSE-004 | MUST | PASS | parsers.py / parse_runner.py | tests/unit/test_parsers.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-PARSE-005 | MUST | PASS | parsers.py / parse_runner.py | tests/unit/test_parsers.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-CHUNK-001 | MUST | PASS | chunking.py | tests/unit/test_parsers.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-CHUNK-002 | MUST | PASS | chunking.py | tests/unit/test_parsers.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-CHUNK-003 | MUST | PARTIAL | chunking.py | tests/unit/test_parsers.py | 파서가 추출한 표/이미지 참조 보존. HWP 바이너리 이미지/표 구조 역추적 미지원. |
| FR-EVD-001 | MUST | PASS | chunking.py / plans.py | tests/unit/test_llm.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-EVD-002 | MUST | PASS | chunking.py / plans.py | tests/unit/test_llm.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-EVD-003 | SHOULD | PARTIAL | chunking.py / plans.py | tests/unit/test_llm.py | 선택 요구: 기본 경로 구현, 전수 수용 시험 미완료. |
| FR-LLM-001 | MUST | PARTIAL | llm.py / adapter_api.py | tests/unit/test_llm.py | mock 실제 Docker E2E PASS. local adapter 계약 시험 PASS, 실제 모델 서버 통합 미검증. |
| FR-LLM-002 | MUST | PASS | llm.py / adapter_api.py | tests/unit/test_llm.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-LLM-003 | MUST | PARTIAL | llm.py / adapter_api.py | tests/unit/test_llm.py | 5단계 JobStep 저장. mock은 결정론적 추출이며 실제 요약 모델 품질은 검증하지 않음. |
| FR-LLM-004 | MUST | PASS | llm.py / adapter_api.py | tests/unit/test_llm.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-LLM-005 | MUST | PASS | llm.py / adapter_api.py | tests/unit/test_llm.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-LLM-006 | MUST | PASS | llm.py / adapter_api.py | tests/unit/test_llm.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-LLM-007 | MUST | PASS | llm.py / adapter_api.py | tests/unit/test_llm.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-LLM-008 | SHOULD | PARTIAL | llm.py / adapter_api.py | tests/unit/test_llm.py | 선택 요구: 기본 경로 구현, 전수 수용 시험 미완료. |
| FR-LLM-009 | SHOULD | PARTIAL | llm.py / adapter_api.py | tests/unit/test_llm.py | 선택 요구: 기본 경로 구현, 전수 수용 시험 미완료. |
| FR-VIS-001 | MUST | PASS | comfy.py | tests/unit/test_comfy.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-VIS-002 | MUST | PARTIAL | comfy.py | tests/unit/test_comfy.py | 고정 seed/workflow/hash 기록 및 mock 이미지 생성. 실제 모델/노드 잠금은 config TBD. |
| FR-VIS-003 | MUST | PARTIAL | comfy.py | tests/unit/test_comfy.py | schema/adapter 옵션 구현. 실제 ControlNet/IP-Adapter workflow 실행 미검증. |
| FR-VIS-004 | MUST | PASS | comfy.py | tests/unit/test_comfy.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-VIS-005 | MUST | PARTIAL | comfy.py | tests/unit/test_comfy.py | mock/adapter 실패와 재시도 시험. 실제 Comfy 서버 장애/취소 미검증. |
| FR-VIS-006 | MUST | TBD | comfy.py | tests/unit/test_comfy.py | TBD-NPS-GPU-001: 실제 A40×4 장치 배치·예약 정책과 GPU 실환경 확인 필요. |
| FR-VIS-007 | SHOULD | PARTIAL | comfy.py | tests/unit/test_comfy.py | 선택 요구: 기본 경로 구현, 전수 수용 시험 미완료. |
| FR-VIS-008 | SHOULD | PARTIAL | comfy.py | tests/unit/test_comfy.py | 선택 요구: 기본 경로 구현, 전수 수용 시험 미완료. |
| FR-PPT-001 | MUST | PASS | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-PPT-002 | MUST | PASS | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-PPT-003 | MUST | PASS | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-PPT-004 | MUST | PASS | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-PPT-005 | MUST | PASS | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-PPT-006 | MUST | PARTIAL | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | native chart renderer 구현. 다양한 차트·원본 데이터 매핑의 Golden 범위 확대 필요. |
| FR-PPT-007 | MUST | PASS | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-PPT-008 | MUST | PARTIAL | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 텍스트/시각화 모드 수정 및 버전 재생성. 이미지 직접 편집 UI 제한, PPTX 패키지 전체 재조립. |
| FR-PPT-009 | MUST | PASS | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-PPT-010 | SHOULD | PARTIAL | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 선택 요구: 기본 경로 구현, 전수 수용 시험 미완료. |
| FR-PPT-011 | SHOULD | PARTIAL | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 선택 요구: 기본 경로 구현, 전수 수용 시험 미완료. |
| FR-PPT-012 | MUST | PASS | ppt.py | tests/unit/test_ppt.py + PowerPoint smoke | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-VID-001 | MUST | PASS | video.py | tests/unit/test_video.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-VID-002 | MUST | PASS | video.py | tests/unit/test_video.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-VID-003 | MUST | PASS | video.py | tests/unit/test_video.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-VID-004 | MUST | PASS | video.py | tests/unit/test_video.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-VID-005 | MUST | PASS | video.py | tests/unit/test_video.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-VID-006 | MUST | PASS | video.py | tests/unit/test_video.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-VID-007 | SHOULD | PARTIAL | video.py | tests/unit/test_video.py | 선택 요구: 기본 경로 구현, 전수 수용 시험 미완료. |
| FR-VID-008 | SHOULD | PARTIAL | video.py | tests/unit/test_video.py | 선택 요구: 기본 경로 구현, 전수 수용 시험 미완료. |
| FR-JOB-001 | MUST | PASS | jobs.py / worker.py / pipeline.py | tests/integration/test_jobs.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-JOB-002 | MUST | PASS | jobs.py / worker.py / pipeline.py | tests/integration/test_jobs.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-JOB-003 | MUST | PASS | jobs.py / worker.py / pipeline.py | tests/integration/test_jobs.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-JOB-004 | MUST | PASS | jobs.py / worker.py / pipeline.py | tests/integration/test_jobs.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-JOB-005 | MUST | PARTIAL | jobs.py / worker.py / pipeline.py | tests/integration/test_jobs.py | CPU 작업 취소/후속 단계 중단 검증. 실제 GPU 요청 취소는 원격 응답/timeout 지연 가능. |
| FR-JOB-006 | MUST | PASS | jobs.py / worker.py / pipeline.py | tests/integration/test_jobs.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-JOB-007 | MUST | PARTIAL | jobs.py / worker.py / pipeline.py | tests/integration/test_jobs.py | Redis/DB lease·우선순위·heartbeat·capability 구현. 실측 VRAM 기반 GPU 배정 미검증. |
| FR-JOB-008 | SHOULD | PARTIAL | jobs.py / worker.py / pipeline.py | tests/integration/test_jobs.py | 선택 요구: 기본 경로 구현, 전수 수용 시험 미완료. |
| FR-REV-001 | MUST | PASS | plans.py / artifacts.py | tests/golden/test_golden.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-REV-002 | MUST | PASS | plans.py / artifacts.py | tests/golden/test_golden.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-REV-003 | MUST | PASS | plans.py / artifacts.py | tests/golden/test_golden.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-ART-001 | MUST | PASS | artifacts.py / storage.py | tests/golden/test_golden.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-ART-002 | MUST | PASS | artifacts.py / storage.py | tests/golden/test_golden.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-ART-003 | MUST | PASS | artifacts.py / storage.py | tests/golden/test_golden.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-ART-004 | MUST | PASS | artifacts.py / storage.py | tests/golden/test_golden.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| FR-ART-005 | SHOULD | PARTIAL | artifacts.py / storage.py | tests/golden/test_golden.py | 선택 요구: 기본 경로 구현, 전수 수용 시험 미완료. |
| SEC-IAM-001 | MUST | PASS | auth.py / api.py | tests/security/test_authz.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| SEC-IAM-002 | MUST | PASS | auth.py / api.py | tests/security/test_authz.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| SEC-IAM-003 | MUST | PASS | auth.py / api.py | tests/security/test_authz.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| SEC-NET-001 | MUST | PASS | compose*.yml | infra/scripts/policy_check.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| SEC-NET-002 | MUST | PASS | compose*.yml | infra/scripts/policy_check.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| SEC-NET-003 | MUST | PASS | compose*.yml | infra/scripts/policy_check.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| SEC-DATA-001 | MUST | PASS | storage.py / auth.py | tests/security/test_gates.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| SEC-DATA-002 | MUST | PASS | storage.py / auth.py | tests/security/test_gates.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| SEC-DATA-003 | MUST | PARTIAL | storage.py / auth.py | tests/security/test_gates.py | 본문/secret 제외 로깅 및 audit allowlist 검사. 모든 외부 엔진 로그 전수 보증은 없음. |
| SEC-FILE-001 | MUST | PASS | upload.py | tests/security/test_upload.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| SEC-FILE-002 | MUST | PASS | upload.py | tests/security/test_upload.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| SEC-FILE-003 | MUST | PARTIAL | upload.py | tests/security/test_upload.py | 파서가 URL/embedded 코드를 실행하지 않음. parser 전용 OS 네트워크 namespace 격리는 미구현. |
| SEC-LLM-001 | MUST | PASS | llm.py / adapter_api.py | tests/unit/test_llm.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| SEC-LLM-002 | MUST | PASS | llm.py / adapter_api.py | tests/unit/test_llm.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| SEC-SECRET-001 | MUST | PASS | .gitignore / config.py | infra/scripts/policy_check.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| SEC-AUDIT-001 | MUST | PASS | auth.py | tests/integration/test_audit.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| SEC-AUDIT-002 | MUST | PASS | auth.py | tests/integration/test_audit.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| SEC-SUPPLY-001 | MUST | PARTIAL | infra/scripts/bundle.py | tests/unit/test_release_policy.py | 개발 bundle에 image tar/ID, Python/npm/OS SBOM, hashes 포함. 실모델 자산/기관 반입 승인 미완료. |
| SEC-SUPPLY-002 | MUST | PASS | infra/scripts/bundle.py | tests/unit/test_release_policy.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| SEC-OFFLINE-001 | MUST | PARTIAL | infra/scripts/manage.py | test-results/offline-result.json | 독립 신규 Docker volume/no-pull/no-build/egress 차단 검증 대상. 물리 clean-host 반입 검증은 별도. |
| SEC-OFFLINE-002 | MUST | PARTIAL | infra/scripts/manage.py | test-results/offline-result.json | 이전 버전 복구 runbook 제공. 실제 이전 승인 bundle을 사용한 DB/storage rollback 미검증. |
| NFR-PERF-001 | MUST | PARTIAL | work_api.py | tests/integration/test_performance.py | 단일 client metadata p95 측정. 기관 동시접속/부하 SLA는 TBD. |
| NFR-PERF-002 | TBD | PARTIAL | work_api.py | tests/integration/test_performance.py | 선택 요구: 기본 경로 구현, 전수 수용 시험 미완료. |
| NFR-REL-001 | MUST | PARTIAL | jobs.py | tests/integration/test_resilience.py | lease recovery 단위시험. 실제 컨테이너 kill 중 작업 복구 추가 검증 필요. |
| NFR-REL-002 | MUST | PASS | jobs.py | tests/integration/test_resilience.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| NFR-MNT-001 | MUST | PASS | prompts / workflows / migrations / packages | infra/scripts/export_contracts.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| NFR-PORT-001 | MUST | PASS | config.py / compose.yml | infra/scripts/policy_check.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| NFR-OBS-001 | MUST | PASS | main.py / jobs.py | tests/integration/test_jobs.py | 프로토타입 기본 계약/회귀 검증 범위. 실모델·기관 승인 완료를 의미하지 않음. |
| NFR-ACC-001 | SHOULD | PARTIAL | apps/web/src | apps/web/tests/workspace.spec.ts | 선택 요구: 기본 경로 구현, 전수 수용 시험 미완료. |
| NFR-KO-001 | MUST | PARTIAL | parsers.py / rendering.py | tests/golden/test_golden.py | 한국어 문서/PPT/화면 Golden. HWP 고어/복잡 서식, 전체 출력 파일의 글리프 보증은 제한. |
