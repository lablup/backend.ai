# v2 연결 유형(to-many) 중첩 필터 표준화

## 관련 이슈

- JIRA: BA-6819 (이 BEP)
- Epic: BA-6818 — v2 연결 유형(to-many) 중첩 필터 표준화

## 목표

**v2 연결 유형(to-many) 중첩 필터**(부모 엔티티를 관련 자식 묶음의 조건으로 조회하는 필터)에 하나의 규칙을 정하고, 먼저 `DeploymentFilter.replicas`(deployment 를 그 route/replica 조건으로 조회)에 적용한다.

이 BEP 는 세 가지와 첫 적용 대상을 정한다.

| 결정 | 결과 |
|----------|---------|
| 필터 모양 | 명시적인 `some` / `every` / `none` 매칭 방식(새 표준) |
| 재사용 추상화 | 공유 `make_correlated_exists` 빌더 + 엔티티별 바인딩(rbac 방식 이름) |
| 의미 문서화 | 각 매칭 방식 필드가 설명에 정확한 집합 의미를 밝힌다 |

v2 filter DTO 는 GraphQL, REST v2, 클라이언트 SDK, CLI 가 함께 사용하는 기준 값이다. 앞으로 이 계층들에 추가하는 모든 to-many 중첩 필터는 이 규칙을 따른다.

## 동기

지금 `DeploymentFilter` 로는 "replica 가 하나 이상 실행 중인 deployment"나 "healthy replica 가 없는 deployment" 같은 운영 질문을 조회할 수 없다. 기존 `status` 필터는 deployment 수명 주기(`READY`)만 반영하고 route 의 실제 `running` / `healthy` / `active` 상태는 반영하지 않는다. 이 공백이 Epic BA-6818 을 시작하게 했다.

더 넓게 보면 두 엔티티가 이미 to-many 중첩 필터를 구현했지만, 공유 규칙 없이 각자 모양을 직접 생성했다. 표준이 없으면 새 필터마다 모양, 의미, 질의 구성을 다시 정하게 되고, 엔티티마다 API 표면이 달라진다.

## 현재 설계와 범위

영역마다 **✅ 이미 있는 것**과 **➕ 추가할 것**을 나눈다.

### 필터 모양 (DTO/GQL 표면)

두 선례는 모두 **암묵적 some(implicit-some)** 을 사용한다. `{Relation}NestedFilter` 임베드를 하나 두는 것만으로 "자식이 하나 이상 일치한다"는 뜻이다.

| | 항목 |
|---|---|
| ✅ | image → alias: `ImageV2Filter.alias`(implicit-some), 설명 "at least one alias matching" |
| ✅ | rbac role → user/scope: `RoleConditions.by_assigned_user_id` / `by_mapped_scope`(implicit-some) |
| ✅ | `some`/`every`/`none` 매칭 방식: 코드베이스에서 **사용처 0** |
| ➕ | 명시적 some/every/none 을 새 표준으로 정의(결정 1) |
| ➕ | deployment → replicas: 새 중첩 필터. deployment 를 replica/route 상태로 조회(이 BEP 의 첫 적용) |

> 기존 implicit-some 선례 두 개를 새 모양으로 옮기는 일은 후속 작업이다(마이그레이션 참고).

### 질의 구성 (adapter/조건 변환)

| | 항목 |
|---|---|
| ✅ | image → alias: `sa.exists` 가 각 `ImageConditions.by_alias_*` 에 미리 들어간다(잎마다 EXISTS 하나, 단일 조건). **합성할 수 없다** |
| ✅ | rbac role → user: `RoleConditions.by_assigned_user_id(list[QueryCondition])`. 자식 조건 **목록**을 상관 EXISTS 하나로 접는다. **합성할 수 있다** |
| ➕ | 공유 `make_correlated_exists` 빌더 + 엔티티 바인딩 `DeploymentConditions.by_replica_exists`(결정 2) |
| ➕ | some/every/none → EXISTS/NOT EXISTS 매핑을 adapter 에 두고 `negate_conditions` 를 재사용 |

### 공유 기반 (모두 이미 있고 재사용한다)

