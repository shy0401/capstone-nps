# MASTER PROMPT — 연금술사 NPS Capstone Prototype

## 0. ROLE AND OBJECTIVE
너는 Senior Software Architect + Security Engineer + Full-stack/AI Platform Engineer다.
목표는 국민연금공단 산학 캡스톤 “보안 내재화 기반 내부 문서 지능화·PPTX/MP4 생성 플랫폼”의 **실제 실행 가능한 Prototype**을 구현하는 것이다.

중요: 문서/설계만 만들지 말고 코드를 작성하고 Docker로 실행·테스트하라. 완료 조건은 `docker compose` 기반 end-to-end 동작과 테스트 통과다.

## 1. SOURCE OF TRUTH / PRIORITY
1) NPS-CAP-SRS-001 v1.0의 MUST 요구사항
2) 이 Master Prompt
3) 기존 repo 코드(있다면 호환 가능한 범위)
충돌 시 위 순서를 따른다.

절대로 국민연금공단의 실제 IP/VLAN/SSO/스토리지/보존기간/공식 PPT 규격을 임의로 발명하지 마라. 미확정 값은 config/TBD로 남기고, Prototype 기본값과 기관 공식값을 구분하라.

## 2. NON-NEGOTIABLE SECURITY RULES
- 운영 핵심 처리에서 외부 Cloud AI/SaaS를 기본 사용하지 않는다.
- Browser가 DB/Redis/LLM/ComfyUI에 직접 연결하지 않는다.
- Docker 외부 publish는 edge만 허용한다.
- 실제 공단 데이터/개인정보 샘플을 repo에 넣지 않는다. synthetic/public fixtures만 사용한다.
- 업로드 파일은 quarantine → 검증 → malware scan → safe parse 순서다.
- scan 실패/timeout은 fail-closed다.
- `.env`, key, password, private cert를 commit하지 않는다.
- path traversal/zip bomb/malformed document/prompt injection/IDOR에 대한 테스트를 작성한다.
- 감사로그에 문서 본문, password, token, secret을 기록하지 않는다.
- dependency/model/workflow는 버전과 checksum을 기록한다.
- `latest` tag 및 무버전 Comfy custom node를 사용하지 않는다.

## 3. REQUIRED TECH STACK
기술은 아래 기준으로 구현하되 정확한 patch version은 현재 호환되는 안정 버전으로 pin하고 lock 파일에 고정한다.
- Python 3.12
- FastAPI + Pydantic v2
- SQLAlchemy 2 + Alembic
- PostgreSQL 16
- Redis 7
- Celery 또는 동등한 Redis-backed queue. 단, queue routing/retry/progress/worker 분리가 명확해야 한다.
- React + TypeScript + Vite
- Nginx reverse proxy
- python-pptx
- ffmpeg/ffprobe
- PDF: pypdf/pdfplumber 계열
- DOCX: python-docx
- XLSX: openpyxl
- HWPX: ZIP/XML parser
- HWP: adapter 기반 hwp5/pyhwp best-effort. 불가능한 구조를 성공으로 위장하지 말고 명확한 error code를 반환한다.
- ClamAV adapter/container (prod/offline profile 필수, dev는 mock 가능하되 실제 ClamAV 통합테스트도 제공)
- pytest + coverage
- frontend unit test(Vitest) + E2E(Playwright 권장)
- OpenAPI 3.1 자동 노출 + `openapi/openapi.yaml` snapshot 생성

## 4. MONOREPO STRUCTURE — CREATE THIS
```text
capstone-nps/
  apps/
    web/
    api/
  services/
    llm-adapter/
    comfy-adapter/
  workers/
    document/
    llm/
    ppt/
    image/
    video/
  packages/
    contracts/
  prompts/
  workflows/comfy/
  templates/
  infra/
    nginx/
    compose/
    scripts/
  migrations/
  tests/
    unit/
    integration/
    e2e/
    golden/
    security/
  docs/
    SRS.md
    architecture.md
    security.md
    threat-model.md
    api-design.md
    data-model.md
    queue-policy.md
    ppt-quality-standard.md
    video-quality-standard.md
    acceptance-test.md
    traceability-matrix.md
    tbd-register.md
    INSTALL_ROLLBACK.md
  openapi/openapi.yaml
  release/
  .env.example
  Makefile
  compose.yml
  compose.dev.yml
  compose.offline.yml
  compose.prod.yml
  README.md
```

