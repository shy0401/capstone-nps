# 프로토타입 기능 및 개발 로드맵 · v0.2.0

**현재 위치: Docker에서 사용하는 CPU/mock 프로토타입. 실제 AI 모델과 기관 운영 연결은 다음 단계.**

## 현재 사용할 수 있는 기능

| 영역 | 제공 기능 | 범위 |
|---|---|---|
| 실행 | React·FastAPI·PostgreSQL·Redis·5개 Worker·Nginx Compose | 외부 공개는 edge 8080 하나 |
| 로그인/권한 | Local 로그인, 4개 역할, 조직·프로젝트 멤버십, IDOR 차단 | 기관 SSO 미연결 |
| 프로젝트 | 프로젝트 생성/조회/설정 UI, 검토자 추가 | 보안등급·기본 템플릿 설정 가능 |
| 업로드 | 격리→형식 검증→백신→safe parse, 파일 버전/해시 | dev는 mock scan 표시, ClamAV 별도 실검증 |
| 문서 분석 | PDF·DOCX·XLSX·HWPX·HWP 5.x | HWP 본문/셀 문자 추출, 복잡 구조 제한 |
| 근거 추적 | 섹션 기반 chunk, document version·source ref 연결 | HWP 쪽 번호·표/이미지 구조 미복원 |
| 계획 검토 | schema-valid SlidePlan, 자동 표시, 수정·저장 | dev 검토패스 / strict 승인 Gate |
| 작업 관리 | 분리 Worker, 진행률 REST/WS, 취소·재시도·단계 재개 | 실제 GPU 취소 미검증 |
| PPT 기능 | 핵심문장 편집, 어절 줄바꿈, 표지/요점/비교/절차/표/차트/이미지 7배치, 편집 가능한 PPTX | CPU 발췌형; 실제 LLM 요약 연결은 다음 단계 |
| 디자인 참고실 | 기본 22종 + PPTX 다중 업로드·스타일 특징 저장·조직별 선택/재사용 | 모델 가중치 학습·원본 디자인 완전 복제는 아님 |
| 영상 기능 | CPU MP4 renderer, scene 근거, ffprobe/QA | 사용자가 검토 후 요청; 고급 연출 제한 |
| 검토/감사 | 버전별 승인/반려/수정 요청, Artifact 이력, Audit Log | mock/내부 템플릿은 공식 사용 표시 금지 |
| 배포/보안 | hash lock, SBOM/checksum, Docker image bundle, 설치/롤백 문서 | 기관 운영 Release Gate 미완료 |

## 앞으로 개발할 항목

| 우선순위 | 항목 | 완료 판단 기준 |
|---|---|---|
| P1 | HWP 표·그림·페이지 구조 복원 | 병합 셀/도표/근거 위치 Golden 비교 통과 |
| P1 | 실제 LLM 연결 | 승인된 로컬 모델로 요약·구성, schema/retry/timeout 통합 통과 |
| P1 | 실제 ComfyUI 연결 | 검증된 workflow/model/node hash와 ControlNet/IP-Adapter 실행 |
| P1 | PPT/영상 발표 품질 확장 | 기본 배치·PowerPoint 렌더 검증 구현. 의미 기반 스토리텔링·복잡 표/그림·공식 템플릿 검증 확대 |
| P1 | 운영 보안 경계 | parser 전용 격리, 백신 signature 갱신·승인, 로그 전수검사 |
| P2 | 조직/멤버 관리 UI 확장 | 역할·활성/프로젝트 설정은 구현. 조직 트리와 전체 멤버 UI 확장 |
| P2 | 장애/부하 검증 | 실제 worker kill/복구, 동시 요청, VRAM/큐 공정성·SLA 시험 |
| P2 | 완전 오프라인/롤백 | 물리 clean-host에서 bundle 단독 설치 및 이전 승인 릴리스 복구 |
| 기관 확인 | SSO·망·저장/보존·GPU·공식 디자인 | 아래 8개 TBD를 공단 승인 값으로 확정 |

## 남은 기관 TBD

| ID | 확인할 내용 |
|---|---|
| TBD-NPS-NET-001 | IP/VLAN·망 배치·edge·egress·origin |
| TBD-NPS-IAM-001 | SSO 방식과 조직/역할 claim |
| TBD-NPS-GPU-001 | A40×4 배치·모델·workflow·GPU 할당 |
| TBD-NPS-STO-001 | 저장·암호화·백업·보존·삭제 |
| TBD-NPS-SEC-001 | 백신 갱신·TLS·비밀관리·SIEM |
| TBD-NPS-OUT-001 | 공식 PPT·폰트·로고·영상/생성 자산 정책 |
| TBD-NPS-PERF-001 | 문서 규모·동시접속·SLA |
| TBD-NPS-REL-001 | 이미지/모델/custom node 반입과 Release 승인 |

SRS MUST: **PASS 73 / PARTIAL 21 / FAIL 0 / TBD 1**. PARTIAL은 미완료이며 전체 SRS 충족을 선언하지 않습니다.
Requirement별 상세 이유는 `traceability-matrix.md`, 원문과 판정 데이터는 `srs-audit.json`에 있습니다.

현재 dev는 **프로토타입-검토패스**다. 검토자 없이 분석→PPTX/MP4 직접 또는 함께 생성→다운로드한다. `PROTOTYPE_REVIEW_MODE=strict`로 기존 승인 흐름을 복원한다.
