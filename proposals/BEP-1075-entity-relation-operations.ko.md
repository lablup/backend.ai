---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-08-26
Created-Version: 26.8.0
Target-Version: 
Implemented-Version: 
---

# 엔티티 관계 연산

## 관련 이슈

- BA-7467 — (액션이 엔티티를 가리키는 방식)
- BA-7468
- BA-7469
- BA-7470
- BA-8573 — (API 에서 Node 와 관계를 식별하는 방식)
- BA-8619 — (관계 식별과 삭제 응답 규칙)
- BA-8459 — (resource group ↔ keypair 를 user 로)
- BEP-1076 — (Project Membership) — 한쪽이 다른 쪽에 담기는 경우

## 동기

두 엔티티를 잇는 연산의 권한을 무엇이 답하는지 정해져 있지 않다.

관계를 virtual scope 로 다루면 그래프가 답한다. 다루지 않으면 연산이 스스로 답해야 한다.
지금은 도메인마다 다르게 답해서, 같은 관계가 어느 API 로 만들어졌는지에 따라 권한 그래프에
들어가기도 하고 안 들어가기도 한다.

| 연산 | 매핑 행 | 권한 그래프 |
| --- | --- | --- |
| resource group 을 domain · project 에 연결 / 해제 | 쓴다 | 쓴다 |
| resource group 을 keypair 에 연결 / 해제 | 쓴다 | 쓰지 않는다 |
| domain · project 의 허용 resource group 편집 | 쓴다 | 쓴다 |
| domain 생성 · 편집 중 resource group 지정 | 쓴다 | 쓰지 않는다 |

API 가 관계를 가리키는 방식도 관계마다 다르다. `user_roles` 와 `idle_checker_bindings` 는 행 id 를
API 에 내보내고, 나머지 관계는 양 끝으로 가리킨다. 행 id 를 받는 API 는 그 id 를 저장한 클라이언트가
있어야 관계를 바꿀 수 있고, 행 id 로 찾은 관계는 양 끝으로 권한을 다시 확인해야 한다.

**virtual scope 는 소유만 표현한다.** 관계는 비즈니스 로직이 읽는 것을 만들고, 그 연산의 권한은
관계가 가리키는 두 scope 가 답한다. 관계 자신은 양 끝으로만 식별한다.

## 현재 설계

### 관계 테이블

| 테이블 | 잇는 것 | 자기 데이터 | 다형 참조 | 행 id |
| --- | --- | --- | --- | --- |
| `sgroups_for_domains` | resource group ↔ domain | 없음 | 아니오 | 있음, 쓰지 않음 |
| `sgroups_for_groups` | resource group ↔ project | 없음 | 아니오 | 있음, 테스트 1곳 |
| `sgroups_for_keypairs` | resource group ↔ keypair — 잇는 뜻은 user | 없음 | 아니오 | 있음, 쓰지 않음 |
| `association_groups_users` | user ↔ project | 없음 | 아니오 | 있음, 쓰지 않음 |
| `user_roles` | user ↔ role | `granted_by` · `granted_at` | 아니오 | API 에 나감 |
| `idle_checker_bindings` | idle checker ↔ scope | `enabled` | 예 | API 에 나감 |
| `association_container_registries_groups` | container registry ↔ project | 없음 | 아니오 | 있음, 존재 확인 1곳 |

셋 이상을 잇는 관계는 없다. 행 id 를 FK 로 참조하는 테이블은 없다. 앞의 네 테이블은 원래 양 끝 쌍이
기본 키였다 (migration `caf54fcc17ab`).

`session_dependencies` 는 의존하는 세션의 field 다. 상호작용이 한 방향이라 관계가 아니다.
`replica_groups` 와 `endpoint_tokens` 는 deployment 의 field 로 다룬다.

### 행 id 가 API 에 나가는 곳

| 관계 | 행 id 를 쓰는 곳 |
| --- | --- |
| user ↔ role | `RoleAssignment.id` Node id, data loader, cursor, lookup, SDK 응답 |
| idle checker ↔ scope | REST 경로(`/idle-checker-assignments/{id}`), GraphQL 입력과 응답, CLI, cursor, lookup key |

WebUI 는 role 할당 id 를 목록 행 키로만 쓰고 revoke 는 (userIds, roleId) 로 한다. idle checker 할당은
WebUI 에 붙지 않았다.

### resource group 연결은 이름 목록을 통째로 바꾼다

