# 아키텍처

Browser → Nginx edge → FastAPI → PostgreSQL/Redis. 문서·LLM·PPT·이미지·영상 Worker는 각각 독립 프로세스다.
LLM/Comfy는 내부 HTTP Adapter를 경유하며 브라우저에는 내부 주소·인증키를 전달하지 않는다.

`nps.jobs`는 DB에 작업과 단계 체크포인트를 저장하고 Redis에 큐 힌트·Worker heartbeat를 저장한다.
DB outbox가 원본이므로 Redis 쓰기가 실패해도 작업 요청이 유실되지 않는다. Worker는 Redis heartbeat와
capability/VRAM을 확인한 뒤 DB의 조건부 UPDATE로 작업을 원자적으로 점유한다. 만료된 lease는 WORKER_LOST로 실패한다.

모든 장기 처리와 실제 악성코드 검사는 HTTP 요청 이후 Worker가 수행한다. 업로드 요청에서는 파일을 64KiB씩 격리 저장한다.
파서는 subprocess에서 실행하며 Linux에서는 CPU/address-space 상한을 적용한다. Windows 진단은 timeout만 검증한다.

호스트 진단: `tests/e2e/local_stack.py`는 SQLite + fakeredis TCP emulator + 실제 HTTP Adapter를 사용한다.
이는 명시적 진단 전용이며 PostgreSQL/Docker/실제 Redis/오프라인 검증을 대체하지 않는다.

기관 망과 GPU 구성은 모두 SRS의 TBD ID로 남긴다. 실제 A40나 기관 모델에서 실행했다는 주장을 하지 않는다.
