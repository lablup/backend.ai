# Manager API 계층: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있고, 구현 패턴은 `/api-guide` 스킬에 있다.

## surface 둘, adapter 하나

이 계층은 각 동작을 두 surface 로 노출한다. REST v2(`api/rest/v2/`)는 주로 CLI 가 소비하고 GraphQL(`api/gql/`)은 주로 WebUI 가 소비한다. 모든 동작을 두 surface 에 함께 제공한다. 하나 없이 다른 하나만 추가하면 client 가 그 기능을 받지 못한다. 어느 surface 도 동작을 가지지 않는다. 둘 다 엔티티별 공유 adapter(`api/adapters/{entity}.py`)를 호출하고, adapter 가 auth context, scope 구성, DTO 매핑을 맡으므로 두 surface 가 어긋날 수 없다. adapter 쪽 패턴: [adapters/KNOWLEDGE.md](adapters/KNOWLEDGE.md).

## 동작 이름과 gate

| 모양 | 의미 | gate |
|---|---|---|
| `admin_*` | 모든 scope 에 걸친 global 동작 | superadmin |
| bare global 조회(get/search) | public 조회, 인증된 모든 사용자에게 제공 | 인증됨 |
| scoped 동작(`scoped/search` 경로) | 호출자가 전달한 scope 에 걸친 동작 하나 | scope 별 RBAC |
| `my_*` | self-service. 호출자가 scope 이다 | 인증됨(adapter 가 user 를 식별한다) |

## v1 surface 를 동결한다

REST v1 과 graphene GQL 계열(`gql_legacy/`)은 대체 대상이지 유지보수 대상이 아니다. 그 위에 구축한 변경은 v2 대체 비용을 높이고, v1 만의 변경은 다른 surface 와 SDK, CLI 가 뒤처지게 한다. 따라서 추가와 변경은 모두 v2 로 가고 v1 은 치명적인 결함에 대한 수정만 받는다.

## v2 endpoint 검증

새 API endpoint 는 commit 전에 live server 로 검증한다. server 재시작, `./bai` 명령, log 확인은 `/local-dev`, `/bai-cli`, `/observability` 스킬에 있다.
