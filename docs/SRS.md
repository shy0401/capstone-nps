





연금술사 소프트웨어 요구사항 명세서(SRS)



    


2026학년도 2학기 산학실전캡스톤3 · 연금술사

연금술사 소프트웨어 요구사항 명세서(SRS)

보안 내재화 기반 내부 문서 지능화 · PPTX/MP4 생성 플랫폼


    

문서 코드

NPS-CAP-SRS-001

버전

v1.0

작성일

2026-09-10

산업체

국민연금공단

지도

김윤경 교수

팀

연금술사

프로젝트

보안 내재화 기반 내부 문서 지능화·발표자료 및 멀티미디어 생성 플랫폼


    
본 문서는 산학협력 문제 제안서와 「연금술사_캡스톤_통합수행계획_2026-2」를 기준선으로 하며, 국민연금공단 실제 망·인증·저장·보존 정책은 담당자 확인 후 TBD를 해소한다.


    


NPS-CAP-SRS-001 · Software Requirements Specification

v1.0 · Baseline



문서 관리





항목

내용





문서명

연금술사 - 소프트웨어 요구사항 명세서(SRS)



문서코드

NPS-CAP-SRS-001



상태

Baseline v1.0 / 산업체 TBD 해소 시 v1.1 이상 개정



작성 근거

산학협력 문제 제안서(source-1/source-2) + 연금술사 캡스톤 통합수행계획 2026-2



범위

보안 내재화 기반 문서 지능화, PPTX/MP4 생성, Web UI, API, Job/Queue, Docker/Offline Release



운영 원칙

국민연금공단 내부망 대상. 학교 개발망은 공개·합성 데이터만 사용.







버전

일자

변경사항

비고





0.1

2026-09-10

SRS 작성 계획 기준선

초안



1.0

2026-09-10

실제 API/데이터/보안/배포/수용 기준 구체화

본 문서





중요:
 본 SRS의 NPS 내부 IP, VLAN, SSO, 저장소, 보존기간, 공식 디자인 규격은 확인되지 않은 사항을 임의 확정하지 않는다. 해당 값은 TBD Register로 관리하고, 프로토타입은 config/adapter로 대체 가능하게 구현한다.



목차




1
 목적 및 범위


2
 배경과 설계 원칙


3
 시스템 컨텍스트


4
 사용자·조직·권한


5
 핵심 업무 흐름


6
 기능 요구사항


7
 데이터 요구사항


8
 API 명세


9
 보안 요구사항


10
 AI/모델/Workflow 요구사항


11
 PPT 공식 품질 기준


12
 영상 공식 품질 기준


13
 비기능 요구사항


14
 Docker/배포 명세


15
 GPU·Queue 정책


16
 시험·수용 기준


17
 추적성


18
 TBD Register


19
 리스크·제약


A
 계약/스키마·Release 구조




1. 목적 및 범위


본 시스템은 국민연금공단 내부 업무 문서를 외부 클라우드로 반출하지 않고 내부 환경에서 분석하여, 구조화된 근거를 유지한 슬라이드 계획과 편집 가능한 PPTX 및 MP4를 생성하고, 사람이 검토·승인한 버전만 공식 사용 가능 상태로 제공하는 내부 업무지원 플랫폼이다.




Security by Design
실제 데이터 외부 반출 금지, 최소권한, 공급망·오프라인 Gate


Evidence First
생성 텍스트와 슬라이드를 원문 Chunk/Table/Image까지 역추적


Official Quality
생성 성공이 아니라 PPT/영상 QA + Reviewer 승인까지 완료



1.1 목표


HWP/HWPX/PDF/DOCX/XLSX의 구조와 표를 공통 데이터 모델로 복원한다.

문맥 단절을 최소화한 Semantic Chunking과 근거 저장소를 구축한다.

LLM을 Adapter로 추상화하여 개발 모델과 공단 내부 대형 모델을 교체 가능하게 한다.

ComfyUI 이미지/영상 Workflow를 버전·해시 기반으로 재현 가능하게 관리한다.

python-pptx 등으로 편집 가능한 PPTX를 생성하고 자동 레이아웃 품질 Gate를 적용한다.

React/FastAPI 기반 UI에서 Job 진행률, 검토, 부분 재생성, 이력을 제공한다.

Docker Compose와 Offline Release Bundle로 공단망 반입·복구 가능성을 증명한다.



1.2 범위 제외


공단 실제 망 토폴로지/IP/VLAN을 학교에서 복제하는 것

운영 전 승인되지 않은 외부 SaaS/Cloud AI 호출

AI 출력물을 사람 검토 없이 자동으로 공식 발표자료로 확정하는 것

미확인 공단 디자인 가이드·보존기간·성능 SLA를 임의로 기관 공식값으로 간주하는 것




2. 배경과 설계 원칙


기준 자료의 핵심은 DEV/APP/AI/DATA/MGMT 분리, 서비스 간 최소 포트, 학교의 공개·합성 데이터 사용, Adapter+Docker+Config, 인터넷 차단 Release Gate, 코드·모델·Workflow·Prompt 추적성이다. 본 SRS는 이 원칙을 구현 가능한 요구사항과 검증 항목으로 승격한다.





원칙

SRS 적용





분리

사용자/서비스/모델/데이터/관리 경로와 Docker network를 분리한다.



최소권한

Role + Organization + Project Membership을 함께 검사한다.



데이터 경계

학교에는 실제 공단 문서·개인정보를 반입하지 않는다.



환경 독립

IP/port/model/storage는 Adapter와 config로 교체한다.



Offline

prod/offline에서 런타임 외부 다운로드 0건을 Release Gate로 검증한다.



추적성

APP/MODEL/WORKFLOW/PROMPT/SCHEMA/TEMPLATE와 Artifact provenance를 기록한다.



Human in the loop

SlidePlan과 최종 Artifact에 검토·승인을 삽입한다.



Contract first

Pydantic/JSON Schema/OpenAPI를 먼저 고정하고 서비스가 같은 계약을 사용한다.






3. 시스템 컨텍스트 및 기준 아키텍처


사용자 브라우저
    │ HTTPS 443 (운영) / 8080 또는 8443 (개발 설정)
    ▼