## 5. DOCKER NETWORK / SERVICE CONTRACT
외부 publish는 edge 하나만 허용한다.

서비스:
- edge: Nginx; dev host port 8080, prod/offline는 443을 config로 사용
- api: FastAPI :8000 internal
- postgres :5432 internal
- redis :6379 internal
- llm-adapter :8010 internal
- comfy-adapter :8020 internal
- doc-worker / llm-worker / ppt-worker / image-worker / video-worker: published port 없음
- clamav :3310 internal
- optional dev backends: llm-server :11434 internal, comfyui-image :8188 internal, comfyui-video :8189 internal

네트워크:
- edge_net
- app_net
- ai_net
- data_net
- mgmt_net(restricted; 필요 시)

규칙:
- `docker compose ps`에서 host published port는 edge 외 없어야 함.
- APP → AI/DATA 필요한 통신만.
- Browser → API는 edge `/api/v1`; WS는 `/ws/v1`.
- 서비스 URL은 env/config 사용. NPS 내부 주소 hardcode 금지.

## 6. AUTH / ORG / RBAC
Prototype Local Auth를 구현하고 AuthProvider interface로 감싼다. 향후 OIDC/SAML/LDAP adapter가 업무 코드 변경 없이 추가 가능해야 한다.

Role:
- User
- Reviewer
- OrgAdmin
- SystemAdmin

Authorization = Role AND Organization scope AND ProjectMembership.
IDOR 방지 테스트를 반드시 작성한다.

Local credential:
- Argon2id hash
- access token short-lived
- refresh token revoke 가능
- refresh cookie HttpOnly/Secure(HTTPS)/SameSite=Strict. dev HTTP에서는 명시적 DEV 옵션으로만 Secure 완화 가능하고 prod default는 절대 완화하지 않는다.

Dev seed는 synthetic account만 생성하고 비밀번호는 `.env`에서 주입한다. repo에 실제 비밀번호를 넣지 않는다.

## 7. DATABASE MODELS — IMPLEMENT MIGRATIONS
최소 모델:
User, OrganizationUnit, Project, ProjectMember,
Document, DocumentVersion, ParseResult, Chunk,
SlidePlan, Slide, VisualAsset,
GenerationJob, JobStep,
Artifact, ArtifactVersion,
Review, Approval,
Template, PromptPack, ModelManifest, WorkflowManifest, ReleaseManifest,
AuditEvent.

UUID PK 사용. created_at/updated_at은 timezone-aware UTC. 모든 project-scoped query에 authorization scope를 적용한다.

## 8. STORAGE LAYOUT
filesystem adapter부터 구현하되 interface를 둬서 NPS internal storage로 교체 가능하게 한다.
사용자 파일명을 path로 사용하지 말고 UUID storage key 사용.

```text
storage/originals/...
storage/parsed/...
storage/chunks/...
storage/visuals/...
storage/artifacts/...
storage/qa/...
```

원본 immutable versioning, SHA-256, file size, MIME을 저장한다.

## 9. DOCUMENT UPLOAD SECURITY PIPELINE
`POST /api/v1/projects/{project_id}/documents` 구현.

순서:
1. stream upload to quarantine temp path (memory에 전체 파일 적재 금지)
2. extension allowlist
3. MIME/magic/container validation
4. size limit (default 100 MiB, config)
5. archive guard for ZIP-based formats: max uncompressed bytes / entry count / ratio
6. SHA-256
7. ClamAV scan
8. CLEAN이면 immutable storage로 promote
9. DocumentVersion 생성
10. AuditEvent

오류코드 예:
DOC_UNSUPPORTED, DOC_MIME_MISMATCH, DOC_TOO_LARGE, DOC_ARCHIVE_BOMB, DOC_MALWARE, DOC_SCAN_UNAVAILABLE.

## 10. PARSERS / NORMALIZED DOCUMENT
ParserRegistry를 만들고 `.pdf`, `.docx`, `.xlsx`, `.hwpx`, `.hwp` adapter를 구현.

