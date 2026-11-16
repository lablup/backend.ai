# service_catalog adapter: 배경

규칙은 상위 디렉터리의 `AGENTS.md` 에 있다. 이 문서와 실행 결과가 어긋나면 문장을 먼저 의심한다.

이 adapter 가 제공하는 호출은 검색(`admin_search`) 하나다. 카탈로그 row 는 service 가 스스로 등록하고 서비스 카탈로그 heartbeat 를 보낼 때 이벤트 처리기가 기록하며, 관리자가 생성, 수정, 삭제하는 호출은 없다. 검색은 전역 역할이 있어야 하고, 읽기 연산이므로 monitor 역할의 사용자도 권한 검사를 통과한다.

src 에서 row 를 생성하는 write spec 은 등록 처리기가 작성하는 upsert spec 하나이고, 그 spec 은 상태를 항상 정상으로 기록한다. 등록 해제 처리기와 서비스 카탈로그 heartbeat 가 끊긴 service 를 비정상으로 변경하는 처리기는 spec 없이 row 를 직접 수정한다. 따라서 비정상이거나 등록 해제된 상태의 service 는 시나리오 트리가 자체로 정의한 spec(등록 spec 에서 상태만 변경해 작성하는 것)으로 생성한다. 정상 상태의 service 는 src 의 spec 으로 생성한다.

## 검색

상태 필터는 `equals`, `in`, `not_equals`, `not_in` 네 조건을 받고, 상태가 같은 것/다른 것/목록에 든 것/목록에 들지 않은 것을 검색하는 시나리오가 조건을 하나씩 확인한다. 네 시나리오 모두 상태마다 service 하나씩을 두고, 지정한 상태의 service 만 남는지 확인한다.

요청 타입에는 `first`, `after`, `last`, `before` 필드가 있지만 이 검색은 페이지 크기(`limit`)와 `offset` 값만 읽는다. 커서 필드를 함께 지정하면 지금은 에러 없이 무시된다. 커서 시나리오는 이 필드 사용 여부에 대한 결정이 필요하다.
