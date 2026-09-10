# 발표 디자인 · v0.2.0

## 사용

1. 프로젝트 선택 → 왼쪽 **디자인 참고실**.
2. 기본 디자인을 고르거나 `.pptx` 여러 개 업로드. 작업 완료 후 조직의 디자인 목록에 추가된다.
3. **이 디자인 사용** 또는 **내용에 맞게 자동 선택**. 프로젝트 소유자가 설정한다.
4. 프로젝트 작업실 → 문서 선택 → **분석 시작**. 기존 계획을 다시 생성해야 새 디자인이 반영된다.
5. 계획 확인/수정 후 PPTX 생성. dev에서는 기존 프로토타입 검토패스가 적용된다.

## 구현된 범위

| 요구 | 구현 |
|---|---|
| 발표용 내용 | CPU 문장 중요도·수치·핵심어 점수, 중복 제거, 최대 10개 내용 장면+표지. 3개 이내 핵심 문장을 선별한다. 생략은 말줄임과 provenance의 제외 chunk 수로 표시 |
| 제목/행간/자간 | 원문에서 제목 후보 선택, 제목과 중복 본문 제거, 어절 단위 줄바꿈. 제목 30–40pt, 본문 기본 24pt·최소 18pt, 행간 1.22, 자간 명시적 0 |
| 디자인 | 표지·요점·비교·절차·표·차트·이미지. 텍스트/도형/표/차트를 편집 가능한 native PPTX로 생성 |
| 그림/수치 | 파서가 제공한 원문 image node를 근거와 함께 보존, 수치 표를 native chart로 선택. 비교·절차는 도형/배치로 구성 |
| 참고 PPT 기억 | 색상·마스터 팔레트·폰트 통계·제목 크기·제목 여백·열 배치·shape 위치 특징 저장. 일부 특징을 안전한 발표 배치로 정규화하여 적용 |
| 자동 선택 | 프로젝트 명시 선택 우선. 그 외 제목 태그와 업로드 이력 기반 조직 내 검색. 복잡한 시각 유사도/embedding 검색은 아직 없음 |
| 기본 테마 | 자체 8종 + reveal.js MIT 14종의 색상 팔레트. `templates/catalog.json`과 원본 CSS, LICENSE, SHA256 포함 |
| 지속성 | PostgreSQL Template에 조직 scope와 설정 저장, 원본은 서버 storage. 분석 당시 디자인 snapshot을 계획 provenance에 고정 |
| 보안 | 격리→형식/ZIP 검증→스캔→시간/메모리 제한 subprocess 추출. 타 조직 디자인 ID 조회/선택 방지, 감사로그, 실패를 성공으로 표시하지 않음 |
| 영상 | 동일 scene geometry와 텍스트·이미지 사용. CPU 차트는 같은 수치를 그리며 ffmpeg/ffprobe 검사. PowerPoint 렌더와 픽셀 단위 동일성은 보장하지 않음 |

## 학습이라는 표현의 의미

파일을 업로드할 때마다 **스타일 특징을 추출·저장·검색**한다. AI 모델의 가중치 fine-tuning은 수행하지 않는다.
본문·로고·사진은 스타일 설정에 저장하거나 새 발표자료에 복제하지 않는다. 참고 PPT의 마스터 전체를 그대로 재현하는 기능도 아니다.
기존 LLM Adapter의 Ollama/vLLM 계열 연결 경로와 발표용 편집 prompt/schema는 유지한다. 현재 실행 환경은 CPU/mock이며 실제 의미 재작성·이미지 의미 판단 품질은 실모델 연결 후 검증해야 한다.

## 제한 및 다음 개발

- HWP 5.x의 본문/셀 글자는 처리하지만 원본 표 병합·그림·쪽 배치는 아직 복원하지 못한다. HWPX/DOCX 등 파서가 제공한 image node만 자동 보존한다. 암호·DRM·배포용 HWP는 제한된다.
- CPU는 의미 이해 기반 재서술이 아닌 발췌형 편집이다. 모든 문서를 ChatGPT 수준으로 편집한다고 보장하지 않는다. 전문 용어·부정/조건 문장·중요도는 사용자가 근거와 대조할 수 있다.
- 큰 표는 발표용으로 일부 행/열을 발췌한다. 수치/단위 재계산은 하지 않는다. 원문 전체는 근거에서 확인한다.
- 사용자가 한 슬라이드에 구조화 블록(표/차트/이미지)을 여러 개 넣으면 분할을 요구한다. 지나친 텍스트는 QA 실패로 보고하며 성공 산출물로 숨기지 않는다.
- 실제 LLM/VLM, 자료 유형별 정보 설계, 기관 승인 템플릿/로고/폰트, OCR 및 HWP 구조 복원, 더 다양한 디자인 배치, 원본 참고자료의 관리/삭제 UI는 후속 범위다.
- 모델·GPU·운영망·SSO·보존기간·공식 PPT 규격은 기존 TBD/config를 유지한다.

## 무료 테마 출처

[reveal.js](https://github.com/hakimel/reveal.js), 고정 커밋 `807b43097da554de4dba6d020b07f3f110fb766d`.
beige, black-contrast, black, blood, dracula, league, moon, night, serif, simple, sky, solarized, white-contrast, white.
MIT 고지 전문은 `templates/vendor/reveal/LICENSE`. CSS는 색상 참조 자료이며 실행/주입하지 않는다. 원격 폰트도 다운로드/실행하지 않는다.
재배포 권한을 확인할 수 없는 인터넷 PPT 템플릿은 수집하지 않았다.

## 재현 검증

```powershell
.\.venv\Scripts\python.exe infra/scripts/manage.py up
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe infra/scripts/design_smoke.py
.\.venv\Scripts\python.exe infra/scripts/http_e2e.py
```

`design_smoke.py`는 합성 참고 PPTX만 생성하여 업로드, HWP 분석, 학습한 테마 선택, 실제 PPTX 생성과 근거/원본 본문 복사 방지를 확인한다.
브라우저 테스트 `design-library.spec.ts`는 먼저 위 smoke로 합성 참고 파일을 만든 뒤 실행한다.
PowerPoint 실검수: `infra/scripts/powerpoint_smoke.ps1`, 근거 `test-results/design/`.

## DB 업그레이드

API 시작 시 Alembic `39b4465bf603 → a21_theme_scope`가 nullable `templates.org_id`와 인덱스를 추가한다.
기존 템플릿과 프로젝트는 보존되며 22종 기본 디자인을 idempotent seed로 추가한다.
롤백은 새 참고자료를 업로드하기 전 DB/storage 백업과 이전 이미지로 복원한다. 새 scope 컬럼을 삭제하는 downgrade는 조직 경계를 잃을 수 있으므로 데이터 백업 복원 절차를 따른다.