| | 항목 |
|---|---|
| ✅ | `models/clauses.py` — `QueryCondition = Callable[[], ColumnElement[bool]]` |
| ✅ | `repositories/base/filter_adapter.py` — `convert_string_filter` / `convert_uuid_filter`(잎 필터 DTO → 조건) |
| ✅ | `repositories/base/utils.py` — `combine_conditions_and` / `combine_conditions_or` / `negate_conditions` |
| ✅ | `repositories/base/querier.py` — 조건 목록을 `WHERE` 절로 접는다 |

## 제안하는 규칙

### 선례 (다른 시스템의 규칙)

to-many relation 필터에는 GraphQL 생태계 전체에 사실상 표준이 있다. 이 BEP 는 그것을 따른다.

| 시스템 | 모양 | 빈 컬렉션에서의 `every` | "일치 없음"의 표현 |
|--------|-------|-----------------------------|-----------------------|
| Prisma | `some` / `every` / `none` | true(문서화됨. 직관에 어긋난다는 지적도 있다) | `none: {…}`. 존재는 `some: {}` / `none: {}` 로 표현 |
| 이 BEP(2026-09-21 개정) | `exists` + `some` / `every` / `none` | true | `none: {…}`. 존재는 `exists` 로 표현 |
| PostGraphile(connection-filter) | `some` / `every` / `none` | true | `none: {…}` |

- **`some`/`every`/`none` 세 가지는 이미 널리 사용되는 Prisma/PostGraphile 규칙과 같다.** 결정 1 은 이것을 채택한다.
- "`every` 는 빈 컬렉션에서 true" 동작도 둘이 같다(Prisma 는 이를 명시적으로 문서화한다).
- **"자식이 있고 모두 일치한다"**(빈 컬렉션이 아닌 `every`)는 둘 다 전용 축약 없이 **`some: {}` + `every: {…}`** 를 조합해 표현한다. 이 BEP 는 그 관용구를 채택한 뒤, 축약을 추가하는 대신 명시적 `exists` 필드로 대체했다(결정 1, 개정).

### 결정 1 — 모양: 명시적 `some` / `every` / `none`

to-many 중첩 필터는 relation 마다 두는 중첩 필터 모델로 표현한다. 매칭 방식 필드를 최대 셋 두고, 각 필드는 자식 엔티티 자신의 필터를 담는다.

```
{Relation}NestedFilter:
  some:  {Child}Filter   # the parent has at least one child matching all conditions
  every: {Child}Filter   # every child of the parent matches all conditions
  none:  {Child}Filter   # the parent has no child matching all conditions
```

- 세 필드는 모두 선택이다. 둘 이상 주면 **AND** 로 묶는다.
- **이름 규칙:** 부모 필터는 이 모델을 **복수형 to-many relation** 이름의 필드로 임베드한다(`DeploymentFilter.replicas`, `ImageFilter.aliases` …). 기존 implicit-some 필드가 이미 단수 이름을 차지하고 있으면 그 단수 필드를 deprecated 로 두고 복수형 필드를 새로 추가한다(마이그레이션 참고).

**집합 의미**(설명이 밝혀야 하는 계약):

| 매칭 방식 | 뜻 | 변환 |
|---------------|---------|-------------|
| `some` | 자식이 하나 이상 일치 | `EXISTS (child where P)` |
| `every` | 모든 자식이 일치 | `NOT EXISTS (child where NOT P)` |
| `none` | 일치하는 자식이 없음 | `NOT EXISTS (child where P)` |

**빈 컬렉션 주의: 문서화해야 한다.** `every` 는 자식이 **하나도 없는** 부모에서도 true 다. 자식이 0개면 "모든 자식이 P 를 만족한다"가 자명하게 성립한다. 이를 어기는 자식이 없기 때문이다(빈 집합에서 `NOT EXISTS (child that violates P)` 는 true 다). 따라서 replica 가 0개인 deployment 는 `replicas.every` 에 일치한다. 표준 동작이지만 사용자가 놀라므로 필드 설명에 이 사실을 밝혀야 한다. "자식이 있고 모두 일치한다"가 필요하면 `exists: true` 와 `every: {…}` 를 함께 사용한다.

**빈 조건 규칙(2026-09-21 개정, BA-8063).** 조건을 담지 않은 매칭 방식은 `EmptyMatchConditionError`(400)로 거부한다. `some: {}` 는 자식을 제한하는 대신 자식이 있는지를 물었고, 모든 필드가 비어 있는 row 필터도 같은 뜻으로 줄어들었으므로, 필터하려던 요청이 "자식이 하나라도 있는가"로 처리됐다. 이제 존재 여부는 이름으로 지정한다.

