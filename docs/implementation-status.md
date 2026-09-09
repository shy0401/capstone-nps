# 구현·검증 현황

## 원본 조사

초기 폴더에는 SRS HTML/PDF, Master Prompt TXT/HTML/PDF, 통합수행계획 HTML, 참고 이미지 2개가 있었다.
기존 코드 저장소는 없었다. SRS/Master의 텍스트 판본을 읽고 참고 이미지도 확인했다.
SRS 110개 요구사항 중 MUST는 95개다. `requirements.json`과 `traceability-matrix.md`에 모두 보존했다.
원본 문서는 변경하지 않았다. 새 구현은 `capstone-nps/` 아래에 있다.

## Phase 진행

| Phase | 구현/실행 | 검증 기록 |
|---|---|---|
| 0 | 모노레포, 계약, Compose, Nginx, health, dependency locks, CI | 초기 단위 2 PASS, Compose config PASS. 실제 Docker startup BLOCKED |
| 1 | Alembic 모델, Argon2id, JWT/refresh revoke, RBAC/org/project, audit | 누적 11 PASS |
| 2 | streaming quarantine, MIME/magic/ZIP guard, mock/ClamAV fail-closed | 누적 21 PASS. 실제 ClamAV는 host 제한으로 SKIP |
| 3 | PDF/DOCX/XLSX/HWPX, HWP5 adapter, safe subprocess, semantic chunks | 누적 27 PASS |
| 4 | local/mock LLM, task 분리, schema/evidence, review gate | 누적 30 PASS |
| 5 | DB outbox + Redis, 분리 Worker, lease, retry/resume/cancel, REST/WS | 누적 33 PASS |
| 6 | native editable PPT/table/chart, template policy, structural/text QA | footer text fitting 실패 수정 후 2/2 PASS |
| 7 | Comfy mock PNG, real HTTP contract, workflow/node/model metadata | 관련 5/5 PASS |
| 8 | approved structure storyboard, CPU MP4, ffprobe/전체 frame decode | 누적 39 PASS |
| 9 | 한국어 React workspace/review/artifact/admin | TS/build PASS, Vitest 3 PASS. CSS import 오류 수정 |
| 10 | Golden, 보안, 장애복구, 브라우저 E2E, 성능, 감사 검증 | pytest 58 PASS / 0 FAIL / 1 SKIP, browser 1 PASS. stale plan session 수정 |
| 11 | Windows/Linux wheels, offline fresh venv, SPDX SBOM, checksum, bundle/runbook | host dependency subgate PASS. 완전한 offline/release Gate BLOCKED |

상위 요구의 실환경 시험이 막힌 경우 해당 Gate를 PASS로 취급하지 않고, 호스트에서 독립 실행 가능한 다음 구현을 진행했다.

## Definition of Done 판정

**전체 DoD 미충족. 완성된 운영 반입 릴리스라고 보고하지 않는다.**

| 항목 | 판정 |
|---|---|
| Docker Compose 실제 기동 | BLOCKED: Virtual Machine Platform not enabled / No virtualization available |
| edge 외 publish 0 | Compose 정적 검사 PASS, runtime inspect 미실행 |
| Local Auth/org/project RBAC | 호스트 HTTP/DB 테스트 PASS, PostgreSQL 컨테이너 미검증 |
| 합성 PDF/DOCX/XLSX/HWPX 보안검사/parse/chunk | PASS(mock scan 명시) |
| schema-valid SlidePlan + 근거 | PASS |
| 승인 후 editable PPTX + QA | PASS. 샘플은 Microsoft PowerPoint read-only 열기/PNG export도 PASS |
| 유효 MP4/ffprobe QA | PASS. 1920×1080 H.264, 모든 frame decode |
| progress/WS/cancel/retry/resume | 호스트 테스트 PASS |
| version/review/approval/audit | PASS |
| security/golden | 호스트 테스트 PASS, real ClamAV 1 SKIP |
| bundle manifest/SBOM/checksum/install-rollback | 개발 bundle 생성. image tar/OS SBOM/실제 rollback 증거 미포함 |
| 10분 내 재현 | Docker 준비 호스트 실행 절차 제공. 본 호스트에서는 전체 재현시간 미검증 |

## 알려진 제한

- Docker/실제 PostgreSQL·Redis 컨테이너, container worker kill, image save/load, clean offline/rollback은 실행하지 못했다.
- HWP는 feature flag와 hwp5txt 설치가 필요하다. 현재 미설치. 지원 시에도 text-only best-effort이고 표/이미지는 review warning.
- PDF 복잡 레이아웃/스캔 OCR, 복잡 HWPX 병합·이미지 매핑, 초대형 표는 완전 충실도 검증 전이다. 잘못된 출력은 명시적 오류/검토로 처리한다.
- mock LLM은 근거에서 추출하는 결정론적 경로다. 실제 모델의 요약·prompt injection 강건성은 미검증.
- Real Comfy HTTP 계약은 테스트했으나 실제 모델/ControlNet/IP-Adapter/영상 Workflow 실행은 config 제공 전 미검증이다.
- 원격 AI 요청 중 취소는 응답/timeout까지 지연될 수 있다. ffmpeg는 polling 취소를 지원한다.
- PPT 부분 재생성은 변경 slide version만 증가하고 parse/LLM은 재실행하지 않지만 deck 패키지는 다시 조립한다.
- PPT QA는 보수적 font metrics 기반이다. 샘플 PowerPoint 검증을 모든 향후 문서에 대한 렌더 보증으로 일반화하지 않는다.
- Video의 logo/intro/outro 고급 편집, 실제 기관 디자인 정책과 공식 사용 허용은 미확정이다.
- Project 멤버 관리와 일부 설정은 API로 제공하고 UI는 핵심 workflow와 기본 admin 조회 중심이다.
- 기관 공식 template이 없고 mock 산출물이므로 Reviewer 승인 이후에도 official_eligible=false이다.
- SBOM은 Python/npm dependencies 범위다. container OS 패키지는 image 빌드 이후 수집해야 한다.

기관 값은 `tbd-register.md`의 8개 SRS TBD ID로 유지한다.
