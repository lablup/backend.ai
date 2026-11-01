---
name: service-catalog-adapter-scenarios
type: reference
description: what the service catalog adapter guarantees; the single search behind the global role that the monitor role also passes, the status filter conditions it accepts, and the cursor fields it ignores
scope: src/ai/backend/manager/api/adapters/service_catalog
keywords: [service catalog, scenario, adapter, superadmin, monitor, search, endpoints]
generated:
  by: claude-code/opus-5
  at: 2026-09-17
updated:
  by: claude-code/opus-5.5
  at: 2026-10-07
status: draft
---
# service_catalog 어댑터 — 시나리오

규칙은 상위 디렉터리의 `AGENTS.md`에 있다. 여기 적힌 내용과 실행 결과가 어긋나면 문장 쪽을 먼저
의심한다.

이 어댑터가 제공하는 호출은 검색(`admin_search`) 하나다. 카탈로그 행은 서비스가 스스로 등록하고
heartbeat를 보낼 때 이벤트 처리기가 기록하며, 관리자가 생성·수정·삭제하는 호출은 없다. 검색은
전역 역할이 있어야 하고, 읽기 연산이므로 모니터 역할의 사용자도 권한 검사를 통과한다.

src에서 행을 만드는 write spec은 등록 처리기가 쓰는 upsert spec 하나이고, 그 spec은 상태를 언제나
정상으로 기록한다. 등록 해제 처리와 heartbeat가 끊긴 서비스를 비정상으로 바꾸는 처리는 spec 없이
행을 직접 수정한다. 그래서 비정상·등록 해제 상태의 서비스는 시나리오 트리가 자체로 정의한 spec —
등록 spec에서 상태만 바꿔 쓰는 것 — 으로 만든다. 정상 상태의 서비스는 src의 spec으로 만든다.

## 검색

상태 필터는 `equals`, `in`, `not_equals`, `not_in` 네 조건을 받고, 상태가 같은 것·다른 것·목록에
든 것·목록에 들지 않은 것을 검색하는 시나리오가 조건을 하나씩 확인한다. 네 시나리오 모두 상태마다
서비스 하나씩을 두고, 지정한 상태의 서비스만 남는지 본다.

요청 타입에는 `first`·`after`·`last`·`before` 필드가 있지만 이 검색은 페이지 크기(`limit`)와
`offset` 값만 읽는다. 커서 필드를 함께 지정하면 지금은 오류 없이 무시된다. 커서 시나리오는 이 필드를
무시할 것인지 사용할 것인지 정한 뒤에 적는다.
