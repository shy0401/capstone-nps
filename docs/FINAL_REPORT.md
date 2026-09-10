# 프로토타입 v0.1.1 검증 보고 · 2026-09-10

**Docker CPU/mock 프로토타입은 실행 가능하다. SRS 전체 및 기관 운영 Release Gate는 미완료다.**
SRS MUST 95개: PASS 72 / PARTIAL 22 / FAIL 0 / TBD 1. PASS는 개별 프로토타입 요구의 범위이며 기관 운영 적합성 승인을 의미하지 않는다.
기능과 다음 개발 항목은 [FEATURES_ROADMAP.md](FEATURES_ROADMAP.md), 요구별 근거는 [traceability-matrix.md](traceability-matrix.md)에 정리했다.

## 이번 보완

- HWP 5.x native parser: 본문/셀 문자, 압축·비압축, 구조/메모리 제한, DRM/암호/배포용 파일 명시적 거절. `HWP_ADAPTER_DISABLED` 기본 장애 해소.
- 프로젝트 소유자가 UI에서 같은 조직의 검토자를 추가할 수 있도록 API·권한 검증 연결.
- QA 실패 작업을 성공 대신 검토 필요로 표시. 승인 Gate와 원문 근거 유지.
- 줄이 많은 문서의 다단 배치 및 내용 초과 검출, Git SHA 산출물 provenance 구성.
- Windows UTF-8 Docker 출력 처리, missing/unhealthy 서비스와 비-edge publish 실패 판정.
- Vite/Vitest 보안 업데이트 및 lock 재생성. npm audit 검출 취약점 0.
- Docker build/source bundle에서 비밀 파일·IDE 설정 제외, 컨테이너 OS SBOM·이미지 포함 개발 bundle 기능.
- 기본 CI와 추가 브라우저 검증은 미디어 생성 없이 수행. 전체 미디어 Golden은 별도 명시적 실행.

## 실행

저장소 루트에서 Docker Desktop Linux 엔진을 켜고 실행한다.

```powershell
python infra/scripts/bootstrap.py
docker compose -f compose.yml -f compose.dev.yml up -d --build --wait
```

웹 주소: http://127.0.0.1:8080
기존 가상환경에서는 `.\.venv\Scripts\python.exe infra/scripts/manage.py up`도 가능하다.
계정은 README 표 참조. 비밀번호는 로컬 `.env`의 `SEED_PASSWORD`이며 Git/배포 bundle에 포함하지 않는다.

## 실행 검증

| 검사 | 결과 | 증거/범위 |
|---|---|---|
| Docker build/up --wait | PASS | API/edge 0.1.1, dev 11개 서비스 정상 |
| 외부 publish | PASS | edge 127.0.0.1:8080만 공개; DB/Redis published=0 |
| 최신 Python 비미디어 회귀 | 85 PASS / 0 FAIL / 1 SKIP | `test-results/nonmedia-tests.xml`; 미디어 5건은 이번 실행 제외 |
| React 단위 검사 | 3 PASS / 0 FAIL | Vitest 4.1.11 |
| TypeScript/Vite build/Ruff | PASS | strict TS, Vite 7.3.6 |
| 실제 브라우저 HWP/검토자 | 1 PASS / 0 FAIL | `test-results/browser.xml`; media request 0 |
| 정적 Security Gate | PASS | `test-results/security-policy.json`; RBAC/IDOR 등 Python suite 포함 |
| 실제 ClamAV | PASS | clean 통과, EICAR 차단, unavailable 차단. `clamav-result.json` |
| npm audit | 검출 0 | `test-results/npm-audit.json` |
| Docker Golden E2E | 기존 실행 PASS | 5개 형식, DOCX/HWP PPT·MP4·검토·IDOR. `docker-golden.json` |
| 격리 offline 컨테이너 | 기존 실행 PASS | pull/build 없음, 새 volume, egress 차단, Golden·restart. `offline-container-result.json` |
| 물리 clean-host/이전 릴리스 rollback | 미검증 | 최종 운영 Release 차단 사유 |

