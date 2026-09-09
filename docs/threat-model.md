# 위협 모델

| 경계/공격 | 방어 | 잔여 검증 |
|---|---|---|
| 타 조직 UUID 대입 | 매 resource 접근의 org + membership 검사 | 기관 조직 계층/SSO claim 확인 |
| 파일명 traversal/위장 ZIP | UUID storage + magic/MIME/ZIP 구조 제한 | 악성 실제 corpus 확대 |
| ZIP/XML 폭탄 | 해제 크기/비율/entry 제한 + defusedxml + parser process | Linux 메모리 kill chaos |
| 백신 장애/timeout | DOC_SCAN_UNAVAILABLE, parse 미실행 | ClamAV image와 최신 승인 signature |
| 문서 prompt injection | untrusted data 분리 + no tools + schema/evidence | 실제 모델 adversarial 회귀 |
| 승인 후 데이터 수정 | plan version 재검증 + artifact approval version 결합 | PostgreSQL 동시성 stress |
| Worker 장애/중복 delivery | DB compare-and-set, lease, checkpoint, idempotency | 컨테이너 kill/restart |
| 외부 반출 | internal networks + URL allowlist + no CDN | 실제 no-egress clean-host Gate |
| 공급망 오염 | dependency hash locks, bundle SHA256, model/workflow manifest | image tar/digest + 시스템 패키지 SBOM |

Prototype은 기관 운영 인증·망·보존 정책의 승인이나 보안 적합성 인증이 아니다.