[edge: Nginx Reverse Proxy]
    ├── /            → React 정적 UI
    ├── /api/v1/*    → api:8000
    └── /ws/v1/*     → api:8000 WebSocket

[api: FastAPI]
    ├── PostgreSQL 16 (data_net)
    ├── Redis 7 (data_net)
    ├── Artifact Storage (volume/internal storage)
    ├── LLM Adapter :8010 (ai_net)
    └── Comfy Adapter :8020 (ai_net)

[workers]
    ├── doc-worker        : security/parse/chunk
    ├── llm-worker        : summary/slide plan
    ├── ppt-worker        : PPTX/QA
    ├── image-worker      : ComfyUI image queue
    └── video-worker      : ComfyUI video + ffmpeg assemble

외부 publish = edge only
LLM / ComfyUI / DB / Redis / worker = internal only


3.1 환경




환경

데이터

네트워크

목적





dev

공개/합성

개발 편의상 제한적 외부 접근 가능

개발·단위/통합 시험



offline

공개/합성 golden set

Internet OFF

반입 가능성, 외부 의존성 0 검증



prod/NPS

실제 내부 업무자료

공단 정책

운영. 실제 값은 TBD를 통해 매핑






4. 사용자·조직·권한 모델


국민연금공단 전체를 단일 서비스 경계로 보고, 하위 OrganizationUnit과 Project Membership으로 데이터 가시성을 제한한다. 이 구조는 본부·지역본부·지사 등 여러 조직 사용자가 동일 플랫폼을 쓰되 서로의 비인가 자료를 열람하지 못하도록 하기 위한 최소 모델이다.




Role

기본 권한

범위





User

프로젝트 생성(정책 허용 시), 문서 업로드, 분석/생성, 자신의 프로젝트 조회

Organization + ProjectMember



Reviewer

User 권한 + SlidePlan/PPT/Video 검토·승인/반려

할당/멤버 프로젝트



OrgAdmin

소속 조직 사용자·프로젝트·감사조회·Queue 모니터링

자신의 Organization subtree



SystemAdmin

시스템 설정·템플릿·전역 운영 관리

시스템 전체. 업무 문서 열람은 별도 정책으로 최소화






5. 핵심 업무 흐름


UPLOAD
  ↓
SECURITY_SCAN / QUARANTINE
  ↓ PASS
PARSE & NORMALIZE
  ↓
SEMANTIC CHUNK + EVIDENCE STORE
  ↓
LLM SUMMARY / SLIDE PLAN
  ↓
SCHEMA + EVIDENCE VALIDATION
  ↓
[1차 사용자/Reviewer 검토·승인]
  ↓
VISUAL PLAN → IMAGE/VIDEO ASSET GENERATION
  ↓
PPTX ASSEMBLY → PPT QUALITY GATE
  ↓
VIDEO STORYBOARD / RENDER → FINAL QUALITY GATE
  ↓
REVIEWER APPROVAL
  ↓
APPROVED ARTIFACT (.pptx / .mp4)



설계 변경:
 기존 계획의 마지막 Review만으로는 GPU 낭비와 오류 전파를 막기 어렵기 때문에 Visual 생성 전에 SlidePlan 승인 Gate를 추가한다. 최종 PPT/영상에는 별도 승인 상태를 둔다.



6. 기능 요구사항

6.1 사용자·인증·조직




ID

우선순위

요구사항

검증/수용 기준

추적 대상






FR-IAM-001



MUST


시스템은 모든 보호 기능에 대해 인증된 사용자만 접근하도록 하며, 비인증 요청은 로그인 또는 401/403 응답으로 차단해야 한다.

비인증 API 호출이 401이고 보호 UI 진입이 차단된다.

/auth, SEC-IAM, TC-IAM




FR-IAM-002



MUST


프로토타입은 Local Identity Provider를 제공하고, 운영 배포는 SSO Adapter(OIDC/SAML/LDAP 중 공단 승인 방식)로 교체 가능해야 한다.

AUTH_PROVIDER 설정 변경만으로 Local/SSO 경계가 분리되고 업무 코드 수정이 없다.

AuthAdapter, DEP-CONFIG




FR-IAM-003



MUST


Local 인증 비밀번호는 Argon2id 등 강한 단방향 해시로 저장하고 평문·복호화 가능한 형태로 저장하지 않아야 한다.

DB 검사에서 평문 비밀번호가 존재하지 않는다.

UserCredential, SEC-SECRET




FR-IAM-004



MUST


사용자는 하나의 OrganizationUnit에 기본 소속되며 여러 Project에 멤버로 참여할 수 있어야 한다.

다른 조직 사용자의 프로젝트를 멤버십 없이 조회할 수 없다.

OrganizationUnit, ProjectMember




FR-IAM-005



MUST


역할은 User, Reviewer, OrgAdmin, SystemAdmin의 최소 4종을 지원해야 한다.

각 역할의 허용·거부 API 자동 테스트가 통과한다.

RBAC policy




FR-IAM-006



MUST


권한 판정은 Role뿐 아니라 OrganizationUnit 및 ProjectMember 범위를 함께 검사해야 한다.

동일 Role이라도 타 조직/비멤버 프로젝트 접근은 403이다.

AuthorizationService




FR-IAM-007



SHOULD


관리자는 사용자의 활성/비활성 상태와 역할을 변경할 수 있고 변경 이력은 AuditEvent에 기록되어야 한다.

역할 변경 전후값·수행자·시간이 감사로그에 남는다.

/admin/users, AuditEvent




6.2 프로젝트·문서 반입




ID

우선순위

요구사항

검증/수용 기준

추적 대상






FR-PRJ-001



MUST


사용자는 프로젝트를 생성하고 프로젝트명, 설명, 조직, 보안등급, 기본 PPT 템플릿을 지정할 수 있어야 한다.

프로젝트 생성·조회·수정 API와 UI가 동작한다.

/projects, Project




FR-PRJ-002



MUST


프로젝트는 멤버와 역할을 관리하고 프로젝트 밖 사용자에게 문서 및 산출물을 노출하지 않아야 한다.

비멤버가 document/artifact URL을 직접 호출해도 403이다.

ProjectMember, SEC-DATA




FR-DOC-001



MUST


시스템은 .hwp, .hwpx, .pdf, .docx, .xlsx 입력을 MVP 정식 지원 형식으로 식별해야 한다.

5개 형식의 샘플 업로드 및 형식 판별 테스트가 통과한다.

DocumentParserRegistry




FR-DOC-002



MUST


업로드 시 확장자, MIME, magic/컨테이너 구조를 교차 검증하여 위장 파일을 거부해야 한다.

확장자만 바꾼 실행파일·ZIP이 거부된다.

UploadGuard, SEC-FILE




FR-DOC-003



MUST


업로드 파일은 SHA-256을 계산하고 동일 프로젝트 내 중복 업로드를 탐지해야 한다.

동일 바이트 업로드 시 중복 여부를 반환한다.

DocumentVersion.sha256




FR-DOC-004



MUST


업로드 직후 파일은 quarantine 상태이며 보안검사 성공 전 파서·LLM·ComfyUI로 전달되지 않아야 한다.

감염/검사실패 파일이 PARSE 단계에 진입하지 않는다.

QuarantineService




FR-DOC-005



MUST


시스템은 파일 크기·페이지/시트·압축 해제 크기 제한을 설정값으로 적용하여 zip bomb 및 자원 고갈을 방어해야 한다.

제한 초과 샘플이 명확한 오류코드로 거부된다.

UploadPolicy




FR-DOC-006



MUST


문서 원본은 immutable DocumentVersion으로 저장하고 교체 시 새 버전을 생성해야 한다.

v1을 교체해도 원본과 해시가 보존되고 v2가 추가된다.

DocumentVersion




FR-DOC-007



SHOULD


사용자는 업로드 문서의 제목, 분류, 보안등급, 태그를 수정할 수 있어야 한다.

메타데이터 변경이 본문 원본 해시를 변경하지 않는다.

DocumentMetadata




6.3 문서 지능화·Chunk·근거




ID

우선순위

요구사항

검증/수용 기준

추적 대상






FR-PARSE-001



MUST


파서는 입력 문서를 공통 NormalizedDocument 모델로 변환해야 한다.

각 형식이 동일 계약의 JSON Schema를 통과한다.

contracts/document.schema.json




FR-PARSE-002



MUST


NormalizedDocument는 section, heading, paragraph, table, image, source_location을 보존해야 한다.

golden 문서의 요소 순서와 source_location이 비교된다.

ParseResult




FR-PARSE-003



MUST


표는 최소 행·열·셀 텍스트·헤더 여부·병합정보·원본 위치를 표현할 수 있어야 한다.

golden 표의 구조 비교 테스트가 통과한다.

TableNode




FR-PARSE-004



MUST


파서는 암호화·손상·미지원 구조를 임의 추정하지 않고 명시적 상태와 오류코드를 반환해야 한다.

암호화 PDF/HWP가 성공으로 오인되지 않는다.

ParseError




FR-PARSE-005



MUST


파싱 작업에는 timeout과 메모리/페이지 제한을 적용하고 실패가 전체 API 프로세스를 중단시키지 않아야 한다.

악성/대형 문서에서 worker만 실패하고 API health는 정상이다.

DocWorker




FR-CHUNK-001



MUST


Semantic Chunk는 섹션 경계를 우선 보존하고 토큰 제한을 보조 조건으로 사용해야 한다.

heading과 표가 임의로 중간 절단되지 않는 golden test가 통과한다.

Chunker




FR-CHUNK-002



MUST


Chunk는 chunk_id, document_id, section_id, text, token_count, source_location, prev/next id, security_class를 포함해야 한다.

chunk.schema 검증이 통과한다.

Chunk




FR-CHUNK-003



MUST


표·이미지 참조가 포함된 Chunk는 table_refs/image_refs를 보존해야 한다.

슬라이드 근거에서 표/이미지 원본을 역추적할 수 있다.

EvidenceStore




FR-EVD-001



MUST


LLM이 생성한 사실성 텍스트 블록은 최소 하나 이상의 source_ref를 가져야 한다.

source_ref 없는 factual block은 validation에서 실패한다.

EvidenceValidator




FR-EVD-002



MUST


source_ref는 document_version, page/section, chunk_id 또는 table/image node id를 포함해야 한다.

UI에서 근거 열기를 누르면 원문 위치 정보를 표시한다.

SourceRef




FR-EVD-003



SHOULD


Reviewer는 각 슬라이드 요소에서 근거 문서·Chunk를 확인할 수 있어야 한다.

Review 화면에서 source panel이 열린다.

Review UI




6.4 LLM 오케스트레이션




ID

우선순위

요구사항

검증/수용 기준

추적 대상






FR-LLM-001



MUST


업무 코드는 LLM 엔진을 직접 호출하지 않고 LLM Adapter 인터페이스를 통해 호출해야 한다.

mock/ollama/openai-compatible local adapter 교체 테스트가 통과한다.

services/llm-adapter




FR-LLM-002



MUST


LLM 출력은 자유 텍스트가 아닌 버전된 JSON Schema로 수신·검증해야 한다.

Schema 불일치 응답은 retry/failed로 처리되고 저장되지 않는다.

slide-plan.schema.json




FR-LLM-003



MUST


LLM은 문서 요약, 핵심 메시지, 슬라이드 개요, 슬라이드별 콘텐츠, 시각 자산 계획을 분리된 단계로 생성해야 한다.

각 단계별 JobStep과 결과 JSON이 존재한다.

JobStep, SlidePlan




FR-LLM-004



MUST


프롬프트는 PromptPack으로 버전 관리되고 생성 결과에 prompt_pack_version과 prompt_hash가 기록되어야 한다.

Artifact provenance에서 사용한 prompt 버전을 확인할 수 있다.

PromptPack




FR-LLM-005



MUST


문서 내용은 시스템 지시와 분리된 untrusted data로 처리하며 문서 내 prompt injection 문구가 시스템 정책을 변경할 수 없어야 한다.

injection golden document에서 금지 동작이 발생하지 않는다.

SEC-LLM




FR-LLM-006



MUST


SlidePlan 생성 후 schema/evidence/length validation을 통과해야 Visual 단계로 진행할 수 있다.

검증 실패 시 WAITING_REVIEW 또는 FAILED이고 GPU 작업이 시작되지 않는다.

SlidePlanValidator




FR-LLM-007



MUST


사용자는 Visual 생성 전 SlidePlan을 검토·수정·승인할 수 있어야 한다.

승인되지 않은 plan으로 image/video job을 시작하면 409이다.

Review/Approval




FR-LLM-008



SHOULD


LLM 요청은 token/timeout/retry 상한을 설정하고 무한 재시도를 금지해야 한다.

오류 주입 테스트에서 지정 횟수 후 종료한다.

LLMPolicy




FR-LLM-009



SHOULD


응답에는 모델 식별자, model revision/hash, context/prompt version 및 수행시간을 남겨야 한다.

GenerationRun 메타데이터가 채워진다.

ModelManifest




6.5 시각 자산·ComfyUI




ID

우선순위

요구사항

검증/수용 기준

추적 대상






FR-VIS-001



MUST


FastAPI/Frontend는 ComfyUI를 직접 호출하지 않고 Comfy Adapter와 Job Queue를 통해서만 작업을 요청해야 한다.

Browser/network 테스트에서 8188 계열 포트가 외부 노출되지 않는다.

ComfyAdapter, SEC-NET




FR-VIS-002



MUST


이미지 생성은 workflow JSON, prompt, seed, 모델/노드 버전을 기록해야 한다.

동일 고정 seed/workflow로 재현 메타데이터가 남는다.

WorkflowManifest




FR-VIS-003



MUST


ControlNet(Canny/Depth) 및 IP-Adapter 사용 여부를 VisualPlan 속성으로 명시할 수 있어야 한다.

VisualPlan schema가 옵션을 표현하고 worker가 분기한다.

visual-plan.schema.json




FR-VIS-004



MUST


문서 도표/차트 형태를 유지해야 하는 시각화는 생성형 이미지로 임의 재구성하지 않고 구조 보존 경로를 우선해야 한다.

chart/table preserve 플래그 시 원본 구조/벡터 경로가 선택된다.

VisualPolicy




FR-VIS-005



MUST


ComfyUI 실패는 해당 JobStep만 실패시키며 retry 정책에 따라 재실행할 수 있어야 한다.

worker 강제 종료 후 재시작·retry가 가능하다.

ComfyWorker




FR-VIS-006



MUST


Image/Video worker는 GPU 예약 정보를 받아 자신에게 할당된 device만 사용해야 한다.

NVIDIA_VISIBLE_DEVICES 및 worker config가 적용된다.

GPU Scheduler




FR-VIS-007



SHOULD


생성 자산은 프로젝트/슬라이드/버전과 연결되고 Reviewer가 교체 또는 재생성할 수 있어야 한다.

asset version history가 보존된다.

VisualAsset




FR-VIS-008



SHOULD


개발환경에서 GPU/ComfyUI가 없어도 mock adapter로 end-to-end 프로토타입을 실행할 수 있어야 한다.

CPU CI에서 golden e2e가 통과한다.

MockComfyAdapter




6.6 PPTX 생성 및 품질




ID

우선순위

요구사항

검증/수용 기준

추적 대상






FR-PPT-001



MUST


시스템은 승인된 SlidePlan으로부터 편집 가능한 .pptx를 생성해야 한다.

PowerPoint/LibreOffice에서 repair 경고 없이 열리고 텍스트가 편집 가능하다.

PptRenderer




FR-PPT-002



MUST


PPT는 선택된 Master/Template 규칙을 우선 적용하고 템플릿 미제공 시 내부 기본 템플릿을 사용하되 공식 템플릿으로 표시하지 않아야 한다.

Template ID가 Artifact에 기록되고 기본 템플릿은 clearly internal로 표기된다.

TemplateService




FR-PPT-003



MUST


텍스트는 슬라이드 경계를 벗어나지 않아야 하며 overflow 검사에서 실패한 슬라이드는 자동 축약/재레이아웃 또는 검토대기로 전환해야 한다.

overflow golden case가 0 overflow 또는 review 상태가 된다.

PptQualityGate




FR-PPT-004



MUST


이미지·도형은 slide bounds와 safe margin을 위반하지 않아야 한다.

clipping/out-of-bounds 검사 0건이다.

PptQualityGate




FR-PPT-005



MUST


표는 가능한 경우 편집 가능한 PowerPoint table로 생성하고 단순 스크린샷으로 대체하지 않아야 한다.

table golden slide에서 cell 편집이 가능하다.

TableRenderer




FR-PPT-006



MUST


그래프는 구조화 데이터가 존재할 경우 차트 또는 편집 가능한 벡터/도형을 우선하며, 근거 데이터를 연결해야 한다.

chart provenance가 source table을 참조한다.

ChartRenderer




FR-PPT-007



MUST


각 슬라이드는 slide_id와 source_refs를 Artifact metadata에 보존해야 한다.

slide-level trace 화면에서 근거가 조회된다.

ArtifactSlideMap




FR-PPT-008



MUST


사용자는 슬라이드 텍스트·이미지를 인라인 수정하고 선택 슬라이드만 재생성할 수 있어야 한다.

전체 deck 재생성 없이 1개 slide version이 증가한다.

PartialRegeneration




FR-PPT-009



MUST


PPT 파일은 DRAFT/REVIEWED/APPROVED 상태를 가지며 APPROVED만 공식 사용 가능 상태로 표시해야 한다.

DRAFT 다운로드에는 비공식 상태가 표시되고 승인 후 상태가 변경된다.

ApprovalState




FR-PPT-010



SHOULD


제목·본문·캡션·표의 최소 글자 크기와 safe margin은 TemplatePolicy로 설정 가능해야 한다.

템플릿 정책 변경이 code 변경 없이 반영된다.

TemplatePolicy




FR-PPT-011



SHOULD


동일 Template/PromptPack/SlidePlan으로 재생성할 때 구조적 일관성이 유지되어야 한다.

golden deck 회귀검사에서 레이아웃 규칙 위반이 없다.

PPT Regression




FR-PPT-012



MUST


PPT 품질 Gate 결과를 machine-readable JSON으로 저장해야 한다.

artifact별 qa_report.json이 생성된다.

QaReport




6.7 영상 생성 및 품질




ID

우선순위

요구사항

검증/수용 기준

추적 대상






FR-VID-001



MUST


영상은 승인된 SlidePlan 및 승인/검토된 PPT 콘텐츠와 동일한 메시지 구조에서 Storyboard를 생성해야 한다.

PPT와 영상 storyboard의 slide/scene mapping이 존재한다.

Storyboard




FR-VID-002



MUST


영상의 scene별 source_slide_id 및 source_refs를 보존해야 한다.

scene provenance 조회가 가능하다.

VideoScene




FR-VID-003



MUST


영상 자산 생성은 ComfyUI Video workflow 또는 대체 renderer adapter를 통해 Job Queue에서 수행해야 한다.

video worker가 독립 queue로 실행된다.

VideoWorker




FR-VID-004



MUST


프로토타입 기본 출력은 16:9, 1920x1080, H.264 MP4로 생성하되 기관 최종 규격은 configuration으로 변경 가능해야 한다.

ffprobe 결과가 기본 규격과 일치하고 설정 변경이 반영된다.

VideoProfile




FR-VID-005



MUST


영상 생성 실패는 PPT artifact를 무효화하지 않으며 VIDEO 단계에서 재시작할 수 있어야 한다.

video step retry가 parse/LLM/PPT를 재실행하지 않는다.

Job Resume




FR-VID-006



MUST


영상은 DRAFT/REVIEWED/APPROVED 상태를 가지며 Reviewer 승인 전 공식 결과로 표시되지 않아야 한다.

미승인 영상의 official flag=false이다.

ApprovalState




FR-VID-007



SHOULD


자막·로고·인트로/아웃트로·장면 길이는 VideoProfile로 관리해야 한다.

profile JSON 수정만으로 렌더링 설정이 바뀐다.

VideoProfile




FR-VID-008



SHOULD


동일 Storyboard에서 특정 scene만 재생성 가능해야 한다.

scene version만 증가하고 전체 영상 assemble만 다시 수행된다.

PartialRegeneration




6.8 Job·Queue·진행률




ID

우선순위

요구사항

검증/수용 기준

추적 대상






FR-JOB-001



MUST


모든 장기 작업은 비동기 GenerationJob으로 생성되어 HTTP 요청 수명과 분리되어야 한다.

업로드 후 202 + job_id 반환, API timeout 없이 작업이 지속된다.

/jobs, Celery/Redis




FR-JOB-002



MUST


Job 상태는 QUEUED, RUNNING, WAITING_REVIEW, SUCCEEDED, FAILED, CANCELLED, RETRYING을 지원해야 한다.

상태 전이 테스트가 허용 transition만 통과한다.

JobStateMachine




FR-JOB-003



MUST


JobStep은 SECURITY_SCAN, PARSE, CHUNK, LLM, PLAN_VALIDATE, IMAGE, PPT, PPT_QA, VIDEO, FINAL_QA를 최소 지원해야 한다.

단일 job의 step 이력이 순서대로 기록된다.

JobStep




FR-JOB-004



MUST


사용자는 job 진행률, 현재 단계, 대기 순서 또는 실행 상태, 실패 원인을 조회할 수 있어야 한다.

REST 조회와 WebSocket event가 일치한다.

/jobs/{id}, /ws/v1/jobs/{id}




FR-JOB-005



MUST


취소 가능한 단계에서 사용자가 job을 취소할 수 있어야 하며 취소가 GPU worker에 전달되어야 한다.

long mock task cancel 후 CANCELLED이고 후속 step이 시작되지 않는다.

CancelToken




FR-JOB-006



MUST


재시도는 step 단위로 수행하며 이미 승인된 이전 단계 결과를 재사용해야 한다.

VIDEO 실패 후 resume_from=VIDEO 시 parse/LLM count가 증가하지 않는다.

RetryPolicy




FR-JOB-007



MUST


Queue Manager는 job type, 우선순위, worker heartbeat, GPU capability를 기준으로 worker를 선택해야 한다.

worker down 상태에서 해당 worker에 신규 할당이 없다.

Scheduler




FR-JOB-008



SHOULD


OrgAdmin/SystemAdmin은 큐 대기량과 worker heartbeat를 조회할 수 있어야 한다.

admin dashboard/API에서 queue metrics가 보인다.

/admin/queues




6.9 검토·승인·산출물 이력




ID

우선순위

요구사항

검증/수용 기준

추적 대상






FR-REV-001



MUST


Reviewer는 SlidePlan, PPTX, MP4 각각에 대해 approve/reject/request-change를 수행할 수 있어야 한다.

승인 이벤트와 코멘트가 AuditEvent/Review에 저장된다.

/reviews




FR-REV-002



MUST


승인은 특정 ArtifactVersion에 결합되어야 하며 수정 시 기존 승인을 자동 승계하지 않아야 한다.

승인 v2 후 수정된 v3는 다시 DRAFT이다.

ArtifactVersion




FR-REV-003



MUST


공식 사용 가능 표시는 최신 ArtifactVersion이 APPROVED이고 모든 필수 QA Gate가 PASS일 때만 true여야 한다.

QA fail artifact를 승인 API가 차단한다.

OfficialEligibility




FR-ART-001



MUST


모든 생성 산출물은 Artifact와 ArtifactVersion으로 관리하고 파일 해시, 크기, 생성시간, 생성자/Job, provenance를 저장해야 한다.

DB와 파일 해시가 일치한다.

ArtifactVersion




FR-ART-002



MUST


사용자는 권한 범위 내에서 과거 버전을 조회·다운로드할 수 있어야 한다.

v1/v2 파일을 각각 재다운로드한다.

/artifacts




FR-ART-003



MUST


원본 문서·중간 JSON·PPTX·MP4·QA report는 별도 storage namespace를 사용해야 한다.

경로 정책 테스트가 통과한다.

StorageLayout




FR-ART-004



MUST


Artifact 다운로드는 API의 권한 확인 후 스트리밍/서명된 내부 경로 방식으로 제공하고 storage 경로를 직접 공개하지 않아야 한다.

직접 storage path 접근이 불가하다.

DownloadService




FR-ART-005



SHOULD


보존/삭제 정책은 organization/project/security_class별 configuration을 지원해야 한다.

retention job이 정책을 적용하고 AuditEvent를 남긴다.

RetentionPolicy






7. 데이터 요구사항




Entity

의미

주요 필드





User

사용자

id, username, display_name, email, org_id, status, created_at



OrganizationUnit

공단 조직 단위

id, parent_id, code, name, path, active



Project

업무 프로젝트

id, org_id, name, security_class, template_id, owner_id



ProjectMember

프로젝트 권한

project_id, user_id, role



Document

논리 문서

id, project_id, title, current_version_id, classification



DocumentVersion

원본 버전

id, document_id, sha256, mime, size, storage_key, scan_status



ParseResult

정규화 결과

id, document_version_id, schema_version, json_storage_key, status



Chunk

시맨틱 청크

id, parse_result_id, section_id, text, token_count, source_location, prev/next



SlidePlan

슬라이드 계획

id, document_id, version, status, prompt_pack, model_run_id



Slide

개별 슬라이드

id, plan_id, order, layout_type, title, content_blocks, source_refs



VisualAsset

이미지/영상 자산

id, slide_id, type, version, workflow, seed, storage_key, provenance



GenerationJob

비동기 작업

id, project_id, type, state, progress, priority, requested_by



JobStep

작업 단계

id, job_id, step_type, state, retry_count, worker_id, started/ended



Artifact

논리 산출물

id, project_id, type(PPTX/MP4), current_version_id



ArtifactVersion

파일 버전

id, artifact_id, version, sha256, qa_status, approval_status, storage_key



Review

검토

id, artifact_version_id/plan_id, reviewer_id, decision, comment



Approval

승인

id, target_type, target_version_id, approver_id, approved_at



Template

PPT/Video 템플릿

id, type, name, version, config, storage_key, official_flag



PromptPack

프롬프트 묶음

id, name, version, sha256, storage_key



ModelManifest

모델 정보

id, engine, model_name, revision, quantization, hash, license



WorkflowManifest

Comfy workflow

id, type, version, sha256, node_lock_version



ReleaseManifest

릴리스 조합

release_version, git_sha, image_digests, model/workflow/prompt/schema versions



AuditEvent

감사 이벤트

id, actor_id, org/project, action, target, result, correlation_id, ts




7.1 저장 경로 원칙

storage/
  originals/{project_id}/{document_id}/{version_id}/source.bin
  parsed/{document_id}/{version_id}/normalized.json
  chunks/{document_id}/{version_id}/chunks.jsonl
  visuals/{project_id}/{slide_id}/{asset_id}/{version}/...
  artifacts/{project_id}/{artifact_id}/{version}/output.pptx|output.mp4
  qa/{artifact_id}/{version}/qa_report.json

* 실제 파일명은 사용자 입력값이 아니라 UUID/서버 생성키 사용
* 사용자 원래 파일명은 DB metadata로만 보존


7.2 핵심 상태

DocumentScanStatus = PENDING | CLEAN | INFECTED | ERROR
ParseStatus        = PENDING | RUNNING | SUCCEEDED | FAILED
PlanStatus         = DRAFT | VALIDATED | REVIEWED | APPROVED | REJECTED
ArtifactStatus     = DRAFT | REVIEWED | APPROVED | ARCHIVED
QaStatus           = NOT_RUN | PASS | FAIL | WARN
JobState           = QUEUED | RUNNING | WAITING_REVIEW | SUCCEEDED | FAILED | CANCELLED | RETRYING



8. API 명세

Prototype의 계약은 OpenAPI 3.1을 기준으로 고정한다. 운영에서 실제 URL/포트는 Reverse Proxy 설정으로 재매핑하되 path contract는 유지한다.




Method

Path

권한

기능

주요 계약





POST

/api/v1/auth/login

Public

Local 계정 로그인

LoginRequest → TokenPair/refresh cookie



POST

/api/v1/auth/refresh

Public(cookie)

Access token 갱신

Refresh cookie → AccessToken



POST

/api/v1/auth/logout

Auth

Refresh revoke

204



GET

/api/v1/me

Auth

현재 사용자·조직·역할

MeResponse



GET

/api/v1/organizations

SystemAdmin/OrgAdmin

접근 가능한 조직 목록

Organization[]



POST

/api/v1/projects

User+

프로젝트 생성

ProjectCreate → Project



GET

/api/v1/projects

Auth

내 프로젝트 목록

ProjectPage



GET

/api/v1/projects/{project_id}

Member

프로젝트 상세

ProjectDetail



PATCH

/api/v1/projects/{project_id}

ProjectOwner/OrgAdmin

프로젝트 수정

ProjectUpdate



POST

/api/v1/projects/{project_id}/members

Owner/Admin

프로젝트 멤버 추가

ProjectMemberCreate



DELETE

/api/v1/projects/{project_id}/members/{user_id}

Owner/Admin

멤버 제거

204



POST

/api/v1/projects/{project_id}/documents

Member

문서 업로드(multipart)

DocumentUploadResponse + security job



GET

/api/v1/documents/{document_id}

Member

문서 메타/버전/상태

DocumentDetail



GET

/api/v1/documents/{document_id}/versions

Member

문서 버전 목록

DocumentVersion[]



POST

/api/v1/documents/{document_id}/analyze

Member

Parse/Chunk/LLM 분석 Job 생성

202 Job



GET

/api/v1/documents/{document_id}/parse-result

Member

정규화 문서 조회

NormalizedDocument



GET

/api/v1/documents/{document_id}/chunks

Member

Chunk 목록

ChunkPage



POST

/api/v1/documents/{document_id}/slide-plans

Member

SlidePlan 생성 Job

202 Job



GET

/api/v1/slide-plans/{plan_id}

Member

SlidePlan 조회

SlidePlan



PATCH

/api/v1/slide-plans/{plan_id}

Reviewer/Owner

Plan 수정

SlidePlan



POST

/api/v1/slide-plans/{plan_id}/validate

Member

Schema/Evidence 검증

ValidationReport



POST

/api/v1/slide-plans/{plan_id}/approve

Reviewer

Visual 생성 전 승인

Approval



POST

/api/v1/slide-plans/{plan_id}/generate-ppt

Member

PPT 생성 Job

202 Job



POST

/api/v1/slide-plans/{plan_id}/generate-video

Member

Video 생성 Job

202 Job



GET

/api/v1/jobs/{job_id}

Member

Job/Step 상태

JobDetail



POST

/api/v1/jobs/{job_id}/cancel

Member

Job 취소

JobDetail



POST

/api/v1/jobs/{job_id}/retry

Member

실패 step 재시도

202 Job



GET

/api/v1/artifacts/{artifact_id}

Member

산출물/버전/QA/provenance

ArtifactDetail



GET

/api/v1/artifacts/{artifact_id}/download

Member

권한검증 후 파일 다운로드

binary stream



POST

/api/v1/artifacts/{artifact_id}/reviews

Reviewer

검토 등록

Review



POST

/api/v1/artifacts/{artifact_id}/approve

Reviewer

ArtifactVersion 승인

Approval



POST

/api/v1/artifacts/{artifact_id}/regenerate

Member

선택 slide/scene 재생성

202 Job



GET

/api/v1/templates

Auth

사용 가능 PPT/Video template

Template[]



POST

/api/v1/admin/templates

SystemAdmin

템플릿 등록

Template



GET

/api/v1/admin/queues

OrgAdmin/SystemAdmin

Queue/Worker 상태

QueueStatus



GET

/api/v1/admin/audit

OrgAdmin/SystemAdmin

범위 내 감사로그 검색

AuditPage



GET

/api/v1/health/live

Public/internal

Liveness

Health



GET

/api/v1/health/ready

Internal

Readiness dependencies

Health



WS

/ws/v1/jobs/{job_id}

Member

실시간 Job 진행 이벤트

JobEvent stream




8.1 공통 응답/오류

ErrorResponse {
  error: {
    code: string,          // e.g. DOC_UNSUPPORTED, AUTH_FORBIDDEN, QA_FAILED
    message: string,       // 사용자 표시용. 민감 내부정보 제외
    correlation_id: UUID,
    details?: object       // 개발/권한 범위에서만 안전한 세부정보
  }
}

Idempotency-Key: UUID  // POST generation 계열 지원
X-Correlation-ID: UUID // 없으면 edge/api가 생성


8.2 Job WebSocket Event

{
  "job_id": "uuid",
  "state": "RUNNING",
  "step": "PPT_QA",
  "progress": 78,
  "message": "PPT 품질 검증 중",
  "ts": "ISO-8601",
  "seq": 41
}



9. 보안 요구사항




ID

우선순위

요구사항

검증/수용 기준

추적 대상






SEC-IAM-001



MUST


모든 API는 명시적으로 public 또는 authenticated로 분류하고 default deny를 적용한다.

OpenAPI security review에서 미분류 protected endpoint가 0건이다.

API Gateway




SEC-IAM-002



MUST


Local refresh token은 HttpOnly, Secure(HTTPS), SameSite=Strict 쿠키로 전달하고 server-side revoke가 가능해야 한다.

로그아웃 후 refresh가 거부된다.

AuthService




SEC-IAM-003



MUST


IDOR 방지를 위해 object id만으로 권한을 신뢰하지 않고 resource scope를 매 요청 검증한다.

타 프로젝트 UUID 대입 공격이 403이다.

AuthorizationService




SEC-NET-001



MUST


외부 publish는 edge/reverse proxy만 허용하고 API/DB/Redis/LLM/ComfyUI는 Docker 내부 network에서만 노출한다.

docker inspect에서 외부 published port가 edge 외 0건이다.

compose.prod.yml




SEC-NET-002



MUST


prod/offline profile은 AI/DATA network에서 인터넷 egress를 허용하지 않는 배치 정책을 지원해야 한다.

offline test에서 외부 HTTP/DNS 의존성이 0건이다.

offline gate




SEC-NET-003



MUST


CORS는 명시된 내부 origin allowlist만 허용해야 한다.

임의 Origin preflight가 거부된다.

Nginx/FastAPI




SEC-DATA-001



MUST


학교 개발환경에는 실제 가입자·내부업무 데이터를 반입하지 않는다.

개발 data manifest가 공개/합성 샘플만 포함한다.

Data Boundary




SEC-DATA-002



MUST


원본·중간물·산출물 파일명으로 사용자 입력 경로를 직접 사용하지 않고 서버가 생성한 ID 기반 경로를 사용한다.

path traversal filename test가 안전하다.

StorageService




SEC-DATA-003



MUST


민감 본문, 개인정보, 토큰, 비밀번호, Secret을 application log에 기록하지 않는다.

log scanner test에서 금지 패턴이 0건이다.

LoggingPolicy




SEC-FILE-001



MUST


업로드 파일은 quarantine에서 악성코드 스캔을 수행하고 scan 실패/timeout은 fail-closed로 처리한다.

EICAR 테스트가 차단되고 scan unavailable 시 parse가 시작되지 않는다.

ClamAV Adapter




SEC-FILE-002



MUST


ZIP 기반 형식(docx/xlsx/hwpx)은 압축 해제 비율·파일 수·총 크기 제한을 적용한다.

zip bomb 샘플이 제한으로 중단된다.

ArchiveGuard




SEC-FILE-003



MUST


파서는 외부 URL/embedded object를 자동 실행·다운로드하지 않는다.

외부 링크 포함 문서에서 네트워크 호출 0건이다.

Safe Parser




SEC-LLM-001



MUST


System prompt와 document content를 구조적으로 분리하고 문서 내 instruction을 정책 지시로 승격하지 않는다.

prompt injection golden test 통과.

LLM Adapter




SEC-LLM-002



MUST


LLM 출력은 schema validation, allowlisted field 검증, 길이 제한을 통과해야 persistence/render에 사용한다.

악성 JSON/HTML/script 문자열이 UI에서 실행되지 않는다.

OutputValidator




SEC-SECRET-001



MUST


.env, API key, password, private certificate는 Git에 커밋하지 않고 secret file/environment injection으로 주입한다.

secret scan CI 통과.

CI




SEC-AUDIT-001



MUST


로그인, 업로드, 생성, 다운로드, 수정, 승인, 삭제, 권한변경을 AuditEvent로 기록한다.

각 행위에 대한 감사 이벤트 integration test 통과.

AuditService




SEC-AUDIT-002



MUST


AuditEvent는 actor, org/project, action, target, timestamp, result, correlation_id를 포함한다.

필수필드 null이 0건이다.

AuditEvent




SEC-SUPPLY-001



MUST


Release bundle은 Docker image digest, 모델/Workflow/Prompt hash, SBOM, checksums를 포함한다.

bundle validator PASS.

release-manifest.yaml




SEC-SUPPLY-002



MUST


latest tag와 무버전 custom node 설치를 금지하고 dependency lock을 유지한다.

CI 정책 검사에서 unpinned dependency가 실패한다.

locks




SEC-OFFLINE-001



MUST


clean host에서 release bundle만으로 설치 가능해야 하고 runtime 외부 다운로드가 없어야 한다.

인터넷 차단 설치 및 golden e2e PASS.

Offline Gate




SEC-OFFLINE-002



MUST


rollback은 이전 release bundle을 기준으로 단일 runbook 절차로 수행 가능해야 한다.

RC에서 이전 version으로 rollback smoke test PASS.

INSTALL_ROLLBACK.md




9.1 보안 파일 처리 흐름

Upload → extension/MIME/magic validation → size/archive guard → SHA-256
      → quarantine → malware scan → CLEAN only → Safe Parser

FAIL / TIMEOUT / UNKNOWN = fail-closed (parse 금지)


9.2 감사 로그 최소 이벤트

LOGIN_SUCCESS/FAIL, LOGOUT, USER_ROLE_CHANGE, PROJECT_CREATE/UPDATE, DOCUMENT_UPLOAD/DOWNLOAD/DELETE, JOB_CREATE/CANCEL/RETRY, PLAN_UPDATE/APPROVE, ARTIFACT_DOWNLOAD, REVIEW, APPROVE, TEMPLATE_CHANGE, RELEASE_IMPORT를 기록한다.



10. AI·모델·Workflow 요구사항


10.1 LLM Adapter

Adapter는 최소 
mock
, 
ollama
, 
openai_compatible_local
 모드를 지원하도록 설계한다. 운영에서는 공단 승인 내부 serving API를 동일 인터페이스로 연결한다. 외부 클라우드 URL을 기본값으로 두지 않는다.


class LLMAdapter(Protocol):
    async def generate_structured(
        task: str,
        input_payload: dict,
        output_schema: dict,
        prompt_pack: str,
        policy: GenerationPolicy,
    ) -> StructuredGenerationResult: ...


10.2 Comfy Adapter

Workflow JSON은 repo의 
workflows/comfy/
에서 버전 관리하고, release에 SHA-256과 custom node lock을 포함한다. Browser는 ComfyUI에 직접 접근하지 않는다.


10.3 Provenance

provenance = {
  app_version, git_sha,
  model_manifest_id, model_hash,
  prompt_pack_version, prompt_hash,
  workflow_version, workflow_hash,
  schema_version, template_version,
  document_version_ids,
  source_refs,
  generated_by_job_id,
  generated_at
}



11. PPT 공식 사용 품질 기준


“PPT가 생성된다”는 수용 기준이 아니다. 공식 사용 가능 상태는 편집 가능성, 레이아웃 무결성, 근거 추적성, 템플릿 준수, 검토·승인을 모두 통과해야 한다.




Gate

검사

PASS 기준





PPT-STRUCT

파일 무결성

PowerPoint/LibreOffice가 repair 요청 없이 열림



PPT-EDIT

편집 가능성

제목/본문/표가 편집 가능한 객체. 전체 슬라이드 이미지화 금지



PPT-BOUND

경계

slide bounds 밖 객체 0건



PPT-TEXT

텍스트

overflow 0건. 자동 조정 실패 시 QA FAIL/Review



PPT-IMAGE

이미지

clipping/비정상 aspect 왜곡 0건 또는 명시적 crop policy



PPT-TABLE

표

구조 데이터 존재 시 edit 가능한 table 우선



PPT-THEME

템플릿

TemplatePolicy의 master/layout/font/color/logo rule 위반 0건



PPT-EVID

근거

사실성 content block에 source_ref 존재



PPT-PROV

재현성

template/model/prompt/workflow/schema/app version 기록



PPT-APPROVAL

공식 사용

QA PASS + Reviewer APPROVED





공식 디자인 주의:
 Prototype 기본 템플릿은 내부 개발용이다. 국민연금공단 공식 Master/폰트/로고 가이드가 제공되기 전에는 official_flag=false로 유지한다.



12. 영상 공식 사용 품질 기준




Gate

검사

PASS 기준





VID-CONSIST

PPT 일치성

Storyboard scene이 approved SlidePlan/PPT slide와 매핑됨



VID-STRUCT

파일 무결성

ffprobe 성공, 손상 frame/0-byte 없음



VID-FORMAT

기본 규격

Prototype: 1920x1080, 16:9, H.264 MP4. 기관값은 config



VID-EVID

근거

scene/source_slide/source_refs 추적 가능



VID-BRAND

브랜딩

VideoProfile의 로고/인트로/아웃트로/자막 규칙 적용



VID-PROV

재현성

workflow/model/seed/profile/version 기록



VID-APPROVAL

공식 사용

Final QA PASS + Reviewer APPROVED






13. 비기능 요구사항




ID

우선순위

요구사항

검증/수용 기준

추적 대상






NFR-PERF-001



MUST


사용자-facing 동기 API(목록/상태/메타데이터)는 프로토타입 기준 정상 부하에서 p95 2초 이내를 목표로 한다. AI/파싱 장기 작업은 제외한다.

k6 또는 pytest benchmark 결과를 기록하고 초과 시 defect로 남긴다.

API




NFR-PERF-002



TBD


공단 최종 동시 사용자 수, 문서 크기, PPT/영상 SLA는 산업체 성능 기준 확인 후 확정한다.

TBD-NPS-PERF-001 해소 후 수치화.

TBD Register




NFR-REL-001



MUST


worker 1개 장애가 API/다른 queue를 중단시키지 않아야 한다.

worker kill chaos test 통과.

Docker/Queue




NFR-REL-002



MUST


모든 장기 작업은 idempotency 또는 중복 방지키를 사용해 사용자 재요청으로 동일 산출물이 무제한 중복 생성되지 않게 한다.

동일 idempotency key 재요청 결과가 동일 job/result를 반환한다.

JobService




NFR-MNT-001



MUST


API contract, DB migration, Prompt, Workflow, Template을 코드와 독립 버전 축으로 관리한다.

Release Manifest에 5축 이상 기록.

Release




NFR-PORT-001



MUST


환경별 차이는 config/secret/volume mapping으로 처리하고 업무 코드의 IP/VLAN hardcoding을 금지한다.

grep/config review에서 NPS 내부 IP hardcoding 0건.

Config




NFR-OBS-001



MUST


health/readiness endpoint와 job/worker 상태를 제공한다.

docker healthcheck가 DB/Redis/API/adapters를 검증한다.

/health




NFR-ACC-001



SHOULD


웹 UI는 키보드 탐색, 명확한 상태텍스트, 색상 외 상태표현 등 기본 접근성을 제공한다.

주요 workflow의 keyboard test PASS.

Web UI




NFR-KO-001



MUST


한국어 파일명·본문·표·PPT 텍스트를 UTF-8/Unicode로 손실 없이 처리하고 PDF/HTML 문서화에서 한글 글리프 깨짐이 없어야 한다.

golden 한글 문서 및 출력 육안/자동 검사 PASS.

전체






14. Docker 및 배포 명세


14.1 Prototype 서비스 구성




Service

내부 포트

외부 publish

Network

역할





edge

80/443

dev:8080, prod/offline:443(설정)

edge_net/app_net

Nginx reverse proxy + React static



api

8000

없음

app_net/data_net/ai_net

FastAPI REST/WS



postgres

5432

없음

data_net

메타데이터/업무 DB



redis

6379

없음

data_net/app_net

Queue broker/cache/progress



llm-adapter

8010

없음

ai_net/app_net

LLM provider abstraction



comfy-adapter

8020

없음

ai_net/app_net

Comfy workflow abstraction



doc-worker

-

없음

app_net/data_net

scan/parse/chunk



ppt-worker

-

없음

app_net/data_net

PPTX + QA



image-worker

-

없음

ai_net/data_net

이미지 GPU queue



video-worker

-

없음

ai_net/data_net

영상 GPU queue + ffmpeg



clamav

3310

없음

data_net

malware scan (prod/offline 필수)



llm-server

11434 등

없음

ai_net

dev reference. 운영은 adapter로 재매핑



comfyui-image

8188

없음

ai_net

dev/reference image worker backend



comfyui-video

8189

없음

ai_net

dev/reference video worker backend




14.2 Compose profile

profiles:
  dev      = edge + api + db + redis + mock/local adapters + workers
  offline  = prod-like + clamav + no-egress verification + local models/workflows
  prod     = edge + api + db/redis(or approved managed equivalent) + internal LLM/Comfy + workers

운영에서 서비스 주소는 환경변수/secret/config로 주입하며 NPS 실제 IP는 source code에 하드코딩하지 않는다.


14.3 Release Bundle

release-bundle/
  images/                 # docker image tar + digest
  models/                 # approved weights/manifest/hash (if packaging allowed)
  comfy/                  # workflow JSON + custom_nodes.lock
  wheelhouse/             # offline Python wheels
  npm-cache-or-static/    # source build 정책에 따라 정적 artifact
  frontend/               # web static build
  compose.prod.yml
  env.example
  release-manifest.yaml
  SBOM.spdx.json
  licenses/
  checksums.sha256
  INSTALL_ROLLBACK.md
  TEST_RESULTS/




15. GPU·Queue 정책


산학 제안서의 A40×4 역할 분리를 기준으로 하되 120B 모델의 실제 배치는 quantization/context/concurrency/serving engine에 따라 달라지므로 TBD-NPS-GPU-001로 관리한다.




GPU

기준 역할

Prototype/운영 처리





GPU 0~1

LLM Serving shard/inference

LLM Adapter → 내부 serving. 실제 TP/PP 구성은 Benchmark로 확정



GPU 2

Image / ControlNet / IP-Adapter

image queue, 예상 VRAM + heartbeat 기반 배정



GPU 3

Video / AnimateDiff / parallel job

video queue. 장시간 작업은 concurrency 제한




15.1 Scheduler 입력

job_type, priority, estimated_vram_mb, required_capability,
worker_heartbeat, worker_free_vram, active_jobs, retry_count


15.2 최소 정책


worker heartbeat 만료 시 신규 할당 금지

동일 GPU에 VRAM 초과 예상 작업 동시 할당 금지

User job은 기본 FIFO, Reviewer/발표 직전 등 조직 정책은 설정 가능한 priority

영상 장기 job이 이미지/PPT 전체를 starvation시키지 않도록 queue 분리




16. 시험 및 수용 기준


16.1 Golden Set




ID

입력

검증 포인트





GS-01

일반 보고서 PDF

섹션/문단/근거/PPT end-to-end



GS-02

표가 많은 PDF/HWPX

표 구조·병합·슬라이드 table



GS-03

이미지가 많은 DOCX

image refs·배치·clipping



GS-04

HWP/HWPX 한글 문서

한글·태그/섹션·문자 깨짐 없음



GS-05

XLSX 데이터

sheet/table → chart/table slide



GS-06

Prompt Injection 포함 문서

시스템 정책 변조 차단



GS-07

대형/압축폭탄/손상 파일

quarantine/limit/fail-closed



GS-08

동일 문서 재생성

manifest/provenance/reproducibility



GS-09

Worker 장애

retry/resume/다른 service 생존



GS-10

Offline clean host

bundle만으로 설치+E2E+rollback




16.2 Release Gate




Gate

필수 PASS 항목





GATE-S Security

외부 데이터 반출 0, edge 외 publish 0, secret scan, RBAC/IDOR, malicious upload 차단, audit



GATE-F Functional

문서 1건 → Parse → Chunk → SlidePlan → PPTX → MP4 end-to-end



GATE-Q Official Quality

PPT overflow/clipping 0, source trace, template rule, PPT/Video consistency, Reviewer approval



GATE-R Release

offline clean-host 설치, digest/hash/SBOM, runtime download 0, rollback, golden scenario






17. 요구사항 추적성




원 요구

SRS

API

Component

Test

Artifact





산학 제안: 문서 구조 복원/Chunking

FR-PARSE-001~005, FR-CHUNK-001~003

/documents/*

doc-worker

TC-PARSE/CHUNK

ParseResult/Chunk



산학 제안: LLM 요약·슬라이드 계획

FR-LLM-001~009

/slide-plans/*

llm-adapter

TC-LLM

SlidePlan



산학 제안: ComfyUI 이미지/영상

FR-VIS-001~008, FR-VID-*

generate-video

comfy-adapter/video-worker

TC-VIS/VID

VisualAsset/MP4



산학 제안: 편집 가능한 PPTX

FR-PPT-001~012

generate-ppt

ppt-worker

TC-PPT

PPTX + qa_report



산학 제안: RBAC/실시간 진행률

FR-IAM-*, FR-JOB-*

auth/jobs/ws

api/queue

TC-IAM/JOB

Audit/Job



통합계획: Offline Release

SEC-SUPPLY-*, SEC-OFFLINE-*

N/A

release tooling

TC-OFFLINE

release-bundle



사용자 보강: 타 공단 조직 사용

FR-IAM-004~007, FR-PRJ-*

organizations/projects

authz

TC-ORG

OrganizationUnit/ProjectMember



사용자 보강: 공식 사용 가치

FR-REV-*, FR-PPT-*, FR-VID-*

reviews/approve

QA/Review

TC-OFFICIAL

APPROVED Artifact






18. TBD Register




TBD ID

미확정 사항

확인 주체

목표 시점





TBD-NPS-NET-001

실제 서비스 배치 망 구역, Reverse Proxy/API Gateway, inbound/egress 정책

국민연금공단 보안/인프라 담당

SRS v1.1 전



TBD-NPS-IAM-001

AD/LDAP/OIDC/SAML 연계 방식과 조직/역할 claim

국민연금공단 IAM 담당

Feature Freeze 전



TBD-NPS-GPU-001

A40×4 단일/다중 호스트, GPU reservation, 120B 모델 엔진/quant/context/concurrency

국민연금공단 AI 운영 담당

M2~M4



TBD-NPS-STO-001

원본/산출물 저장경로, 용량, 백업, 암호화, 보존·삭제 기간

국민연금공단 인프라/보안

M5 전



TBD-NPS-SEC-001

악성코드 검사·SIEM·로그 보존·인증서·비밀관리 체계 연계

국민연금공단 보안

M5 전



TBD-NPS-OUT-001

공식 PPT Master, 폰트, 로고·컬러 가이드, 영상 해상도/코덱/자막/생성형 자산 정책

국민연금공단 실무 담당

M3 전



TBD-NPS-PERF-001

동시 사용자, 문서 최대 크기/페이지, PPT/영상 처리시간 검수 기준

국민연금공단 실무 담당

M4 전



TBD-NPS-REL-001

Docker image/model/custom node 승인 반입 경로 및 Release 승인 절차

국민연금공단 보안/운영

M6 전






19. 주요 리스크 및 제약




리스크

영향

대응





120B 모델이 예상 GPU 배치에서 목표 성능 미달

LLM 병목/동시성 저하

Adapter 유지, quant/context/batch benchmark, GPU mapping TBD



HWP binary 파서 호환성

문서 구조 복원 실패

Parser adapter, HWPX 우선 지원, hwp5 기반 best-effort, 오류 명시



공식 PPT Master 미확정

디자인 검수 지연

기본 내부 템플릿 + TemplatePolicy, 공식 master 수령 후 회귀테스트



Comfy custom node 의존성

Offline 설치 실패

custom_nodes.lock, image tar, checksum, offline smoke



AI 환각/문맥 오해

공식 자료 오류

source_ref 강제, plan validation, 2단계 human review



민감자료 로그/캐시 노출

보안 사고

redaction/log policy, ID storage path, retention, audit



영상 렌더링 장시간

Queue starvation

image/video queue 분리, GPU scheduler, cancel/retry



개발망과 공단망 차이

이관 실패

Docker/Config/Adapter, offline profile, NPS 실제 정책은 TBD 매핑






부록 A. 계약·Repository·Release 기준


A.1 Repository

capstone-nps/
  apps/
    web/                  # React + TypeScript + Vite
    api/                  # FastAPI + SQLAlchemy + Alembic
  services/
    llm-adapter/
    comfy-adapter/
  workers/
    document/
    ppt/
    image/
    video/
  packages/
    contracts/            # Pydantic + generated JSON Schema
  prompts/
  workflows/comfy/
  templates/
  infra/
    nginx/
    compose/
    scripts/
  migrations/
  tests/
    unit/
    integration/
    e2e/
    golden/
    security/
  docs/
  release/



A.2 SlidePlan 최소 계약

{
  "schema_version": "1.0",
  "plan_id": "uuid",
  "document_versions": ["uuid"],
  "title": "...",
  "audience": "internal",
  "slides": [{
    "slide_id": "uuid",
    "order": 1,
    "layout_type": "title_content",
    "title": "...",
    "content_blocks": [{
      "type": "text|table|chart|image",
      "text": "...",
      "source_refs": [{"document_version_id":"uuid","chunk_id":"uuid","page":1}]
    }],
    "visual_plan": {"mode":"preserve|generate|none","workflow":"wf-image-v1"}
  }]
}


A.3 Release Manifest 최소 필드

release: capstone-v0.x.y
app_git_sha: ...
images:
  edge: sha256:...
  api: sha256:...
  workers: {...}
model_manifest: ...
workflow_image: wf-image-v...
workflow_video: wf-video-v...
prompt_pack: prompt-slide-v...
schema_version: ...
template_version: ...
db_revision: ...
comfy_nodes_lock: ...
sbom: SBOM.spdx.json
offline_golden_test: PASS



본 SRS는 Prototype 구현용 계약과 국민연금공단 이관용 요구사항을 함께 정의한다. TBD가 해소되면 요구사항 ID를 유지한 채 값/수용기준을 개정한다.




팀 검토


성명/서명:


지도교수/산업체 확인


성명/서명:




