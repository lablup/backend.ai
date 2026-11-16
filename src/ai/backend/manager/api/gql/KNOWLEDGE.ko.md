# Manager GraphQL 계층: 배경

> 규칙은 같은 디렉터리의 `AGENTS.md` 에 있고, 구현 패턴은 `/api-guide` 스킬에 있다.

## adapter 의존과 동작 surface

resolver 는 동작을 갖지 않는다. 모든 resolver 가 엔티티별 공유 adapter(`api/adapters/`)를 호출한다. 동작 surface 는 API 계층의 이름 규칙을 따른다. scoped 질의는 호출자가 전달한 scope 를 받고(parent-fixed 변형은 legacy 패턴이므로 새로 추가하지 않는다), `admin_` 접두사 field 는 superadmin global 동작이며 bare global 읽기는 인증된 모든 사용자에게 public 이다.

## federation 이름 충돌 주의

v2 Strawberry schema 는 v1 Graphene schema 와 함께 supergraph 로 구성된다. `GQL` 접미사를 뗀 schema 이름이 다른 모양의 기존 v1 Graphene type 과 충돌하면(예: `KeyPair`, `CreateContainerRegistryInput`) supergraph 구성이 실패한다. 그 경우 `V2` 접미사를 붙인 schema 이름(`name="KeyPairV2"`)을 사용한다. 기존 `DomainV2`/`UserV2` 관례와 같다. 이름을 변경한 뒤 `scripts/generate-graphql-schema.sh` 로 구성을 검증한다.

## pagination 모드 동작

search 질의는 cursor 와 offset 인자를 모두 받는다.

- **기본(인자 없음):** offset 을 기본으로 사용한다(`limit=10, offset=0`).
- **offset(`limit`/`offset`):** 사용자가 지정한 `order_by` 를 적용하고 없으면 엔티티의 기본 정렬을 적용한다. custom 정렬이 필요할 때 사용한다.
- **cursor(`first`/`after` 또는 `last`/`before`):** 정렬을 엔티티의 cursor key(보통 `created_at` 이나 primary key)로 고정한다. 사용자가 지정한 `order_by` 는 무시한다. cursor 일관성에는 고정 정렬이 필요하다. infinite-scroll 이나 "load more" UX 에 적합하다.
- 요청마다 모드 하나만 사용한다. `first` 와 `limit` 을 섞으면 에러다.

## relation 도 Node 다: id 는 끝으로 구성한 global ID 다

| 선언 | 예 | GQL 모양 | `id` |
|---|---|---|---|
| `EntityType` | `EntityShare`, `AppConfigAllowList` | Node | row id 의 global ID |
| `FieldType`, `DanglingFieldType` | `Permission`, `DomainFairShare`, `UserUsageBucket` | Node | row id 의 global ID |
| 없음(두 엔티티를 잇는 row) | `user_roles`, `idle_checker_bindings`, `session_idle_checks` | relation type, Node | 끝 UUID 들의 global ID |

- Node 는 server 가 id 만으로 다시 가져올 수 있는 객체다(Relay Global Object Identification). relation 은 끝으로 고정되므로 끝을 담은 global ID 가 id 만으로 그것을 다시 가져온다.
- relation 테이블에는 row id 가 없다. 끝의 쌍이 primary key 다(BEP-1075). 쌍 밖의 id 는 같은 relation 의 두 번째 이름이고, 그것으로 찾은 relation 은 권한을 검사하기 전에 끝으로 다시 읽어야 한다.
- Node 이므로 relation 은 Relay store 에서 정규화되고 unlink 응답의 `purgedId` 가 `@deleteEdge` 에 들어간다.
- global ID 는 GQL 계층에 남으므로 client 가 저장한 id 가 relation 을 변경하는 요청으로 변경되지 않는다. relation 을 변경하는 인자는 끝 UUID 다.
- 자기 lifecycle 을 가진 row 는 relation 으로 두지 않고 entity type 으로 선언한다.

## relation 값은 relation type 의 connection 으로 읽는다

relation row 는 client 가 읽어야 하는 값을 담는다. 누가 언제 부여했는지, 활성인지, session 의 idle check 상태와 기한이다. 노출 방식 둘 중 relation type 의 connection 을 골랐다.

| 기준 | 엔티티를 직접 잇고 값을 edge field 에 두는 방식 | relation type 의 connection |
|---|---|---|
| 값 읽기 | edge field | relation type field |
| relation 당 type | 방향마다 Edge, Filter, OrderBy 하나 | relation type, Filter, OrderBy 를 두 방향이 공유 |
| relation 값과 엔티티 조건을 함께 필터링 | 방향마다 wrapper Filter | relation type 의 Filter 에 end entity 조건을 중첩 |
| mutation payload | 끝 id 만, 또는 별도로 정의한 모양 | 변경된 relation type 객체 |
| 다른 엔티티까지 거리 | 한 단계 | 두 단계(`node.checker`) |