`adminUpdateAllowedResourceGroupsForDomainV2` · `…ForProjectV2` 와 그 반대 방향 두 개는 이름 목록을 받아
관계를 통째로 교체한다. 한 쌍을 잇거나 끊는 연산이 없다.

### 비즈니스 로직이 관계 테이블을 읽는다

`query_allowed_sgroups(domain_name, group, access_key)` 는 세 테이블을 union 으로 읽어 세션이 돌 수 있는
resource group 을 정한다. 세션 생성과 스케줄링이 이것을 부른다. project ↔ user 검색도 같은 방식으로
관계 테이블을 읽는다.

### virtual scope 는 소유를 표현한다

virtual scope 간선은 값 하나(`permission_cap`)를 싣고, 그래프는 (user, 엔티티, 권한) 꼴의 질문에 답한다.
관계는 둘 다 맞지 않는다.

- 실을 값이 접근의 양이 아니다 — `enabled`, `granted_by`, 또는 값 없음
- 주체가 user 가 아니다 — domain 이 resource group 에서 스케줄된다

소유한다고 idle checker 가 돌거나 role 의 권한이 적용되지 않는다. 소유와 동작은 다른 축이다.

## 제안 설계

### 관계는 세 번째 자리다

엔티티도 field 도 아니다. 개별 관계 테이블은 둘 중 어느 것으로도 다루지 않는다.

|  | 자리 |
| --- | --- |
| 값이 접근의 양이고 주체가 user | virtual scope 간선 — 테이블 없음 |
| 그 밖에 두 엔티티를 잇는 것 | **관계 — 자기 테이블, 자기 연산** |
| 다른 쪽이 관계를 갖지 않는 값 | field |

### 관계는 양 끝 UUID 로 식별한다

| 자리 | 식별 |
| --- | --- |
| 테이블 | 행 id 컬럼 없음. 양 끝 쌍이 기본 키 |
| repository · 권한 검사 | 양 끝 UUID 로만 조회 |
| adapter · DTO | 양 끝 UUID 만 다룬다 |
| GraphQL 의 관계 id | 관계 타입 이름과 양 끝 UUID 로 만든 global ID. GraphQL 층에서만 만들고 푼다. 타입은 `ID!` |
| `node(id:)` | 관계 타입은 Node 를 구현한다. global ID 를 양 끝으로 풀어 다시 읽는다 |
| 개별 query · mutation · REST | 양 끝 UUID 를 모두 인자 · 바디로 받는다. global ID 와 경로의 id 를 받지 않는다 |

global ID 는 `node(id:)` 조회와 Relay store 의 키에만 쓴다. 관계를 바꾸거나 고르는 인자는 양 끝 UUID 다.

`node(id:)` 로 관계를 읽으려면 양 끝 scope 모두에 read 권한이 있어야 한다. global ID 가 양 끝을 모두
담고 있으므로 양쪽을 다 묻는다.

양 끝이 정해지면 관계가 정해진다. 쌍 밖의 id 는 같은 관계를 가리키는 두 번째 이름이 될 뿐이고,
그 id 로 찾은 관계는 양 끝을 다시 읽어야 권한을 물을 수 있다.

다형 참조가 있는 관계는 다형 쪽의 타입까지 키에 넣는다. idle checker 할당의 키는 unique 제약과 같은
(scope type, scope id, idle checker) 셋이다.

### 액션이 권한을 정한다, ops 가 아니라

관계 ops 는 쌍을 받아 행을 쓴다. 권한은 모른다. 누가 실행할 수 있는지는 액션이 정하고, 액션의 모양은
**한쪽이 다른 쪽에 담기는지**로 갈린다.

|  | 예 | 모양 |
| --- | --- | --- |
| 담김 | project ⊃ user | `scope_targets` = 담는 쪽만, `entity_type` = 담기는 것 |
| 담기지 않음 | resource group ↔ domain | `scope_targets` = 양쪽, `entity_type` 없음 |

resource group 은 여러 domain 이 나눠 쓰는 클러스터 자원이라 어느 쪽도 다른 쪽 안에 있지 않다.
이때 권한은 가리킨 scope 각각에 직접 묻는다.

```
link · unlink  →  왼쪽 scope 의 권한  AND  오른쪽 scope 의 권한
```

`entity_type` 이 없으면 "이 scope 안에서 이 타입에 대한 권한" 을 물을 수 없으니 scope 자체의 권한만
남는다.

