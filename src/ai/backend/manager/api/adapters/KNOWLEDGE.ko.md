# Manager API adapters: 배경

> 규칙은 API 계층의 `AGENTS.md`, 구현 패턴은 `/api-guide` 스킬에 있다.

## adapter 가 인증 컨텍스트와 스코프 구성을 맡는다

adapter 는 두 API 표면(REST v2 와 GraphQL) 뒤의 단일 구현이다. `OperationScope` 를 생성하고 호출자 컨텍스트를 담으며 DTO 를 매핑한다. handler 와 resolver 는 파싱한 입력을 그대로 전달한다. `my` 검색은 예외로, handler 와 resolver 가 사용자 스코프를 생성한다.

## `my_` 패턴

스코프 검색이 있는 엔티티의 `my` 검색에는 자체 adapter 메서드가 없다. REST handler 는 `UserContext` 에서, GQL resolver 는 `current_user()` 에서 사용자를 가져와 각각 사용자 스코프를 생성하고 `scoped_search` 를 호출한다. 스코프 권한 검사는 스코프 검색과 같은 경로에서 실행된다. 엔티티마다 adapter 메서드가 하나 더 늘지 않는다.

대응하는 스코프 검색이 없는 `my_` 연산은 adapter 안에서 `current_user()` 로 사용자 컨텍스트를 가져와 `OperationScope` 를 직접 생성한다.

## 연산 이름을 계층마다 같게 맞추는 이유

같은 동작이 adapter, processor, service 에서 다른 이름을 가지면 호출 경로를 따라갈 때마다 대응표가 필요하다. 이름이 같으면 검색 한 번으로 세 계층이 모두 나온다.

`admin_` 은 gate 를 이름에 적는다. Action 의 모양(전역, 스코프, 단일 엔티티)이 gate 를 이미 말하므로 이름에 다시 적으면 둘이 어긋날 수 있다. `node` 는 GQL 타입 이름이 아래 계층으로 유입됐다.

REST 경로, handler 이름, GQL 필드 이름은 공개 계약이라 이 규칙과 무관하게 그대로 둔다. REST handler 이름은 OpenAPI 의 operationId 가 된다.

## adapter 가 다른 엔티티의 processor 를 받지 않는 이유

domain adapter 가 자원 그룹 processor 로 자원 그룹 이름을 해석하던 때는 두 엔티티의 adapter 가 서로의 processor 를 가지고 있었다. GQL resolver 가 자원 그룹 adapter 의 `lookup_name` 을 먼저 호출하고 id 를 전달하면 domain adapter 는 자기 processor 하나만 받는다. 이름 해석의 권한 판단도 한 곳에 남는다. `lookup_name` 은 인증만 검사하고, id 를 받은 연산이 권한을 검사한다.

REST handler 와 GQL resolver 가 생성해 adapter 에 전달하던 `UserInfo` 는 Action 이 사용하지 않았다. validator 가 요청 컨텍스트의 `current_user()` 로 권한을 판단하므로 같은 정보가 두 곳에 있었다.

도메인이 이 규칙을 처음 따랐다. 같은 epic 의 후속 작업이 다른 엔티티를 이 규칙으로 옮긴다.

## `entity_id` 와 `field_id` 가 `id` 옆에 있는 이유

GQL 의 `id` 는 Relay 전역 id 다. 타입 이름과 row 키를 base64 로 인코딩해 하나의 불투명한 값으로 생성하고, client 는 그 안을 보지 않는다. REST v2 의 `id` 는 그 안쪽 키를 그대로 노출하며, 키가 무엇인지는 엔티티마다 다르다. 도메인과 자원 그룹은 이름, keypair 는 access key, 에이전트는 문자열 id 를 사용한다. 따라서 `id` 에서 row 의 UUID 를 복원하는 방법이 엔티티마다 다르고, 이름이 키인 곳에서는 아예 불가능하다.

`entity_id` 와 `field_id` 는 그 UUID 를 하나의 이름으로 노출한다. adapter 가 data class 에서 값을 가져오므로 `id` 가 무엇을 담는지에 의존하지 않는다. `id` 의 안쪽 키가 이미 UUID 인 곳에도 두 값이 있다. 두 값은 그때 같지만, `id` 는 Relay 가 읽는 값이고 `entity_id` 는 client 가 다른 API 에 전달하는 값이다.

엔티티와 필드를 이름으로 구분하는 이유는 `data/` 가 둘을 나누는 이유와 같다. 엔티티 row 는 자기 membership 을 가지지만 필드 row 는 갖지 않는다. 이름만으로 그 row 에 권한을 요청할 수 있는지 응답에서 알 수 있다.

fair share 값과 resource allocation row 는 이 규칙 밖이다. 전자는 (자원 그룹, 스코프) 쌍마다, 후자는 (kernel, slot 이름)마다 계산하며 둘 다 row id 아래에 저장되지 않는다.
