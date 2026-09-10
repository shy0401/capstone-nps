# v0.2.0 · 발표용 디자인과 참고 PPT 라이브러리

현재 Docker 웹 서비스에서 문서 업로드→핵심문장 중심 계획→테마 적용 PPTX·MP4 생성까지 사용할 수 있다. dev 검토패스는 유지한다.
이번 변경은 PPT 품질과 참고자료 재사용 기능이며, 전체 SRS/기관 운영 Release 완료 선언은 아니다. 기존 strict 요구사항 전수 분류는 별도 traceability matrix를 따른다.

## 구현

| 영역 | 현재 기능 |
|---|---|
| 내용 편집 | 중요 문장 선별·중복 제거, 원문 제목 후보 사용, 핵심 3문장 이내, 최대 10개 내용 슬라이드와 표지, 생략/근거 추적 |
| PPT 디자인 | 표지/요점/비교/절차/표/차트/이미지, 한글 어절 줄바꿈, 제목·본문 크기/행간/자간·여백 지정, native 편집 가능 |
| 디자인 참고실 | PPTX 다중 업로드, 스캔 후 색상·폰트·배치 특징 추출, 조직별 저장/선택, 같은 파일 중복 재사용, 감사로그 |
| 기본 무료 디자인 | 자체 8종 + reveal.js MIT 14종 = 22종. 출처/고정 커밋/SHA256/라이선스 보관 |
| 영상 | 같은 배치와 근거·원문 이미지, 실제 CPU MP4 인코딩/ffprobe/전체 프레임 decode |
| 보안 | 기존 RBAC/IDOR/검토 Gate 유지, 타 조직 디자인 선택 차단, 실패한 업로드는 학습 성공 처리하지 않음 |

## 검증 결과

| 검사 | 결과 / 근거 |
|---|---|
| Python 전체 | 127 PASS / 0 FAIL / 1 SKIP · test-results/design-pytest.xml |
| 신규 디자인 검사 | 기본 22테마, 편집성/overflow, 참고 업로드/조직 scope/중복, 원본 이미지, 핵심문장/evidence, source checksum 포함 |
| React 단위 | 4 PASS |
| Browser | 3 PASS · 디자인 업로드/선택, HWP 검토패스 PPTX·MP4 생성/다운로드/재생, 기존 문서 작업 흐름 |
| Docker Golden | PDF/DOCX/XLSX/HWPX/HWP 5종 분석 PASS. DOCX/HWP PPTX·MP4 QA/다운로드 PASS |
| 디자인 HTTP Golden | 참고 PPT→저장→HWP→선택 테마 PPTX PASS. 참고 본문이 새 PPT에 복제되지 않음 |
| PowerPoint | 합성 6배치 및 HTTP로 생성된 참고 테마 PPTX를 실제 PowerPoint에서 열고 PNG export PASS; 어절 끊김 수정 후 재검수 |
| Compose | 11개 서비스 정상. 실제 publish는 edge 127.0.0.1:8080 한 곳 |
| Security Gate | 정적 policy/Ruff PASS, pytest의 RBAC/IDOR/업로드/근거 방어 PASS. 실 ClamAV 연결 pytest 1건 SKIP; dev scan은 mock |
| Offline Gate | 호스트 no-index/socket-denied PPTX·MP4 subgate PASS. v0.2.0 물리 clean-host/airgap/rollback 미검증 |

테스트 자료는 전부 합성 자료이다. 사용자 문서나 개인정보를 Git/test fixture/bundle에 넣지 않았다.
합성 샘플: test-results/design/synthetic-design.pptx, docker-learned-theme.pptx, test-results/samples/prototype-browser.pptx 및 .mp4.

## 실행

```powershell
.\.venv\Scripts\python.exe infra/scripts/manage.py up
```

http://127.0.0.1:8080 접속 후 새로고침/로그인 → 프로젝트 선택 → 디자인 참고실 → 테마 선택 또는 PPTX 업로드 → 작업실 → 문서 선택 → **분석 시작** → PPTX 생성.
기존 계획/산출물은 이전 디자인을 보존한다. 새 테마는 다시 분석한 계획부터 적용된다.

## 파일 및 배포

전체 소스 트리: docs/file-tree.txt. 상세 기능: docs/DESIGN_LIBRARY.md. 현재 기능과 후속 개발: docs/FEATURES_ROADMAP.md.
개발 Release Bundle 경로: release/latest-bundle.txt. 무결성 보고서: test-results/bundle-result.json.
Bundle에는 runtime images, 소스, SBOM, checksums, release manifest, 테마 출처/라이선스, 설치·rollback 문서와 합성 검증 결과가 포함된다.
release_ready=false. 운영 반입 승인본과 구분한다.

## 남은 개발/TBD

- 실제 LLM/VLM·ComfyUI 연결 후 의미 재작성/그림 판단 품질 검증. 현재 CPU는 발췌형 편집이며 모델 가중치 학습을 수행하지 않는다.
- HWP의 표 병합/그림/페이지 복원과 OCR. 암호/DRM/배포용 HWP 제한 유지.
- 복잡한 자료별 이야기 구성, 더 많은 배치, 참고 디자인 시각 유사도 검색/관리·삭제 UI, 공식 PPT 품질 기준.
- parser 추가 격리, 기관 백신 갱신 승인, clean-host 설치·실제 승인 릴리스 rollback, 부하/SLA 검증.
- 기관 IP/VLAN·SSO·보존기간·스토리지·A40×4 배치·공식 PPT·폰트·로고·반입 정책은 기존 8개 TBD/config를 유지한다.
