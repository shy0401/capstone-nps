# v0.1.2 실행 결과 · 검토패스와 실제 생성

**현재 dev에서는 일반 사용자로 검토자 없이 분석·PPTX·MP4 생성/다운로드가 가능하다.**
최신 사용자 요청에 따라 합성 자료로 실제 미디어 생성 검증을 다시 수행했다. 사용자 업로드 파일은 테스트나 Git에 포함하지 않았다.
전체 SRS/기관 운영 Release는 미완료다. strict 구현 기준 MUST 73 PASS / 21 PARTIAL / 1 TBD.

## 이번 수정

- dev 전용 `prototype-pass`: 계획/PPT 사람의 검토 생략, 자동 승인 기록 없음. API·Worker 모두 적용.
- 생성 요청 감사로그 `PROTOTYPE_REVIEW_BYPASS`와 artifact provenance에 모드 기록. 공식 사용 자격 없음.
- 분석 결과 자동 표시, 직접/동시 PPTX·MP4 생성 버튼, 진행·다운로드 안내, 배포용 HWP 오류 안내.
- FR-PRJ-001: 프로젝트 설정 UI(이름·설명·보안등급·기본 템플릿).
- FR-IAM-007: 조직 scope 사용자 관리 UI/API, 역할/활성 변경 전후 감사 기록.
- strict 승인 Gate·버전/근거·QA·IDOR·업로드 보안은 유지. 검토패스는 prod/offline에서 설정 오류로 차단.

## 실제 검증

| 항목 | 결과 |
|---|---|
| Python 전체(실제 PPT/영상 검사 포함) | 98 PASS / 0 FAIL / 1 SKIP · v0.1.2-tests.xml |
| React 단위 | 4 PASS |
| 브라우저 | 2 PASS: HWP 분석/설정/검토패스, 동시 생성/다운로드/MP4 재생 |
| Docker Golden | PDF/DOCX/XLSX/HWPX/HWP 5종 PASS, DOCX/HWP PPTX·MP4 QA·다운로드·IDOR PASS |
| 브라우저 실파일 | PPTX 33,738 bytes / MP4 810,170 bytes; synthetic HWP 입력 |
| Docker | 11개 dev 서비스, edge 127.0.0.1:8080만 publish |
| 정적 보안/Ruff/TypeScript/build | PASS |
| ClamAV | 기존 실제 clean/EICAR/unavailable PASS. 호스트 연결 pytest 1건 SKIP |
| Offline | 기존 격리 컨테이너 Golden PASS. 현재 커밋 물리 clean-host/rollback 미검증 |

브라우저 증거: `test-results/prototype-generation.json`, `test-results/browser.xml`.
프로젝트 경로로 생성·다운로드한 합성 샘플: `test-results/samples/prototype-browser.pptx`, `prototype-browser.mp4`.
추가 Golden 자료는 `test-results/docker-golden.json`과 samples/docker-*.
LLM/이미지는 mock이며 MP4는 실제 CPU 인코딩 파일이다. 실제 AI 요약·생성형 영상으로 주장하지 않는다.

## 실행 / 사용

```powershell
.\.venv\Scripts\python.exe infra/scripts/manage.py up
```

저장소 루트에서 실행하고 http://127.0.0.1:8080 접속. 기존 브라우저는 새로고침 후 로그인한다.
화면의 프로토타입-검토패스 확인→문서 선택→분석→PPTX + MP4 함께 생성→아래 산출물 다운로드.
기관 승인 모드 복원: `.env`에 `PROTOTYPE_REVIEW_MODE=strict` 후 같은 명령.

## 배포 / 전체 파일 / 한계

최신 개발 bundle 경로: `release/latest-bundle.txt`. 무결성: `test-results/bundle-result.json`.
source, 5종 runtime images, SBOM, checksums, model/workflow/prompt manifest, 설치·롤백 문서 및 합성 증거를 포함한다.
`release_ready=false`: 기관 백신 갱신 승인·물리 clean-host 및 이전 승인 릴리스 rollback 미완료.
전체 소스 트리 `docs/file-tree.txt`, 요구별 현황 `docs/traceability-matrix.md`, 기능/계획 `docs/FEATURES_ROADMAP.md`.
남은 항목: 배포용/암호 HWP, 복잡 표·그림·쪽 구조, OCR, 실제 LLM/Comfy/GPU, 공식 템플릿 품질, 조직 트리 UI, 대규모 장애/부하·rollback.
기관 망/SSO/GPU/저장·보존/보안/출력/성능/반입 값은 기존 8개 SRS TBD ID를 유지한다.
WSLg GUI 비활성화 우회와 edge 동적 DNS 수정은 유지한다.
