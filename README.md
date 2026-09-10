# 연금술사 · 작동 가능한 CPU/mock 프로토타입 v0.1.1

React + FastAPI + PostgreSQL + Redis + 독립 Worker + Nginx 구성입니다.
SRS 110개 요구사항(95 MUST)을 기준으로 구현하며, 기관 공식 서비스/반입 승인본은 아닙니다.

## 가장 빠른 실행

Docker Desktop의 Linux 엔진을 켠 뒤 **이 저장소 루트**에서 실행합니다.
Python 3.12와 Docker Compose 2.24.4 이상이 필요합니다. 최초 다운로드 시간은 환경에 따라 달라집니다.

```powershell
python infra/scripts/bootstrap.py
docker compose -f compose.yml -f compose.dev.yml up -d --build --wait
```

브라우저: http://127.0.0.1:8080

| 계정 | 용도 |
|---|---|
| demo-user | 프로젝트 생성, 문서 업로드/분석, 산출물 요청 |
| demo-reviewer | 계획과 산출물 검토/승인 |
| demo-orgadmin | 조직 관리 |
| demo-systemadmin | 시스템 관리 |

비밀번호는 bootstrap이 로컬 `.env`에 생성한 `SEED_PASSWORD`입니다. 재실행해도 기존 비밀번호를 덮어쓰지 않습니다.
개발 모드는 화면/API에 **MOCK** 표시가 있으며 실제 모델 요약/생성형 이미지가 아닙니다.

## 웹에서 사용하는 순서

1. `demo-user`로 로그인하고 프로젝트를 선택하거나 만듭니다.
2. 새 프로젝트에서는 **검토자 선택 → demo-reviewer → 검토자 추가**를 누릅니다.
3. PDF/DOCX/XLSX/HWPX/HWP를 업로드하고 보안검사 완료를 기다립니다.
4. 문서를 선택해 **분석 시작 → 계획 보기**를 누릅니다.
5. 원문 근거를 확인하고 필요하면 제목/본문을 수정·저장합니다.
6. `demo-reviewer`로 로그인해 동일 프로젝트/문서의 **계획 승인**을 누릅니다.
7. 승인 뒤 사용자가 PPTX 생성을 요청할 수 있습니다. PPT 검토/승인 뒤 MP4 생성을 요청할 수 있습니다.
8. 결과와 QA, 버전별 다운로드는 산출물 이력에서 확인합니다. QA 실패는 검토 필요 상태로 표시됩니다.

HWP 5.x는 별도 한글 프로그램 없이 본문과 셀 안의 문자를 읽습니다. 표의 행/열·그림·원본 쪽 배치는 복원하지 않으므로 검토 경고가 표시됩니다.
암호/DRM/배포용 HWP, 스캔 PDF의 OCR은 별도 지원이 필요합니다. 파일 내용이나 검토 승인을 추정해 성공으로 처리하지 않습니다.

## 코드 검증: 새 PPT/영상 생성 없음

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pytest tests --ignore=tests/unit/test_ppt.py --ignore=tests/unit/test_video.py -k "not golden_review_ppt_video_version_audit"
.\.venv\Scripts\python.exe infra/scripts/policy_check.py
```

프런트엔드는 Node 22.12 이상(또는 Node 24 LTS)에서 `apps/web`으로 이동해 `npm ci`, `npm test`, `npm run build`로 검증합니다.
`npx playwright test workflow-no-media.spec.ts`는 실제 웹의 HWP 분석/검토자 흐름만 확인합니다.
일반 push CI도 미디어를 생성하지 않습니다. 전체 Golden/미디어 검증은 명시적으로 실행할 때만 수행합니다.

## 명시적 전체 검증 및 배포 묶음

아래 E2E 명령은 **합성 테스트 PPTX/MP4를 생성**합니다.

```powershell
python infra/scripts/manage.py e2e
python infra/scripts/offline_docker_gate.py
python infra/scripts/bundle.py --development
```

개발 bundle에는 코드, 이미지 tar/ID, 의존성 SBOM, checksum, 기존 테스트 증거와 설치 문서를 담습니다.
정확한 로컬 경로는 `release/latest-bundle.txt`입니다. `release_ready=false`는 기관 승인·물리 clean-host·이전 승인 릴리스 rollback 검증이 남았다는 뜻입니다.
기본 `bundle.py`와 `verify_bundle.py --require-ready`는 이런 미완료 릴리스를 통과시키지 않습니다.

## 문제 해결

- `dockerDesktopLinuxEngine` pipe 오류: Docker Desktop 실행 및 WSL2/가상화/재부팅 상태를 확인합니다.
- 기존 HWP 작업이 `HWP_ADAPTER_DISABLED`: 최신 이미지를 다시 build/up하고 실패 단계 재시도를 누릅니다. `.env`에서 `HWP_ENABLED=false`를 지정했다면 변경해야 합니다.
- 검토자가 새 프로젝트를 볼 수 없음: 프로젝트 소유자가 검토자를 멤버로 추가해야 합니다.
- `PLAN_APPROVAL_REQUIRED`, `PPT_REVIEW_REQUIRED`: 해당 버전의 계획/PPT를 먼저 검토·승인합니다.
- Windows CP949 출력 오류는 실행 스크립트의 UTF-8 처리로 수정했습니다.

[현재 기능과 개발 로드맵](docs/FEATURES_ROADMAP.md) · [SRS 전수 대조](docs/traceability-matrix.md) · [검증 보고서](docs/FINAL_REPORT.md) · [설치/롤백](docs/INSTALL_ROLLBACK.md)
