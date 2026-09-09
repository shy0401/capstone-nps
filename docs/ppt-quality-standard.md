# PPT QA

기본 16:9 내부 template, editable title/body/table/chart 객체를 만든다. 원문 image는 contain 배치를 쓴다.
근거와 slide_id 및 모델/프롬프트 provenance를 notes와 artifact metadata에 보존한다.
QA는 ZIP CRC, python-pptx 재열기, slide 수, bounds/safe margin, font-metric 기반 보수적 text fitting,
editable object 수, 표 cell fitting, evidence 존재를 검사한다. 실패 항목은 machine-readable qa_report에 남긴다.

생성기의 기본 QA는 Office render를 NOT_RUN으로 명시한다. 이번 Golden 샘플은 별도로 Microsoft PowerPoint에서 읽기 전용 열기와 PNG export를 실행해 PASS했고, `test-results/powerpoint-smoke.json`에 해당 파일의 SHA256을 남겼다. 폰트 측정 PASS만으로 모든 Office 렌더링 무결성을 증명하지 않는다.
기관 공식 Master/폰트/로고는 TBD-NPS-OUT-001이다. 기본 template은 official_flag=false이며 mock 산출물은 공식 사용 불가다.
