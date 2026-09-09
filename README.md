# 연금술사 Capstone Prototype

SRS NPS-CAP-SRS-001 v1.0 및 Codex6 Astra Master Prompt에 기반한 React + FastAPI + PostgreSQL + Redis + 독립 Worker 모노레포.
합성 데이터만 사용한다. 기본 template과 mock 결과는 기관 공식 산출물이 아니다.

## 실행 (Docker가 준비된 호스트)

```powershell
cd 'C:\Users\ggg\Documents\4학년\캡스톤\2차 모임 준비\capstone-nps'
python infra/scripts/bootstrap.py
docker compose -f compose.yml -f compose.dev.yml up -d --build --wait
```

브라우저 `http://127.0.0.1:8080`. 계정은 `demo-user`, `demo-reviewer`, `demo-orgadmin`, `demo-systemadmin`.
비밀번호는 bootstrap이 무작위 생성한 로컬 `.env`의 `SEED_PASSWORD`를 사용한다.
문서 업로드 → 보안검사 완료 → 분석 시작 → 계획 보기 → Reviewer 계정에서 승인 → PPT 생성 → PPT 검토/승인 → MP4 생성.
최초 image 다운로드/LibreOffice 설치 시간은 환경에 따라 10분을 넘을 수 있다. 사전 준비된 bundle이면 다운로드 없이 기동한다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
.\.venv\Scripts\python.exe infra/scripts/manage.py test
.\.venv\Scripts\python.exe infra/scripts/manage.py golden
.\.venv\Scripts\python.exe infra/scripts/manage.py security-test
.\.venv\Scripts\python.exe infra/scripts/manage.py e2e
.\.venv\Scripts\python.exe infra/scripts/manage.py offline-test
.\.venv\Scripts\python.exe infra/scripts/manage.py bundle
```

Linux에서는 `.venv/bin/python` 또는 `make PYTHON=.venv/bin/python <target>`을 사용한다.
Node 22.12 이상 또는 24 LTS를 사용한다. `cd apps/web; npm ci; npm test; npm run build`.
system Node 21은 지원하지 않는다. lock 파일을 커밋하고 임의 업데이트하지 않는다.

## 현재 실행 증거

`test-results/`에 pytest/JUnit, Golden 결과, PPTX/MP4 샘플·QA, 브라우저 screenshot, Docker/Offline 판정이 있다.
`docs/implementation-status.md`와 `docs/traceability-matrix.md`는 구현과 미검증 항목을 구분한다.

현재 Windows 호스트는 Virtual Machine Platform/가상화가 비활성이어서 Docker Desktop engine 기동이 차단되었다.
실행 가능한 진단 환경 `tests/e2e/local_stack.py`는 SQLite + Redis TCP emulator를 쓴다. 이 진단 PASS를 Docker/Redis/PostgreSQL Gate PASS로 바꾸지 않는다.

```powershell
# 별도 터미널 1: 진단 서버 (개발용이며 Docker의 대체 배포 모드가 아님)
.\.venv\Scripts\python.exe tests/e2e/local_stack.py
# 별도 터미널 2
cd apps/web
npm run dev -- --port 8080
```

참고: real ClamAV/SSO/HWP5/LLM 모델/Comfy Workflow/기관 공식 템플릿/A40 검증은 해당 의존성과 승인 config를 확보한 뒤 수행한다.
설치와 안전한 rollback 절차는 [INSTALL_ROLLBACK.md](docs/INSTALL_ROLLBACK.md)에 있다.