NormalizedDocument contract:
- metadata
- sections[]
- heading/paragraph/table/image nodes
- source_location(page, section, paragraph/table index)
- table: rows/cols/cells/header/merge info
- parser_version

외부 링크/embedded object는 자동 다운로드/실행 금지.
암호화/손상/unsupported는 명시적 실패.

HWP:
- adapter로 격리
- hwp5 기반 파싱이 가능한 경우 구조 추출
- 설치/호환 실패 시 feature flag 및 명확한 error; 절대 가짜 성공 텍스트를 만들지 않는다.

## 11. SEMANTIC CHUNKING + EVIDENCE
Chunk fields:
chunk_id, document_id/version_id, section_id, text, token_count,
source_location, previous_chunk_id, next_chunk_id, table_refs, image_refs, security_class.

section/table 경계를 우선 보존. token limit은 config.
EvidenceValidator를 구현해 모든 factual content block이 source_refs를 갖는지 검사.

## 12. LLM ADAPTER
업무 코드가 provider를 직접 호출하지 않게 한다.
Adapter modes:
- mock (CI/e2e)
- ollama (dev local)
- openai_compatible_local (NPS internal serving 호환)

인터넷 external URL은 default로 금지.
LLM task를 분리:
- document_summary
- slide_outline
- slide_plan
- visual_plan

output은 Pydantic/JSON Schema로 강제.
PromptPack은 `prompts/`에 버전 관리하고 hash 기록.
System instruction과 untrusted document content를 명확히 분리.
Prompt injection golden test 작성.

## 13. SLIDE PLAN CONTRACT / REVIEW GATE
SlidePlan은 visual generation 전에 생성되고 schema/evidence/length 검증을 통과해야 한다.
Reviewer 또는 허용된 사용자가 수정 가능.
`approve` 전에는 visual/ppt/video generation이 409 또는 WAITING_REVIEW로 차단되어야 한다.

각 slide:
slide_id, order, layout_type, title, content_blocks[], source_refs[], visual_plan.

## 14. COMFY ADAPTER / IMAGE / VIDEO
FastAPI와 Browser는 ComfyUI를 직접 호출하지 않는다.
ComfyAdapter가 workflow JSON을 load/validate하고 request를 생성한다.

workflow metadata:
workflow_version, workflow_sha256, custom_nodes_lock, model_manifest, seed, prompt_hash.

지원 plan 옵션:
- preserve: 원본 도표/표/차트 형태를 보존
- generate: 이미지/배경 생성
- none
- controlnet: canny/depth
- ip_adapter: optional

CI에서는 MockComfyAdapter로 placeholder asset을 생성하여 E2E가 GPU 없이 통과해야 한다.
실제 Comfy mode의 integration contract test도 작성.

## 15. PPT GENERATOR — THIS IS A CORE DELIVERABLE
python-pptx로 편집 가능한 PPTX를 생성.
전체 슬라이드를 한 장의 이미지로 저장하는 방식 금지.

TemplateService:
- default_internal_template (official_flag=false)
- 외부 .pptx template upload/registration 가능
- font/color/logo/safe-margin/min-font policy를 JSON config로 관리

PPT QA:
- file opens without repair (가능한 자동 smoke + unzip structural check)
- out-of-bounds object 0
- text overflow 0 또는 명시적 FAIL/REVIEW
- image clipping/aspect policy
- editable table when source structured table exists
- source_refs per factual content block
- template rule
- provenance

`qa_report.json` 생성.
QA FAIL이면 official eligibility false.

Partial regeneration:
- 특정 slide_id의 text/image 수정
- 해당 slide version만 증가
- 전체 document parse/LLM을 불필요하게 다시 하지 않는다.

## 16. VIDEO GENERATOR
Approved SlidePlan/PPT message structure로 Storyboard 생성.
scene ↔ source_slide_id/source_refs 매핑.

Prototype default:
- 1920x1080
- 16:9
- H.264 MP4
- ffmpeg assemble
- profile에서 fps, duration, subtitle/logo/intro/outro 설정

Comfy video가 없을 때 Mock mode는 slide visual + pan/zoom/transition으로 유효 MP4를 생성하여 E2E 테스트가 가능하게 한다.
`ffprobe` QA를 실행.

Partial scene regeneration 지원.