- relation type 을 Node 로 두므로 그 connection 은 strawberry 의 `Edge` 와 `Connection` generic 을 그대로 사용한다.
- cursor 는 불투명 문자열이므로 끝 key 를 인코딩해도 id 로 row 를 변경하는 경로가 열리지 않는다. cursor 조건 factory 는 문자열을 받고 여러 primary key column 도 담는다.
- `node(id:)` 와 `nodes(ids:)` 는 끝 key 목록으로 relation 을 한 번에 읽고 두 끝 scope 에 읽기를 요구한다. global ID 가 두 끝을 담으므로 한쪽만 요구하면 다른 끝 엔티티가 권한 없이 드러난다.

## Node 는 id 기반 동작을 거부하면서 id 를 유지할 수 없다

- v2 schema 의 root `node(id: ID!): Node` 는 Node 를 구현한 모든 type 을 id 로 읽는다. 이것을 막으면 그 lookup 이 실패하고 id 만으로 다시 가져오는 Node 계약이 깨진다.
- `DomainFairShare`, `ProjectFairShare` 와 `UserFairShare` 는 (resource group, scope) 쌍마다 계산되고 row id 가 없다. `node(id:)` 와 `nodes(ids:)` 는 그 id 에 에러가 아니라 `null` 로 응답한다.

## mutation payload 는 응답 시점의 대상 존재 여부를 따른다

| 응답 시점의 대상 | payload | 이유 |
|---|---|---|
| 존재(create, update, soft delete, restore, `purge_status` 가 있는 엔티티의 purge) | 대상 Node | Relay store 가 같은 id 의 record 를 갱신한다 |
| 사라짐(요청 안에서 purge 가 끝남, force purge) | `purgedId` + UUID | `@deleteEdge` 와 `@deleteRecord` 가 `ID` 또는 `[ID]` field 를 받아 그 node 의 edge 와 record 를 제거한다 |

- payload 자체의 `id` 에 global ID 를 두면 제거된 Node 와 같은 Relay store key 가 되어 충돌한다. Relay 예(`deletedTodoId`), GitHub(`deletedItemId`), Shopify(`deletedProductId`)는 자기 field 를 사용한다.
- 제거된 대상을 Node 로 반환하면 제거된 대상의 권한 검사에서 자식 connection 이 실패한다(`PurgeRolePresetPayload.rolePreset.permissionPresets`).
- `purge_status` 가 있는 엔티티(BEP-1069)는 purge 요청이 반환될 때 row 가 남아 있다. 여기에 `purgedId` 를 두면 아직 존재하는 Node 를 제거됨으로 보고한다. Kubernetes 는 finalizer 가 남은 객체에 대한 DELETE 에 202 와 남은 객체로 응답하고, Shopify 의 비동기 `productDelete` 는 operation 객체를 반환하고 완료되면 `deletedProductId` 를 채운다.
- field 이름은 `deletedId` 가 아니라 `purgedId` 다. 여기서 delete 는 soft delete(`deleted_at`)이고 그 응답이 Node 를 반환한다. 위 예는 자기 mutation 동사로 field 이름을 정한다(`productDelete` → `deletedProductId`).
- purge payload 는 자기 type 이다(`Purge<X>Payload`). soft delete 나 deprecated delete 와 공유하는 `Delete*Payload` 는 대상이 아직 존재할 수 있는 응답에 `purgedId` 를 두게 된다.
- REST 와 DTO 는 global ID 를 담지 않는다. Azure Key Vault 의 purge 는 body 없이 204 로 응답하고 AIP-165 `Purge` 는 제거 건수만 반환한다.

## relation type 이름은 table 이 아니라 코드를 따른다

| relation | table | 코드 이름(Data, DTO, CLI, REST) | relation type |
|---|---|---|---|
| session 과 idle checker | `session_idle_checks` | `SessionIdleCheckData` | `SessionIdleCheck` |
| scope 와 idle checker | `idle_checker_bindings` | `IdleCheckerAssignmentData`, CLI `idle-checker-assignment` | `IdleCheckerAssignment` |
| user 와 role | `user_roles` | DTO `RoleAssignmentNode`, CLI `rbac assignment`, REST `/assignments` | `RoleAssignmentV2` |

- table 을 따르면 `IdleCheckerBinding` 이 되어 service, CLI, REST 이름과 어긋난다.
- `UserRole` 은 계정 role enum `UserRoleV2`(`UserV2.role`, `UserV2.roles`) 옆에 놓여 같은 type 의 version 으로 읽힌다.

## 공개된 relation Node

| relation | 현재 | 대상 |
|---|---|---|
| user 와 role | `RoleAssignment` Node(row id), deprecated | `RoleAssignmentV2` relation Node, (user, role) 로 구성한 id |
| scope 와 idle checker | `IdleCheckerAssignment` Node(row id), 미출시 | 같은 이름의 relation Node, (scope type, scope id, idle checker) 로 구성한 id |
| session 과 idle checker | 읽기 없음, mutation 만 | `SessionIdleCheck` relation Node, (session, idle checker) 로 구성한 id |

- `RoleAssignment.id` 는 `ID!` type 을 유지하고 값만 끝의 global ID 가 된다.
