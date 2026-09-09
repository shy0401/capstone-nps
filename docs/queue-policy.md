# Queue/실패 복구

| 단계 | 큐 |
|---|---|
| SECURITY_SCAN, PARSE, CHUNK | q_document |
| LLM_SUMMARY, LLM_KEY_MESSAGES, LLM_OUTLINE, LLM, LLM_VISUAL, PLAN_VALIDATE | q_llm |
| IMAGE | q_image |
| PPT, PPT_QA | q_ppt |
| VIDEO, FINAL_QA | q_video |

각 Worker는 1개 작업만 실행한다. FIFO에 우선순위를 적용하고 capability/estimated_vram/heartbeat를 확인한다.
lease 기본 120초, heartbeat TTL 20초, 5초마다 갱신한다. Worker 종료 뒤 lease 만료 시 FAILED/WORKER_LOST가 된다.
retry는 최대 3회이며 실패 또는 취소 단계부터만 가능하다. 완료된 선행 단계의 output은 재사용한다.
명시적 사용자 retry가 기본이고 local LLM schema retry는 2회까지 자동 수행한다.

취소는 step 전후 및 ffmpeg polling에서 관측한다. 원격 LLM/Comfy HTTP 호출 중에는 응답/timeout까지 지연될 수 있다.
실제 GPU 하드 취소/VRAM 측정은 기관 serving/workflow 연결 후 추가 검증이 필요하다.