| 묻는 것 | 필드 |
|-----|-------|
| 자식이 하나 이상 있는가 | `exists: true` |
| 자식이 없는가 | `exists: false` |
| P 에 일치하는 자식이 하나 이상인가 | `some: {P}` |
| 모든 자식이 P 에 일치하는가 | `every: {P}` |
| P 에 일치하는 자식이 없는가 | `none: {P}` |

`exists` 는 row 필터가 아니라 `Boolean` 이므로 같은 방식으로 퇴화할 수 없다.

**검토한 트레이드오프.** 지금까지의 관례는 implicit-some(임베드만 두면 `some`)이다. 이를 유지하면 선례 둘과 같아지고 새 개념도 늘지 않지만, `every` 나 `none` 을 전혀 표현할 수 없다. BA-6818 을 이끈 운영 질의("모든 replica 가 healthy", "실행 중인 replica 없음")가 바로 그것이다. 그래서 **기각했다**. 명시적 매칭 방식은 중첩이 한 단계 늘고 implicit-some 선례 둘과 달라지지만(마이그레이션에서 해소), 실제 질의 요구를 포함하는 최소 모양이고 읽을 때 뜻이 분명하다.

### 결정 2 — 재사용 추상화: 공유 `make_correlated_exists` + 엔티티별 바인딩

상관 `EXISTS` 를 생성하는 로직은 **공유 빌더 하나**에 두고, 각 엔티티는 빌더를 자기 relation 에 바인딩해 **도메인 이름의 팩토리**로 노출한다. 엔티티가 사용하는 이름은 rbac 의 `by_assigned_user_id(list[QueryCondition])` 모양을 잇는다.

```
# shared builder (models/condition_utils.py)
make_correlated_exists(child_row, correlate_row, join_predicate)
    -> Callable[[list[QueryCondition]], QueryCondition]

# entity binding (models/endpoint/conditions.py)
DeploymentConditions.by_replica_exists = make_correlated_exists(
    child_row=RoutingRow,
    correlate_row=EndpointRow,
    join_predicate=RoutingRow.endpoint == EndpointRow.id,
)
# call: by_replica_exists(route_conditions)
#   -> EXISTS ( SELECT 1 FROM routings
#               WHERE routings.endpoint = endpoints.id AND <route_conditions...> )
```

- **둘 다 두는 이유:** 공유 빌더는 상관 `EXISTS` 구성(상관 서브쿼리, join, `.correlate()`)을 한곳에 두어 엔티티가 다시 직접 생성하지 않게 한다. 동시에 엔티티 코드는 `by_replica_exists` 같은 도메인 이름으로 노출해 가독성과 발견성을 유지한다.
- 빌더는 긍정 `EXISTS` 만 생성한다. `some`/`every`/`none` → `EXISTS`/`NOT EXISTS` 매핑은 **adapter** 의 책임이고 기존 `negate_conditions` 를 재사용한다.
- 자식 조건은 엔티티의 기존 잎 필터 변환기에서 온다. deployment 는 `_convert_replica_filter` 이고, 이미 `RoutingRow` 위의 `RouteConditions.*` 를 생성한다.
- 선례 둘(image 는 잎마다 `EXISTS` 를 넣고, rbac 는 목록을 접는다)도 나중에 옮길 때 이 공유 빌더로 모인다.

### 결정 3 — 의미 문서화 표준

각 매칭 방식 필드의 설명은 정확한 집합 의미를 밝힌다. `ImageV2Filter.alias`("at least one alias matching")가 세운 선례를 넓힌다.

| 필드 | 요구하는 설명 형식 |
|-------|---------------------------|
| `exists` | "Matches parents that have at least one {child} when true, and parents with none when false. Says nothing about what the {child} rows hold." |
| `some` | "Matches parents with **at least one** {child} satisfying all conditions." |
| `every` | "Matches parents where **every** {child} satisfies all conditions (**also true when the parent has no {child}**)." |
| `none` | "Matches parents with **no** {child} satisfying all conditions." |

`every` 설명에는 "also true when there are no {child}" 구절을 넣어 스키마만 보고도 이 동작을 알 수 있게 한다.

## 첫 적용 — `DeploymentFilter.replicas`

위 규칙을 deployment 를 route 로 조회하는 데 적용한다. deployment replica 에는 기존 implicit-some 필드가 없으므로 처음부터 새 모양으로 시작한다.