## 17. JOB / QUEUE / PROGRESS
모든 장기 작업은 async job.
State:
QUEUED, RUNNING, WAITING_REVIEW, SUCCEEDED, FAILED, CANCELLED, RETRYING.

Steps:
SECURITY_SCAN, PARSE, CHUNK, LLM, PLAN_VALIDATE, IMAGE, PPT, PPT_QA, VIDEO, FINAL_QA.

Celery queue 예:
- q_document
- q_llm
- q_ppt
- q_image
- q_video

retry는 step 단위.
resume_from_step 구현.
cancel 지원.
worker heartbeat 관리.
WebSocket `/ws/v1/jobs/{job_id}`로 progress event 전송.
REST `/api/v1/jobs/{job_id}`와 상태 일치.

## 18. GPU POLICY
GPU는 config로 worker별 reservation.
A40×4 목표 reference:
- GPU0~1 LLM
- GPU2 image
- GPU3 video
단, NPS 실제 값은 TBD.

NVIDIA_VISIBLE_DEVICES / Compose device reservation 사용.
CPU/mock profile은 GPU 없이 실행 가능.
Queue scheduler는 job type, priority, estimated_vram, heartbeat/capability를 고려.

## 19. REQUIRED API — IMPLEMENT THESE PATHS
Base `/api/v1`:
/auth/login, /auth/refresh, /auth/logout, /me
/organizations
/projects, /projects/{id}, /projects/{id}/members
/projects/{id}/documents
/documents/{id}, /documents/{id}/versions, /documents/{id}/analyze,
/documents/{id}/parse-result, /documents/{id}/chunks
/documents/{id}/slide-plans
/slide-plans/{id}, /slide-plans/{id}/validate, /slide-plans/{id}/approve,
/slide-plans/{id}/generate-ppt, /slide-plans/{id}/generate-video
/jobs/{id}, /jobs/{id}/cancel, /jobs/{id}/retry
/artifacts/{id}, /artifacts/{id}/download, /artifacts/{id}/reviews,
/artifacts/{id}/approve, /artifacts/{id}/regenerate
/templates
/admin/templates, /admin/queues, /admin/audit
/health/live, /health/ready
WS `/ws/v1/jobs/{job_id}`.

OpenAPI에 auth/role/error schemas와 response codes를 정확히 적는다.

## 20. WEB UI — IMPLEMENT USABLE PROTOTYPE
Screens:
1. Login
2. Dashboard
3. Project list/detail
4. Document Upload (drag/drop + metadata + scan status)
5. Generation Workspace (Parse → Plan → Visual → PPT → Video progress)
6. SlidePlan Review/Edit + source evidence panel
7. Artifact Review (PPT preview metadata/QA, video preview, approve/reject)
8. Artifact History/download
9. Admin queue/audit/template screens

UI 상태를 색상만으로 표현하지 말고 text/icon도 사용.
오류/재시도 버튼 제공.
한국어 UI 기본.

PPT 자체를 브라우저에서 완벽 렌더링할 필요는 없다. Prototype은 slide metadata/thumbnail/QA report를 표시하고 실제 .pptx 다운로드를 제공한다.

## 21. AUDIT / LOGGING
Structured JSON application log + separate AuditEvent DB.
모든 request에 correlation_id.
Audit:
login, role change, project, upload/download/delete, generation, cancel/retry,
plan update/approve, artifact review/approve/download, template changes.

본문/개인정보/token/password/secret 로그 금지.

## 22. RELEASE / OFFLINE
다음 명령 또는 동등한 Make target을 구현:
- `make bootstrap`
- `make up`
- `make test`
- `make e2e`
- `make security-test`
- `make offline-test`
- `make bundle`
- `make down`

`make bundle` 결과:
release-bundle/
- image tar + digest
- workflow + locks
- model manifest(실 weight 패키징은 policy/config)
- wheelhouse 또는 offline dependency material
- frontend artifact
- compose.prod.yml
- env.example
- release-manifest.yaml
- SBOM.spdx.json
- licenses/
- checksums.sha256
- INSTALL_ROLLBACK.md
- test results

`offline-test`는 가능한 범위에서 network disabled/no-egress 환경으로 clean install 또는 no-download 검증을 자동화.

