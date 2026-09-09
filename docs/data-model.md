# 데이터 모델

`apps/api/nps/models.py`에 SRS 7절의 24개 업무 모델과 RefreshSession을 정의한다.
`migrations/versions/39b4465bf603_initial_schema.py`는 실제 Alembic create/drop migration이다.
UUID 문자열 PK, timezone-aware UTC timestamp, 주요 FK/unique constraint를 사용한다.

원본은 Document/DocumentVersion, 정규화는 ParseResult/Chunk, 계획은 SlidePlan/Slide,
시각 자산은 VisualAsset, 산출물은 Artifact/ArtifactVersion으로 분리한다. JSON 계약을 DB와 별도 namespace 파일에 저장한다.
DocumentVersion은 백신 CLEAN 이후에만 생성한다. 격리 단계 metadata는 GenerationJob payload에 저장한다.
삭제는 논리 삭제이며 실제 보존·폐기 작업의 기관 정책은 TBD-NPS-STO-001이다.

PostgreSQL 16이 Compose의 기본 DB다. SQLite는 호스트 단위/통합 진단에 한정한다.
