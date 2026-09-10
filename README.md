# 연금술사 · 작동 가능한 CPU/mock 프로토타입 v0.2.0

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

## 발표 디자인과 참고 PPT

**디자인 참고실**에서 기본 22종 디자인을 선택하거나 여러 PPTX를 업로드할 수 있습니다.
업로드는 격리→검증→스캔→별도 프로세스 스타일 추출 순서입니다. 색상·제목 크기·여백·열 배치를 PostgreSQL에 저장하며 같은 조직에서 다음 분석 때 재사용합니다.
원본 참고 PPT의 본문·로고·사진은 복제하지 않습니다. 이것은 스타일 특징 저장/검색이며 모델 가중치 재학습이 아닙니다.

프로젝트 선택 → 디자인 참고실 → **이 디자인 사용** → 프로젝트 작업실 → 문서 선택 → **분석 시작** → PPTX 생성.
기존 계획은 당시 테마를 보존합니다. 새 디자인은 다시 분석한 계획부터 적용됩니다.
기본 디자인은 8개 자체 테마와 MIT reveal.js 14개 팔레트입니다. CSS·원격 폰트는 실행하지 않으며 출처·고정 커밋·SHA256·라이선스를 보관합니다.

CPU 모드도 핵심문장 선별·중복 제거·표/차트·원문 이미지 선택과 7개 배치를 제공합니다. 실제 LLM의 의미 재작성과 동일하지 않으며 모든 HWP의 복잡한 표·그림을 복원하지는 못합니다.
세부 범위와 검증: [디자인 기능 문서](docs/DESIGN_LIBRARY.md).

## 웹에서 사용하는 순서

1. `demo-user`로 로그인하고 프로젝트를 선택하거나 만듭니다.
2. 상단 **프로토타입-검토패스** 표시를 확인합니다. 기본 dev 모드에서는 검토자를 추가할 필요가 없습니다.
3. 문서를 업로드하고 보안검사 완료 후 문서를 선택해 **분석 시작**을 누릅니다.
4. 분석이 끝나면 슬라이드 계획이 자동 표시됩니다. 변경했다면 **변경 저장**을 누릅니다.
5. **PPTX 생성**, **MP4 생성** 또는 **PPTX + MP4 함께 생성**을 누릅니다.
6. 아래 산출물에서 QA와 버전을 확인하고 **다운로드 ↓**를 누릅니다. MP4는 **검토 / 이력**에서 재생할 수 있습니다.

프로젝트 소유자는 **프로젝트 설정**에서 이름·설명·보안등급·기본 템플릿을 변경합니다.
관리자는 **사용자 관리**에서 조직 내 역할·활성 상태를 변경합니다.
검토패스는 개발용 예외이며 자동 승인 기록을 만들지 않습니다. QA 실패는 계속 검토 필요로 표시합니다.
기존 승인 흐름은 `.env`의 `PROTOTYPE_REVIEW_MODE=strict` 설정 후 Compose를 다시 기동하면 복원됩니다.
prod/offline은 strict만 허용합니다.

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