담기는 경우는 이미 있는 scope 모양 그대로다. project membership 이 그 경우이고 BEP-1076 이 다룬다.

### ops

```
create_relation (scope, target, creator)   행, scope 가 target 을 READ 로 govern, target 이 scope 를 read
delete_relation (scope, target, updater)   `deleted_at` 에 현재 시각을 쓴다. 양쪽 read 는 남는다
restore_relation(scope, target, updater)   `deleted_at` 을 NULL 로 되돌린다
purge_relation  (scope, target, purger)    행과 양쪽 read 를 지운다
```

가운데 둘은 soft delete Mixin(`deleted_at`, BEP-1069)을 가진 관계에만 배선한다. 두 scope 모두에 권한이
있으면 관계를 soft delete 하고 restore 할 수 있다. soft delete 는 unlink 와 같은 권한이다. 관계는 외부 자원
정리가 없어 `purge_status` 를 두지 않고, purge 는 요청 안에서 끝난다.

### spec 이 정하는 것

- create 는 새 행만 넣는다. 이미 이어진 쌍은 soft delete 됐든 아니든 기본 키 위반이고, spec 의
  `integrity_error_checks` 가 도메인 에러로 바꾼다. 되살리는 것은 restore 라서 create 에 upsert 는 없다.
- soft delete · restore 는 `deleted_at` 만 쓴다. 각 쪽이 상대를 읽는 것(scope 의 govern READ, target 의
  share READ)은 남는다. soft delete 된 관계도 양쪽에서 보여야 restore 할 수 있다. 접근을 지우는 것은
  purge 뿐이다. soft delete 된 관계를 쓰지 않는 것은 읽는 쪽 일이다 (resource group 을 고르는 스케줄러,
  적용하는 idle checker).
- soft delete Mixin 이 없는 관계는 create 와 purge 만 있다.
- `idle_checker_bindings.enabled` 는 켜고 끄는 업무 값이다. soft delete 가 아니다.

### resource group 연결은 link · unlink 로 바꾼다

resource group 과 domain, project 의 연결은 이름 목록 통째 교체(`adminUpdateAllowed*`) 대신 쌍 하나를
link · unlink 하는 연산으로 다룬다. 두 연산은 양 끝 UUID 를 받는다. resource group 과 keypair 의 연결은
BA-8459 가 user 연결로 바꾸면서 다룬다.

### 관계를 읽는 방식

관계는 관계 타입으로 읽는다. 관계 타입은 Node 이고, 양 끝 엔티티와 관계 값, 양 끝으로 만든 global ID
를 가진다. 행 id 는 없다.

목록 조회의 권한 검사는 새 장치가 필요 없다. scope 연산이 이미 가진 두 축에 놓인다.

| 축 | 값 |
| --- | --- |
| `scope_targets()` | domain — 권한을 여기에 묻는다 |
| `operation_scopes()` | 관계 테이블에서 만든 조건 |

resource group 마다 간선을 둘 필요가 없다. 관계에서 권한을 끌어내면 같은 엔티티가 여러 관계로 닿을 때
참조 횟수 세기가 되고, 비즈니스 연산의 부수 효과로 쓴 권한은 권한 모델에 보이지 않는다.

### 관계를 바꾸는 연산의 응답

| 연산 | DTO · REST | GraphQL payload |
| --- | --- | --- |
| link (create) · update · soft delete · restore | 관계 DTO | 관계 Node |
| unlink (purge) | 양 끝 UUID | `purgedId: ID!`(관계의 global ID) + 양 끝 UUID |

Node 와 같은 규칙이다. 관계가 남는 연산은 관계를 돌려주고, 사라지는 연산은 Relay 의 `@deleteEdge` ·
`@deleteRecord` 가 쓸 global ID 를 돌려준다. 규칙 전체는 `api/gql/AGENTS.md` 에 있다.

### 관계 기반 검색

`OperationScope` 구현 48개 중 9개는 이미 관계 테이블을 subquery 로 써서 대상을 좁힌다.

```python
class DomainResourceGroupOperationScope(OperationScope):
    def to_condition(self) -> QueryCondition:
        return lambda: ResourceGroupRow.id.in_(
            sa.select(ResourceGroupForDomainRow.resource_group_id)
            .where(ResourceGroupForDomainRow.domain_id == self.domain_id)
        )
```

관계가 자기 테이블과 두 참조 컬럼을 선언하면 그 9개는 손으로 쓰지 않고 선언에서 나온다.

