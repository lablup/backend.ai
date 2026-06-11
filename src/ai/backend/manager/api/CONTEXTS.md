# Manager API 레이어 — 컨텍스트

> 규칙은 같은 디렉터리 `AGENTS.md`, 구현 패턴은 `/api-guide` 스킬.

## Adapter `my_` 패턴

self-service(`my_`) 엔드포인트에서 인증은 Adapter가 내부에서 처리한다. Adapter가 `current_user()`를
호출해 사용자 컨텍스트를 얻고 거기서 `SearchScope`를 구성한다. GQL resolver / REST 핸들러는 스코프를
넘기지 않고 search 입력 DTO만 넘긴다. 인증 로직을 resolver마다 흩뿌리지 않고 adapter에 모으기 위함이다.

## v2 엔드포인트 검증

신규 API 엔드포인트는 커밋 전 라이브 서버로 검증한다. 서버 재시작·`./bai` 명령·로그 확인 절차는
`/local-dev`, `/bai-cli`, `/observability` 스킬 참고.
