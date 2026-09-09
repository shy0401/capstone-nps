# API 계약

REST: `/api/v1`, progress WS: `/ws/v1/jobs/{job_id}`. Snapshot은 `openapi/openapi.yaml`.
생성 계열은 202 + job를 반환한다. Upload는 document_id, PENDING scan과 job를 반환한다.
`Idempotency-Key`는 동일 사용자·프로젝트 범위에서 요청 payload hash와 결합한다.
동일 키/다른 payload는 409, 동일 키/동일 payload는 기존 job를 반환한다.

WS는 연결 후 첫 JSON frame에 access_token을 받는다. URL query에는 token을 넣지 않는다.
Origin과 token 만료, 사용자 활성 상태, 리소스 권한을 반복 확인한다. REST와 동일 snapshot/seq를 전송한다.
연결 재수립 시 최신 DB 상태를 다시 전송한다.

Error는 stable code와 correlation_id만 노출하고 validation 입력값을 반사하지 않는다.
템플릿 등록도 격리/보안검사 작업을 거친다. 기본 및 등록 template은 기관 검증 전 official_flag=false이다.