**scope 검색 전체가 하나로 합쳐지지는 않는다.** 나머지 39개는 대상 행의 컬럼에 scope id 를 싣고
(`SessionRow.group_id == project_id`) 관계를 거치지 않는다. 합쳐지는 것은 관계를 거치는 9개다.

## 마이그레이션 / 호환성

### 남는 것

관계 테이블은 남는다. 비즈니스 로직이 직접 읽고, 그 읽기가 정하는 것을 virtual scope 가 표현하지 못한다.

### 없어지는 것

| 대상 | 순서 |
| --- | --- |
| resource group 관계가 쓴 권한 그래프 간선 | 남겨 두면 그 경로로 만든 관계만 domain 관리자에게 상속된다 |
| `sgroups_for_*` 셋 · `association_groups_users` · `association_container_registries_groups` 의 행 id | 바로 지운다. 기본 키를 양 끝 쌍으로 되돌린다 |
| `user_roles` · `idle_checker_bindings` 의 행 id | API 를 양 끝 기반으로 옮긴 뒤 지운다 |
| `adminUpdateAllowed*` 네 mutation | link · unlink 를 더하고 deprecated |

### API 호환

- `RoleAssignment.id` 와 `IdleCheckerAssignment.id` 는 `ID!` 그대로 두고 값만 양 끝 global ID 로 바뀐다.
- 행 id 를 받던 입력 · REST 경로는 양 끝 UUID 를 받는 것을 더하고 deprecated 로 둔다. 행 id 컬럼이
  없어지면 행 id 로는 찾을 수 없다.
- 관계 타입(`RoleAssignmentV2`, `IdleCheckerAssignment`, `SessionIdleCheck`)이 Node 를 구현한다. 필드를
  더하는 변경이다.

### 관계는 updater 의 field 로 싣지 않는다

지금 updater 둘이 관계를 싣고 있고, 스스로 그렇다고 밝힌다.

| Updater | Field | 쓰는 것 |
| --- | --- | --- |
| `UserUpdater` | `group_ids` | user 의 project membership |
| `ContainerRegistryUpdater` | `allowed_groups` | registry 의 project 연결 |

두 field 모두 `build_values()` 에 닿지 않는다. repository 가 update 옆에서 그 행을 쓴다. soft delete 가
이미 따르는 규칙이다 — 바뀔 때 다른 쓰기를 끌고 오는 값은 일반 updater 에 두지 않는다. 그 전이를 할 수
있는 편집 경로는 잘못된 전이도 할 수 있다. 두 field 는 관계 연산으로 옮긴다.

### 참조하는 엔티티가 지워질 때

`purge_relation` 은 두 값을 받아야 행을 지운다. 한쪽만 알고 그 엔티티의 관계를 쓸어 내는 연산은 없다.

FK CASCADE 는 로직에 대한 보장이지 소유의 표현이 아니다. 둘 수는 있지만 다형 참조에는 걸 수 없다.

domain 같은 오래 사는 엔티티의 삭제는 lifecycle manager 가 다루고, 남은 관계 행은 거기서나 retention
sweep 이 치운다. 관계 테이블은 `RetentionCategory` 에 자기 항목을 가진다.

## 구현 계획

- 관계 타입이 Node 를 구현하게 한다. GraphQL 층이 global ID 를 양 끝 UUID 로 만들고 풀며, `node(id:)` 는
  양 끝 scope 의 read 를 묻는다.
- user ↔ role: global ID 를 양 끝으로 바꾸고, 바꾸는 mutation · REST 가 (user, role) 를 바디로 받게 한다.
  data loader · cursor · lookup · SDK 응답을 양 끝 기반으로 옮긴다.
- idle checker ↔ scope: 같은 방식으로 (scope type, scope id, idle checker) 를 받게 하고 경로의 id 를 뺀다.
  GraphQL 입력 · 응답, CLI, cursor, lookup key 를 옮긴다.
- resource group ↔ domain · project: link · unlink 를 더하고 `adminUpdateAllowed*` 를 deprecated 로 둔다.
- 관계 테이블 7개의 행 id 컬럼을 지우고 양 끝 쌍을 기본 키로 둔다. `user_roles` · `idle_checker_bindings`
  는 앞의 두 단계 뒤에 한다.
- 관계 ops(create · delete · restore · purge_relation)와 관계 선언에서 `OperationScope` 9개를 만든다.

## 결정 기록

