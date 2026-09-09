# 시험 재현과 증거

| 실행 | 증거 |
|---|---|
| `python -m pytest tests --cov=nps --cov-report=json:test-results/coverage.json --junitxml=test-results/test.xml` | pytest/JUnit/coverage |
| `python -m pytest tests/golden` | 4개 형식 + PPT/MP4/review/version/IDOR/audit |
| `python infra/scripts/policy_check.py` | edge-only 정적검사/secret scan |
| `python infra/scripts/manage.py up` | Docker 기동/포트 runtime 판정 |
| `python infra/scripts/manage.py offline-test` | 새 venv + wheelhouse + no-index + 네트워크 제한 + PPT/MP4 |
| `python infra/scripts/manage.py offline-container-test` | 사전 적재 image로 별도 프로젝트/새 volume/no-build/no-pull/egress probe/Golden/restart (Docker 필요) |
| `npm test`, `npm run build` | Vitest/strict TS/Vite |
| `npm run e2e` (실행중 서버 필요) | 실제 Edge/Playwright의 한국어 workflow |
| `powershell -File infra/scripts/powerpoint_smoke.ps1` | 실제 PowerPoint sample reopen/render + SHA256 |
| `python infra/scripts/bundle.py` | 개발 bundle + checksums/SPDX/manifest |

전체 Gate 미충족은 exit code 2 또는 nonzero로 보고한다. 개발 bundle checksum PASS는 release_ready=true를 의미하지 않는다.
`test-results/samples`의 모든 데이터는 script로 만든 합성 자료다.
