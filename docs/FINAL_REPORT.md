# 실행 결과 보고

**전체 Definition of Done 미충족.** 호스트에서 실제 코드를 실행하고 프로토타입·샘플·테스트를 만들었으나, Windows 가상화/Virtual Machine Platform 비활성으로 Docker·최종 Offline·Release Gate를 완료하지 못했다.

## 구현

React/TypeScript/Vite 한국어 UI, FastAPI REST/WS, SQLAlchemy/Alembic, PostgreSQL/Redis Compose, Nginx, 5개 독립 Worker를 작성했다.
Argon2id/local auth/refresh revoke, 4개 Role, org/project scope, IDOR, 감사로그를 구현했다.
Streaming quarantine, MIME/magic/container/ZIP guard, mock/ClamAV fail-closed scan, immutable document version, safe parser,
semantic chunk/source evidence, mock/local LLM adapter, schema-valid SlidePlan 승인 Gate를 연결했다.
Native editable PPTX/table/chart, PPT QA, CPU MP4/ffprobe/전체 frame QA, version/review/approval/부분 재생성,
queue/lease/heartbeat/progress/cancel/retry/resume 및 REST/WS 동일 snapshot을 제공한다.
Dependency hash locks, OpenAPI/JSON schemas, synthetic fixtures, offline wheels, SPDX/checksum/manifest/runbook을 작성했다.

## 파일 트리

전체 작성 소스와 생성된 검증 산출물 경로: [file-tree.txt](file-tree.txt).
설치된 .venv/.offline-venv/node_modules cache는 소스 목록에서 제외한다. Bundle 전체 payload는 checksums.sha256에 기록한다.

```text
capstone-nps/
  apps/api/nps/          API, domain, adapters, parsers, rendering, queue
  apps/web/             React, Vitest, Playwright, static build
  services/             llm-adapter, comfy-adapter
  workers/              document, llm, ppt, image, video
  packages/contracts/   JSON schemas
  prompts/              PromptPack
  workflows/comfy/      workflow/model/node locks
  templates/            internal PPT policy, video profile
  infra/                Dockerfiles, Nginx, GPU/offline overlays, scripts
  migrations/           Alembic
  tests/                unit/integration/security/golden/e2e
  openapi/openapi.yaml
  docs/                 110 requirements (95 MUST), traceability, runbooks
  test-results/         JUnit/coverage/QA/PowerPoint/browser evidence
  release/              wheelhouse, release-bundle, latest-bundle.txt
  compose.yml, compose.dev.yml, compose.prod.yml, compose.offline.yml
  requirements.lock, requirements-dev.lock, pyproject.toml
  Makefile, README.md, .env.example, .github/workflows/ci.yml
```

## 실행

```powershell
cd 'C:\Users\ggg\Documents\4학년\캡스톤\2차 모임 준비\capstone-nps'
.\.venv\Scripts\python.exe infra/scripts/bootstrap.py
docker compose -f compose.yml -f compose.dev.yml up -d --build --wait
.\.venv\Scripts\python.exe infra/scripts/manage.py test
.\.venv\Scripts\python.exe infra/scripts/manage.py e2e
.\.venv\Scripts\python.exe infra/scripts/manage.py offline-test
.\.venv\Scripts\python.exe infra/scripts/manage.py bundle
```

호스트 진단 UI: http://127.0.0.1:8080. SQLite + Redis TCP emulator를 사용하며 배포용 Compose와 구분한다.
재기동 절차는 README에 있다.

## 실제 결과

| 항목 | 결과 |
|---|---|
| Python 전체 | **58 통과, 0 실패, 1 건너뜀** (실제 ClamAV) |
| Python coverage | 77.91% (표시값 78%), subprocess/별도 서버 coverage 미통합 |
| Vitest | **3 통과, 0 실패** |
| 실제 Edge/Playwright | **1 통과, 0 실패**: 로그인/업로드/근거/승인 Gate/PPTX 다운로드 |
| strict TypeScript/Vite/Ruff | PASS |
| Golden | **5 통과**, Python 58개에 포함 |
| Alembic upgrade/downgrade/upgrade | SQLite 진단 PASS, PostgreSQL/운영 rollback 미검증 |
| metadata API p95 | 2초 미만, 실측은 test-results/performance.json (단일 client 진단) |
| Compose config | dev/prod/offline 정적 검증 PASS |
| Docker 기동 | **BLOCKED**: Virtual Machine Platform not enabled / No virtualization available |
| 외부 publish | 정적 edge-only PASS, runtime 확인 불가 |
| Security Gate | 호스트 RBAC/IDOR/업로드/secret/schema/audit PASS. real ClamAV/실망 미검증으로 전체 PASS 아님 |
| Offline Gate | 새 venv/no-index/hash wheel 설치 + Python network deny + PPT/MP4 PASS. 전체 clean-host/rollback BLOCKED |

## 샘플

- `test-results/samples/golden-synthetic.pptx`: 2 slides, editable title/body/table, QA PASS.
- 실제 Microsoft PowerPoint read-only 열기/PNG export PASS. 파일 hash는 `test-results/powerpoint-smoke.json`.
- `test-results/samples/golden-synthetic.mp4`: 1920×1080, H.264, 24fps, 4초, ffprobe/전체 frame decode PASS.
- QA: `test-results/samples/pptx-qa_report.json`, `mp4-qa_report.json`.
- 렌더 증거: `test-results/powerpoint-render/`, `workspace.png`, `artifact-review.png`.

## Release Bundle

`release/release-bundle/capstone-0.1.0-<UTC timestamp>/`. 현재 정확한 경로는 `release/latest-bundle.txt`.
무결성 결과는 `test-results/bundle-result.json`. SPDX, Linux/Windows wheels, frontend, workflow/locks, 모델 manifest,
source, 테스트 증거, checksum, install/rollback 문서를 포함한다.
**개발 검증용 `release_ready=false`**: Docker image tar/digest, 실제 ClamAV signature/통합 증거,
clean-host no-egress/이전 release rollback, container OS SBOM은 미포함/미검증이다.
Checksum PASS가 최종 릴리스 완료를 뜻하지 않으므로 bundle 명령은 성공 exit code를 반환하지 않는다.

## 남은 TBD · 제한

TBD-NPS-NET-001, TBD-NPS-IAM-001, TBD-NPS-GPU-001, TBD-NPS-STO-001,
TBD-NPS-SEC-001, TBD-NPS-OUT-001, TBD-NPS-PERF-001, TBD-NPS-REL-001은 모두 미확정이다.
기관 IP/VLAN/SSO/보존기간/공식 템플릿은 추정하지 않았다.
HWP5 미설치, 실제 LLM/Comfy/A40 미검증, 복잡 문서 fidelity/운영 부하, 원격 AI hard cancel 지연,
일부 관리자 UI와 영상 브랜딩 제한이 남는다. 기본 template/mock 결과는 승인 후에도 공식 사용 불가다.
세부 범위는 [implementation-status.md](implementation-status.md), [traceability-matrix.md](traceability-matrix.md)를 참조한다.
