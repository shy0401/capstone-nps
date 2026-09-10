# 구현·검증 현황 · v0.1.1

원본 SRS/Master/수행계획을 조사하여 모노레포를 구현했다. 원문은 보존했다.
아래는 Phase별 현재 도달 상태이며, 운영 환경 시험을 포함한 전체 Phase 완료 선언은 아니다.

| Phase | 구현 | 현재 검증/잔여 |
|---|---|---|
| 0 | repo·Compose·계약·CI·health | Docker 11개 서비스 기동, edge만 publish |
| 1 | DB/Auth/Org/Project/RBAC/Audit | IDOR·조직/프로젝트 scope 테스트; 상세 관리 UI 확장 필요 |
| 2 | quarantine/검증/scan/storage | 실제 ClamAV clean/EICAR/unavailable PASS; 갱신 승인 TBD |
| 3 | 5개 형식 parse/chunk/evidence | HWP native 본문 분석 PASS; 복잡 표/그림/쪽 구조 부분 지원 |
| 4 | mock/local LLM·schema·Review Gate | 기본 계약 PASS; 실제 모델 연결 필요 |
| 5 | job/outbox/Redis/WS/retry/resume | 회귀 PASS; GPU 장애/부하 미검증 |
| 6 | editable PPT·QA·version | 기존 Golden PASS; 공식 템플릿/품질 고도화 필요 |
| 7 | Comfy adapter·image worker | mock/HTTP 계약; 실제 모델/워크플로 실행 필요 |
| 8 | storyboard·CPU MP4·ffprobe QA | 기존 Golden PASS; 고급 연출/실모델 미완료 |
| 9 | React workspace/review/admin | 단위 3 PASS, HWP 검토자 브라우저 1 PASS |
| 10 | 보안·Golden·E2E | 최신 비미디어 85 PASS, 기존 Docker Golden PASS |
| 11 | SBOM/checksum/images/offline/runbook | 격리 컨테이너 PASS; 물리 clean-host/승인 rollback 남음 |

최신 사용자 지시 이후 PPT/영상 생성은 중단하고 코드·보안·검토 흐름·배포 검증만 진행했다.
현재 MUST 72 PASS / 22 PARTIAL / 1 TBD. 미완료 요구별 사유는 traceability-matrix.md 참조.
실행 결과와 제약은 FINAL_REPORT.md, 사용 가능한 기능/향후 개발은 FEATURES_ROADMAP.md에 정리했다.
