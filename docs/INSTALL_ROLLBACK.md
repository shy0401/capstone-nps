# 설치 · 검증 · Rollback

현재 bundle의 `release_ready`와 `missing_materials`를 먼저 확인한다. false이면 기관 반입용 최종 릴리스가 아니다.

## 준비

1. Docker Engine/Desktop와 Compose v2.24.4 이상. Windows는 BIOS 가상화, Virtual Machine Platform, WSL2 및 필요한 재부팅을 완료한다.
2. 인터넷 가능한 빌드 호스트에서 `python infra/scripts/bootstrap.py`, `docker compose -f compose.yml -f compose.dev.yml build`.
3. `docker compose --profile scan pull clamav`로 승인된 이미지/signature를 확보하고 EICAR를 실제 스캔한다.
4. dev golden, security, Office 렌더링, 실제 no-egress clean-host 검증과 backup/rollback을 수행한다.
5. `python infra/scripts/bundle.py`로 image tar/digest, frontend, wheels, hashes, SBOM과 증적을 묶는다.

## 오프라인 반입

1. 승인된 경로로 bundle을 반입한다. `python infra/scripts/verify_bundle.py <bundle> --require-ready`를 통과해야 한다.
2. `docker load -i images/runtime.tar`. compose가 참조하는 모든 image ID/digest를 manifest와 비교한다.
3. `env.example`를 `.env`로 복사하고 승인된 secret/config를 별도 주입한다. `.env`를 공유/커밋하지 않는다.
4. 기관 인증서 파일을 `infra/secrets/tls.crt`, `infra/secrets/tls.key`에 배치한다. 기관 values는 TBD Register로 관리한다.
5. `docker compose -f compose.yml -f compose.prod.yml -f compose.offline.yml up -d --no-build --pull never --wait`.
6. DNS/HTTP egress deny 상태에서 clean volumes로 Golden을 수행한다. `docker compose ps`의 published port가 edge만인지 검증한다.
7. `make offline-test`의 호스트 dependency 검사는 부분 증거이며 이 clean-host 절차를 대체하지 않는다.

## 백업과 Rollback

1. 업그레이드 전 쓰기를 중단하고 PostgreSQL `pg_dump -Fc` 및 storage volume snapshot을 같은 시점으로 보존한다.
2. 현행·이전 bundle 및 checksums, DB revision을 함께 보존한다. secret은 별도 승인된 저장소에 둔다.
3. 문제 시 현재 compose를 `down`한다. `down -v`는 사용하지 않는다.
4. 이전 bundle checksum/digest 검증 후 image tar를 load한다.
5. 데이터 호환이 확인되지 않은 경우 이전 DB dump와 storage snapshot을 별도 새 volume에 복구한다.
6. 이전 bundle의 compose를 `up -d --no-build --pull never --wait`, Golden/권한/다운로드 smoke를 수행한다.
7. `alembic downgrade base`는 개발 empty DB 시험용이며 운영 rollback 절차가 아니다.

v0.1.1에서 Docker 기동 및 독립 신규 volumes의 no-build/no-pull/egress deny 검증을 수행했다. 물리 clean-host 반입 및 이전 승인 bundle 기반 DB/storage rollback은 미검증이다.


## 개발용 묶음의 재현

기관 운영 반입과 별도로 `bundle.py --development`로 만든 CPU/mock 개발 묶음을 검증할 수 있다.
`verify_bundle.py <bundle>`로 checksum을 확인하고 `docker load -i <bundle>/images/runtime.tar`를 수행한다.
묶음의 `source/`로 이동해 bootstrap으로 새 secret을 생성한 뒤 `docker compose -f compose.yml -f compose.dev.yml up -d --no-build --pull never --wait`를 실행한다.
LLM/Comfy mock과 기본 템플릿 표시를 유지하며, 운영 `--require-ready` 검증을 대신하지 않는다.