**선행 조건: `ReplicaFilter` 에 `health_status` 를 추가한다.** 동기가 된 "healthy replica 없음" 질의는 route health 로 조회해야 하는데, 지금 `ReplicaFilter` 는 `status` 와 `traffic_status` 만 노출하고 `health_status` 필드가 없다(`RouteFilter` 와 다르다). 그래서 이 적용은 `ReplicaFilter` 에 `health_status` 도 추가한다(`RouteFilter.health_status` 를 따름). 조건 팩토리 `RouteConditions.by_health_statuses` 는 이미 있어 재사용한다.

| 계층 | 변경 |
|-------|--------|
| DTO(`common/dto/manager/v2/deployment/request.py`) | `ReplicaNestedFilter { some, every, none: ReplicaFilter }` 를 추가하고 `DeploymentFilter.replicas` 로 임베드한다. `ReplicaFilter` 에 `health_status` 를 추가해(`RouteFilter` 를 따름) "healthy" 질의를 표현할 수 있게 한다. |
| GQL(`api/gql/deployment/types/deployment.py`) | `ReplicaNestedFilterGQL`(스키마 이름 `ReplicaNestedFilter`)과 `DeploymentFilter.replicas` 필드를 `added_version = NEXT_RELEASE_VERSION` 으로 추가하고 결정 3 의 설명을 붙인다. replica 필터 GQL 타입에도 대응하는 `health_status` 필드를 추가한다. |
| Adapter(`api/adapters/deployment/adapter.py`, `_convert_deployment_filter`) | `replicas` 분기를 추가한다. 안쪽 route 조건은 **`_convert_replica_filter` 를 재사용**해 생성한다(`health_status` 를 기존 `RouteConditions.by_health_statuses` 로 변환하도록 확장). 그다음 `some` → `by_replica_exists(preds)`, `none` → `negate_conditions([by_replica_exists(preds)])`, `every` → `negate_conditions([by_replica_exists(per-child-negated preds)])` 로 매핑한다. |
| Conditions(`models/condition_utils.py`, `models/endpoint/conditions.py`) | 공유 `make_correlated_exists(child_row, correlate_row, join_predicate)` 빌더와, `RoutingRow.endpoint == EndpointRow.id`(FK `routings.endpoint → endpoints.id`)에 바인딩한 `DeploymentConditions.by_replica_exists` 를 추가한다. |

join 키는 기존 FK 인 `RoutingRow.endpoint` → `endpoints.id` 다. `EXISTS` 는 `EndpointRow` 에 상관되며 rbac 의 `.correlate(RoleRow)` 를 따른다.

REST v2 와 클라이언트 SDK 는 DTO 를 공유하므로 필터별 작업 없이 새 필드를 함께 사용한다. **CLI 는 그렇지 않다.** deployment 검색 명령은 정해진 Click 옵션 묶음에서 `DeploymentFilter` 를 생성한다(`client/cli/v2/{admin,my}/deployment.py`). 그래서 CLI 에 `replicas` 를 노출하려면 전용 `--replicas-*` 옵션 묶음을 추가해야 한다. 이 CLI 작업도 이 적용 범위에 든다.

## 마이그레이션 / 호환성

- **새 필드는 additive 다.** `DeploymentFilter.replicas` 는 새 선택 필드이므로 GraphQL 스키마나 기존 클라이언트에 대한 breaking change 가 없다.
- **기존 implicit-some 선례(image → alias, rbac)는 유지하고 `@deprecated` 만 표시한다.** 지금 모양이 `some` 과 의미상 같으므로 계속 동작한다. 새 `some/every/none` 필터는 그 옆에 **별도 필드로** 추가한다(additive, non-breaking). GraphQL 은 같은 이름의 필드를 둘 수 없으므로 **새 필드 이름은 달라야 한다.** 복수형 to-many relation 이름을 사용하고 deprecated 필드는 원래 이름을 유지한다. 예를 들어 image 는 deprecated `alias` 옆에 새 `aliases: { some, every, none }` 를 추가한다. deployment 는 처음부터 `replicas` 로 시작한다. 이 엔티티별 이관은 이 BEP 범위 밖이고 BA-6818 아래 후속 Story 로 추적한다.
- **DB 마이그레이션은 없다.** 이 규칙은 질의 구성에만 해당하고 스키마를 변경하지 않는다.