ClamAV 호스트 경유 테스트 1건은 내부 전용 네트워크 때문에 SKIP이다. 별도 실제 컨테이너 INSTREAM 검증으로 clean/EICAR/fail-closed를 확인했다.
최신 코드 변경 후 사용자의 지시에 따라 PPT·영상은 새로 생성하지 않았다. 따라서 기존 미디어/Offline Golden 결과를 최신 커밋의 전체 재실행 결과로 주장하지 않는다.

## 기존 샘플 증거

이전 승인된 작업에서 합성 DOCX/HWP PPTX와 MP4를 생성하여 QA PASS를 확인했다.
PPTX는 편집 가능한 텍스트/표/차트 구조이며, MP4는 ffprobe와 프레임 디코드 검사 대상이다.
기존 실제 업로드 HWP의 승인된 17장 계획도 PPTX QA 및 Microsoft PowerPoint read-only 열기/17장 export를 통과했다.
사용자 문서·계획·산출물은 private storage에 보관하고 저장소나 공개 테스트에 포함하지 않는다.
현재 지시 이후 새로운 PPTX/영상 생성 또는 해당 생성 테스트 실행은 하지 않았다.

## Release Bundle

개발 snapshot 생성 명령: `python infra/scripts/bundle.py --development`.
정확한 최신 경로는 `release/latest-bundle.txt`, checksum 검사 결과는 `test-results/bundle-result.json`에 기록한다.
구성: source, Docker runtime.tar, image ID/digests, Python/npm/container OS SPDX SBOM, licenses, wheelhouse, frontend,
model/workflow/prompt version·hash, release-manifest, checksums, 기존 합성 테스트 증거, INSTALL_ROLLBACK.
`release_ready=false`: 기관 승인된 백신 갱신 정책·물리 오프라인 설치·이전 승인 릴리스 rollback 증거가 남아 있다.
개발 bundle 무결성 PASS와 운영 반입 승인 PASS를 구분한다. 대용량 bundle은 로컬 보관하고 GitHub에는 소스/문서를 push한다.

## Windows Remote Desktop/RemoteApp 오류

2026-09-10 프로세스 조사에서 WSL이 실행한 `C:/Program Files/WSL/msrdc.exe`를 확인했다.
동일 경로의 rdclientax.dll과 msrdc.exe는 버전 1.2.7214.0이며 Microsoft 서명이 정상이다.
현재 설치된 WSL 배포판은 docker-desktop뿐이다. 사용자 프로필 `.wslconfig`에 `[wsl2] guiApplications=false`를 적용하고 Docker/WSL을 재시작했다.
이후 msrdc 프로세스가 사라지고 Docker 기동 및 브라우저 테스트가 통과했다.
이 조치는 WSLg GUI 연결을 사용하지 않는 개발환경 우회이며 DLL 자체의 근본 호환성 수리를 의미하지 않는다.
Linux GUI 앱이 필요해지면 값을 true로 복원하고 WSL 종료/재시작 후 공식 WSL 구성요소를 재검증해야 한다.
설정 근거: https://learn.microsoft.com/ko-kr/windows/wsl/wsl-config

## 전체 파일 목록 / TBD / 제한

실제 프로젝트 소스 전체 목록은 [file-tree.txt](file-tree.txt). 설치 캐시·비밀·개인 업로드는 제외한다.
배포 payload 전체 파일 목록은 bundle의 checksums.sha256에 있다.
기관 TBD 8개는 [tbd-register.md](tbd-register.md): 망, SSO, GPU, 저장/보존, 보안, 공식 출력 규격, 성능, 반입 승인.
미완료 핵심: 복잡 HWP 표/그림/쪽 매핑, OCR·복잡 레이아웃, 실제 LLM/Comfy/GPU, 고급 발표 품질,
관리자 상세 UI, 대규모 장애/부하 및 물리 offline/rollback. 임의 기관 값과 실제 개인정보 테스트 데이터는 사용하지 않는다.