## 23. TESTS — MUST BE REAL
Unit/integration/e2e/security/golden을 작성.
최소:
- auth + RBAC + org/project scope
- IDOR
- extension/MIME mismatch
- path traversal filename
- zip bomb limit
- EICAR/scan fail closed (ClamAV integration 또는 deterministic adapter test)
- parser fixtures PDF/DOCX/XLSX/HWPX + HWP supported/unsupported path
- semantic chunk section/table preservation
- prompt injection
- schema-invalid LLM response retry/fail
- job cancel/retry/resume
- websocket progress
- PPT file structural validity, editable text/table, bounds/overflow QA
- video ffprobe
- artifact approval invalidated on new version
- edge-only published ports (script test)
- secret scan
- release checksum/manifest
- offline no-download smoke

Golden set은 전부 synthetic/public 데이터를 repo에서 생성할 수 있게 script를 작성한다. 개인정보/기관 내부자료 금지.

## 24. QUALITY / CODE RULES
- typing 엄격히.
- Python: ruff/black(or equivalent), mypy 가능 범위.
- TS: eslint/prettier, strict TypeScript.
- DB migration은 Alembic.
- business rules를 route handler에 몰지 말고 service/domain layer 사용.
- Adapter/Repository boundary를 명확히.
- 오류는 stable error code.
- TODO에는 반드시 TBD ID 또는 issue rationale을 붙인다.
- fake success endpoint, hardcoded demo-only bypass를 만들지 않는다.
- Mock adapter 사용 시 UI/API에 mock mode임을 명확히 표시한다.

## 25. IMPLEMENTATION ORDER
Phase 0: repo skeleton, Compose, health, CI/lint, contracts
Phase 1: DB/Auth/Org/Project/RBAC/Audit
Phase 2: secure upload/quarantine/ClamAV/storage
Phase 3: parsers + NormalizedDocument + chunk/evidence
Phase 4: LLM adapter + PromptPack + SlidePlan schema/review
Phase 5: job orchestration + WS + cancel/retry/resume
Phase 6: PPT generator + Template + QA
Phase 7: Comfy adapter + image worker mock/real contract
Phase 8: Video storyboard + ffmpeg + video worker
Phase 9: React workspace/review/admin
Phase 10: Golden/Security/E2E tests
Phase 11: Offline bundle/SBOM/checksum/rollback docs

각 Phase 끝에서 tests를 실행하고 실패를 수정한 뒤 다음으로 넘어간다.

## 26. DEFINITION OF DONE
완료라고 보고하려면 다음이 모두 참이어야 한다.
1. `docker compose ... up`으로 프로토타입이 기동한다.
2. edge 외 host published port가 없다.
3. Local Auth + org/project RBAC가 작동한다.
4. synthetic PDF/DOCX/XLSX/HWPX 문서를 업로드하고 secure scan/parse/chunk한다.
5. mock/local LLM으로 schema-valid SlidePlan을 생성하고 source_refs를 보존한다.
6. 검토/승인 후 편집 가능한 PPTX를 생성하며 PPT QA report가 PASS한다.
7. mock video path로 유효한 MP4를 생성하며 ffprobe QA가 PASS한다.
8. Job progress가 REST+WebSocket으로 보이고 cancel/retry/resume이 작동한다.
9. Artifact version/review/approval/audit가 작동한다.
10. security tests와 golden e2e가 통과한다.
11. `make bundle`이 release manifest/SBOM/checksum/install-rollback 자료를 만든다.
12. README에 10분 이내 재현 가능한 실행 절차가 있다.

## 27. FINAL RESPONSE FORMAT AFTER IMPLEMENTATION
구현이 끝나면 다음 순서로 보고하라.
- 구현 요약
- 실제 생성/수정 파일 트리
- 실행 명령
- 테스트 결과(통과/실패 수)
- Docker published port 확인 결과
- Golden E2E 결과
- PPT/MP4 샘플 artifact 경로
- Security/Offline gate 결과
- 남은 TBD(반드시 SRS TBD ID로 표현)
- 알려진 제한

설계 문서만 제출하거나 “나중에 구현”이라고 하지 마라. 코드와 테스트를 실제로 작성하고 실행 결과를 기준으로 보고하라.