## 구현 계획

1. **규칙 + 첫 적용(이 BEP 범위, Story 하나)**
   - `ReplicaFilter`(DTO + GQL)에 `health_status` 를 추가해 "healthy" 질의를 표현할 수 있게 한다
   - `ReplicaNestedFilter` DTO + `DeploymentFilter.replicas` 임베드
   - 공유 `make_correlated_exists` 빌더 + `DeploymentConditions.by_replica_exists`
   - adapter `replicas` 분기(some/every/none 매핑). `_convert_replica_filter` 를 확장해 `health_status` 를 기존 `RouteConditions.by_health_statuses` 로 변환
   - GQL `ReplicaNestedFilterGQL` + 필드(결정 3 설명)
   - deployment 검색 명령에 CLI `--replicas-*` 옵션 묶음
   - 테스트: `some` / `every`(replica 0개에서 true 인 경우 포함) / `none`, 그리고 최상위 `AND` / `OR` / `NOT` 과의 조합
2. **기존 선례 이관(BA-6818 아래 후속 Story)**
   - image → alias 와 rbac 의 implicit-some 필드에 `@deprecated` 표시
   - 다른(복수형 relation) 이름으로 새 `some/every/none` 필드 추가
   - 각 엔티티의 상관 `EXISTS` 를 공유 `make_correlated_exists` 빌더로 모은다

## 결정 기록

| 날짜 | 결정 | 근거 |
|------|----------|-----------|
| 2026-07-10 | 모양 = 명시적 `some`/`every`/`none` | implicit-some 은 `every`/`none`(BA-6818 을 이끈 운영 질의)을 표현할 수 없다. 널리 사용되는 Prisma/PostGraphile 규칙과 같다 |
| 2026-07-10 | 빈 컬렉션이 아닌 `every` 는 `some: {}` + `every: {…}` 로 표현하고 전용 축약을 두지 않는다 | Prisma 와 PostGraphile 이 모두 이 관용구를 노출한다 |
| 2026-09-21 | 존재 여부는 명시적 `exists: Boolean` 으로 옮기고, 조건 없는 매칭 방식은 400(BA-8063) | `some: {}` 는 다른 질문을 빈 값에 담았고, 아무것도 설정하지 않은 row 필터가 우연히 그 값에 도달했다. 조건 없는 `every` 는 잘못된 SQL 을 생성했다 |
| 2026-07-10 | 공유 `make_correlated_exists(child_row, correlate_row, join_predicate)` 빌더 + 엔티티별 바인딩(`by_replica_exists`) | 상관 `EXISTS` 구성을 한곳에 두면서 엔티티마다 도메인 이름을 노출한다 |
| 2026-07-10 | some/every/none → EXISTS/NOT EXISTS 매핑은 adapter 에 둔다 | 조건 계층에는 엔티티마다 기호 하나만 늘리고 `negate_conditions` 를 재사용한다 |
| 2026-07-10 | 새 `some/every/none` 필드 이름 = **복수형 to-many relation**(예: `aliases`, `replicas`). 기존 단수 implicit-some 필드는 `@deprecated` 만 표시 | GraphQL 은 중복 필드 이름을 금지하고, 하위 호환을 유지하며, 이름을 일관되게 한다 |

## 열린 질문

- **이관 순서와 시점:** 이름 규칙은 정해졌으므로(복수형), 남은 것은 각 implicit-some 필드를 그 엔티티의 v2 GA 대비 어느 시점에 deprecated 로 표시하는가뿐이다. 후속 Story 마다 정한다.

## 참고

- [BEP-1021: GQL StringFilter Enhancement](BEP-1021-gql-string-filter-enhancement.md) — 필터 규칙 선례 BEP(같은 저자, 같은 영역)
- [BEP-1038: ImageV2 GQL Implementation](BEP-1038-image-v2-gql-implementation.md) — image → alias 중첩 필터 선례
- [BEP-1008: RBAC](BEP-1008-RBAC.md) — role → user/scope 중첩 필터 선례
- [Prisma — Relation queries (some/every/none)](https://www.prisma.io/docs/orm/prisma-client/queries/relation-queries) — to-many 필터의 사실상 표준. 빈 컬렉션에서의 `every`
- [PostGraphile connection-filter — Filtering](https://www.graphile.org/postgraphile/filtering/) — one-to-many `some`/`every`/`none`