| ID | 날짜 | 결정 | 이유 | 검토한 대안 |
| --- | --- | --- | --- | --- |
| D1 | 2026-10-20 | 관계는 양 끝 엔티티의 UUID 로만 식별한다. API 의 관계 id 는 양 끝으로 만든 global ID 이고, repository 와 권한 검사는 양 끝으로만 조회한다. | 쌍 밖의 id 는 같은 관계의 두 번째 이름이고, 그 id 로 찾은 관계는 양 끝을 다시 읽어야 권한을 물을 수 있다. | 행 id 를 Node id 로 유지 — 클라이언트가 행 id 를 저장해야 관계를 바꿀 수 있다. |
| D2 | 2026-10-20 | 관계 테이블의 행 id 컬럼을 모두 지우고 양 끝 쌍을 기본 키로 둔다. | 행 id 를 FK 로 참조하는 테이블이 없고, 다섯 테이블은 행 id 를 쓰지 않는다. 앞의 네 테이블은 원래 쌍이 기본 키였다. | 행 id 를 남기고 API 에서만 숨김 — 쓰지 않는 키가 남아 다시 API 로 나갈 수 있다. |
| D3 | 2026-10-20 | 관계의 unlink(purge) 응답은 GraphQL 에서 `purgedId`(관계 global ID)와 양 끝 UUID, DTO · REST 에서 양 끝 UUID 를 준다. 관계가 남는 연산은 관계를 돌려준다. | Relay 의 `@deleteEdge` · `@deleteRecord` 는 global ID 를 받는다. global ID 는 GraphQL 층만 만든다. | payload `id` 에 global ID — Relay store 에서 지운 관계와 같은 키가 되어 충돌한다. |
| D4 | 2026-10-20 | resource group 과 domain, project 의 연결은 link · unlink 로 다룬다. 이름 목록 통째 교체는 deprecated. | 통째 교체는 한 쌍의 권한을 따로 물을 수 없고 양 끝 UUID 로 관계를 가리키지 않는다. |  |
| D5 | 2026-10-20 | 관계 타입은 Node 를 구현한다. global ID 는 `node(id:)` 에만 쓰고, 개별 query · mutation 은 양 끝 UUID 를 받는다. `node(id:)` 는 양 끝 scope 모두의 read 를 묻는다. | 양 끝으로 만든 global ID 로 id 만 가지고 다시 읽을 수 있어 Node 계약을 지킨다. global ID 가 양 끝을 모두 담으므로 양쪽 권한을 묻는다. | 관계 타입을 Node 가 아닌 타입으로 두고 `id` 를 두지 않음 — Relay store 가 관계를 정규화하지 못하고 unlink 응답으로 edge 를 지울 수 없다. |

## 열린 질문

| ID | 질문 |
| --- | --- |
| Q1 | 참조가 사라진 관계 행을 어떻게 찾을지. 참조가 다형(`entity_type`, `entity_id`)이라 anti-join 은 그 타입이   어느 테이블에 사는지 알아야 한다. `virtual_scopes` 가 이미 살아 있는 엔티티를 `(scope_type, scope_id)` 로   색인하므로 맞대 볼 수 있지만, virtual scope 도입 전에 만든 행은 scope 가 없을 수 있어 살아 있는 엔티티의   관계를 끊긴 것으로 읽게 된다. |
| Q2 | `sgroups_for_*` 셋을 다형 테이블 하나로 합칠지 — 합치면 `query_allowed_sgroups` 가 쿼리 하나가 되고   새 종류의 scope 가 값이 된다. |
| Q3 | resource group ↔ keypair 관계를 user 로 바꿀지 — BA-8459 로 넘어갔다. |
| Q4 | domain 관리자가 resource group 을 편집할 권한은 무엇이 주는지. 관계에서 나오지 않으므로 role 이나   grant 로 적어야 한다. |

## 참고

- `src/ai/backend/manager/models/specs/KNOWLEDGE.md` — write spec 선택 기준
- `src/ai/backend/manager/actions/KNOWLEDGE.md` — v2 액션 모양
- `src/ai/backend/manager/api/gql/AGENTS.md` — mutation payload 와 관계 타입 규칙
- BEP-1069 (Entity Lifecycle Deletion) — soft delete Mixin 과 `purge_status`
- BEP-1008 · BEP-1012 (RBAC)
- BEP-1076 (Project Membership)

<!-- generated by hejo bep render from hejo report bep/entity-relation-operations (sha256 5727eea6e1c5011e); edit the source, or hejo bep import after editing here -->
