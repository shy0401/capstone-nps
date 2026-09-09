# 보안 구현과 검증 범위

- Argon2id local credential, 10분 access JWT, 회전·폐기 가능한 hash-only refresh session.
- Refresh: HttpOnly/SameSite=Strict. Secure는 기본 활성. dev의 명시적 옵션만 HTTP 허용.
- Organization 범위와 ProjectMember를 동시에 검사한다. SystemAdmin도 문서 자동 열람 권한이 없다.
- 파일명으로 경로를 만들지 않는다. storage key는 서버 UUID. 확장자/MIME/magic/container/ZIP guard를 검사한다.
- 악성코드 UNKNOWN/오류/timeout은 fail-closed. mock scanner는 시험용이며 실제 백신이 아니다.
- XML entity/ZIP traversal/폭탄/embedded VBA/OLE 차단. 파서에서 외부 링크를 실행·다운로드하지 않는다.
- LLM 문서 입력은 system 지시와 분리한다. 출력 스키마, source_ref 범위, 길이를 검증한다.
- SlidePlan 승인 버전과 생성 요청 버전이 같아야 한다. 장기 작업 후에도 다시 검사한다.
- 모든 사용자 콘텐츠는 React text로 렌더링한다. HTML 실행 API를 쓰지 않는다.
- 로그에 본문/헤더/URL query/token/password를 기록하지 않는다. 감사로그는 명시적 metadata allowlist만 허용한다.
- app/ai/data Docker network는 internal. 외부 port mapping은 edge만 있다.

보안 테스트는 `tests/security`, `tests/integration`, Golden의 객체별 IDOR를 포함한다.
실제 ClamAV EICAR는 `RUN_CLAMAV_TEST=1` 설정으로 실행한다. 실행하지 않은 실서비스 보안 검증은 PASS로 표시하지 않는다.
TLS 인증서/기관 SIEM/백신 signature 반입·갱신은 TBD-NPS-SEC-001이다.
