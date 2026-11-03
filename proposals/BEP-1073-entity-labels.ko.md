# 엔티티 레이블

## 관련 이슈

- JIRA: **BA-7466**(이 BEP)
- Epic: **BA-7465**: 엔티티 레이블. scope 를 가로질러 `key=value` 레이블을 붙이고 그것으로 필터링한다
- 출처: **BA-7326**(기능 요청). session 과 agent 에 tag 붙이기

## 목표

어느 엔티티에나 붙일 수 있는 **일반화된 `key=value` 레이블**, **레이블 자체에 대한 검색**, **레이블로 엔티티를 고르는 필터**를 정의한다.

이 BEP 는 네 가지를 정한다.

| 결정 | 결과 |
|----------|---------|
| 레이블 정체성 | 레이블은 map entry 다. 대상 하나에서 key 하나가 값 하나를 가지고, 같은 key 를 다시 쓰면 값이 교체된다 |
| 구조 | 테이블 하나. 레이블이 붙는 엔티티는 polymorphic 참조이고 foreign key 가 아니다 |
| 필터 | [BEP-1060](BEP-1060-v2-connection-type-nested-filters.md) 의 `some` / `every` / `none` 중첩 필터. 레이블을 붙일 수 있는 모든 엔티티가 `LabelFilter` 하나를 공유한다 |
| API 표면 | put 하나, remove 하나, search 하나. `audit_log` 의 필터와 page/order 모양을 재사용한다 |

레이블은 어느 엔티티에나 붙는다. `labels` 필터는 **session, deployment, vfolder, agent** 에 먼저 연결한다.

레이블은 독립된 기능이다. RBAC 를 확장하지 않고 RBAC 가 레이블을 정의하지도 않는다. 레이블은 붙은 엔티티의 field 로 취급하므로 모든 권한 검사는 그 엔티티를 거친다. [접근 제어](#access-control)를 참고한다.

## 동기

엔티티에 주석을 달거나 묶는 일반적인 방법이 없다. schema 에 그 의도가 기록되지 않으므로 운영자는 "어느 session 이 `prod` 환경에 속하는가", "`infra` team 이 어느 vfolder 를 소유하는가", "어느 agent 가 `gpu-reserved` 표시를 가지는가"에 응답할 수 없다.

## 현재 설계와 범위

영역마다 **✅ 이미 있는 것**과 **➕ 추가할 것**을 나눈다.

### 저장

| | 항목 |
|---|---|
| ✅ | `audit_logs`: foreign key 대신 polymorphic `(entity_type, entity_id)` 짝으로 임의의 엔티티를 참조하는 선례 |
| ➕ | 레이블 테이블 |

### 타입 체계

| | 항목 |
|---|---|
| ✅ | `common/data/entity/types.py`: polymorphic 엔티티 참조인 `EntityType` 과 `EntityID` |

### 필터링

| | 항목 |
|---|---|
| ✅ | `make_correlated_exists`(`models/condition_utils.py`): 상관 `EXISTS` 생성기 |
| ✅ | `BaseFilterAdapter.convert_string_filter`: `StringFilter` → `QueryCondition` |
| ✅ | `some` / `every` / `none` 중첩 필터 규약(BEP-1060) |
| ✅ | 엔티티 필터마다 `AND` / `OR` / `NOT` 조합(예: `SessionFilter`) |
| ➕ | `LabelFilter`, 그리고 연결한 엔티티마다 필터 DTO 의 `labels` 중첩 field |

### API

| | 항목 |
|---|---|
| ✅ | `audit_log`: 재사용할 필터와 page/order 모양. `AND`/`OR`/`NOT` 조합, cursor 와 offset pagination |
| ➕ | 레이블 검색, 그리고 추가와 제거 |

## 제안 설계

### 1. 레이블 정체성

레이블은 **map entry** 다. Kubernetes label 처럼 대상 하나에서 key 하나가 값 하나를 가진다. 대상이 이미 가진 key 를 다시 쓰면 row 를 하나 더 추가하지 않고 값을 교체한다. 그래서 쓰기가 add 가 아니라 put 이다.

`UNIQUE (entity_type, entity_id, key)` 가 이것을 강제한다. 한 이름 아래 여러 값을 두려는 호출자는 값을 key 에 적거나(`team-infra`, `team-ml`), 스스로 해석하는 구분자 문자열로 value 에 적는다.

### 2. 구조와 관계

테이블 하나(`entity_labels`)에 엔티티 하나에 put 한 key 마다 row 하나를 둔다. 엔티티, key, 값이다.

엔티티는 `audit_logs` 가 이미 사용하는 모양의 polymorphic `(entity_type, entity_id)` 참조다. DB 수준에서는 타입이 없고 함께 오는 타입으로 구분한다. 레이블을 붙일 수 있는 테이블은 column 이나 제약이 늘지 않고, schema 가 어떤 엔티티 타입도 알 필요가 없으므로 어디에나 레이블을 붙일 수 있다.

엔티티를 purge 하면 기존 엔티티 purger 가 그 레이블을 삭제하므로 끊어진 참조는 도달 가능한 상태가 아니다.

column 수준 정의, index, 제약은 구현 PR 에서 정한다.

### 3. 레이블 검색

레이블 검색은 "어느 레이블이 사용되는가"에 응답한다. "어느 엔티티가 이 레이블을 가지는가"에 응답하는 [레이블로 엔티티 필터링](#4-filtering-entities-by-label)와 다르다. 둘 다 필요하고 어느 쪽도 다른 쪽을 대신하지 않는다.

**진입점은 `search_labels` 하나**이고 `key`, `value`, `entity_type`, `entity_id` 로 필터링한다. 요청한 사용자가 읽을 수 있는 엔티티의 레이블을 반환한다. admin 이 더 많이 보는 것은 RBAC 가 더 많은 엔티티를 주기 때문이지 진입점이 둘이기 때문이 아니다. 레이블은 엔티티의 field 이고, field 는 scoped 표면과 별도인 admin 표면을 갖지 않는다.

**GraphQL 과 REST v2 양쪽**에 노출한다. SDK 와 CLI 는 REST 로 API 에 접근한다.

필터와 page/order 모양은 `audit_log` 에서 가져온다. 필터의 `AND` / `OR` / `NOT` 조합과, 입력의 cursor 및 offset pagination 이다.

<a id="4-filtering-entities-by-label"></a>
### 4. 레이블로 엔티티 필터링

공유 v2 필터 DTO 가 GraphQL, REST v2, SDK, CLI 를 한 번에 구동한다.

```graphql
input LabelFilter {
  key: StringFilter
  value: StringFilter
}

input LabelNestedFilter {
  some:  LabelFilter   # at least one label matches
  every: LabelFilter   # all labels match (vacuously true when unlabeled)
  none:  LabelFilter   # no label matches
}

input SessionFilter {
  # ...existing fields
  labels: LabelNestedFilter
}
```

**`LabelFilter` 는 레이블 row 하나씩 맞춘다.** 그래서 같은 블록 안의 `key` 와 `value` 는 *같은* 레이블을 제한한다. `some: {key: {equals: "env"}, value: {equals: "prod"}}` 는 `env=prod` 를 가진 엔티티를 고른다. key 가 `env` 인 레이블과 값이 `prod` 인 레이블을 따로 가진 엔티티가 아니다.

서로 다른 레이블의 논리곱은 엔티티 필터가 이미 가진 `AND` 를 사용한다. v2 엔티티 필터는 모두 `AND` 를 가진다.

```graphql
# sessions carrying both env=prod and team=infra
AND: [
  { labels: { some: { key: {equals: "env"},  value: {equals: "prod"} } } },
  { labels: { some: { key: {equals: "team"}, value: {equals: "infra"} } } }
]
```

`some` / `every` / `none` 의 집합 의미는 BEP-1060 이 정한 것을 따른다. 각 field 는 description 에서 그것을 다시 적는다.

key 와 value 는 **대소문자를 구분해** 비교한다. `env=Prod` 와 `env=prod` 는 하나가 아니라 두 레이블이다. `StringFilter` 의 `i_*` field 가 개별 비교를 그 구분에서 제외한다.

계약 두 가지가 구현을 묶는다.

- **쿼리 모양.** 엔티티 row 에 대해 레이블 테이블로 상관 `EXISTS` 를 걸고, key 와 value 조건을 그 안에서 적용한다.
- **가시성.** 레이블은 그 엔티티를 읽을 수 있을 때 정확히 읽을 수 있으므로, 엔티티 자체의 필터링이 이미 레이블 필터가 맞출 수 있는 범위를 제한한다. 더 필요한 것이 없고, `none:` 절이 요청한 사용자가 볼 수 없는 레이블의 oracle 이 될 수도 없다.

### 5. 쓰기 동작

감사 기록은 시스템이 쓰고 API 로만 읽는다. 레이블은 사용자가 쓴다. 따라서 이 동작에는 대응하는 `audit_log` 가 없다.

| 동작 | 모양 |
|-----------|-------|
| Put | 엔티티와 `key=value` 를 지정한다. key 를 설정하고 그 key 가 가지고 있던 값을 교체한다 |
| Remove | 레이블 자체의 id 를 지정한다. 검색에서 읽는다 |

Put 은 insert 가 아니라 upsert 다. key 하나가 값 하나를 가지므로, 엔티티가 이미 가진 key 를 지정하는 것은 충돌이 아니라 호출자가 원하는 값을 다시 말한다. `updated_at` 은 값이 마지막으로 교체된 시각을 기록한다.

Remove 는 엔티티와 key 가 아니라 row 를 지정한다. 그래서 레이블 row 에 대한 모든 동작이 다른 field 종류의 이름을 붙이는 방식과 같다. 그 row 가 어느 엔티티의 것인지는 삭제를 실행하기 전에 row 에서 읽는다.

레이블을 정의하는 일과 어딘가에 붙이는 일은 나뉘지 않는다. 아무것에도 붙지 않은 레이블에는 이 BEP 가 부여하는 의미가 없고, 미리 선언한 레이블만 쓰도록 제한하는 규칙도 없다. 둘을 나누면 호출과 상태만 늘고 기능은 늘지 않는다.

### 6. 배치

| 계층 | 위치 |
|-------|----------|
| DTO | `common/dto/manager/v2/label/` |
| GraphQL | `api/gql/label/` |
| REST v2 | `api/rest/v2/label/` |
| adapter | `api/adapters/label/` |
| service | `services/label/` |
| repository | `repositories/label/` |
| SDK | `client/v2/domains_v2/label.py` |
| CLI | `client/cli/v2/label/` |

<a id="access-control"></a>
### 접근 제어

**레이블은 붙은 엔티티의 field 로 취급**하고, 자기 권한을 가진 주체로 보지 않는다. 따라서 모든 검사가 그 엔티티를 거치고, 이미 있는 것에 대한 평범한 RBAC 검사다.

| 동작 | 검사 대상 |
|--------|-----------------|
| 추가와 제거 | 엔티티에 대한 쓰기 |
| 엔티티의 레이블 읽기 | 엔티티에 대한 읽기 |
| 레이블 검색 | 레이블을 가진 엔티티. 엔티티를 읽을 수 있으면 레이블을 반환한다 |

따라 나오는 것이 둘이다. 레이블은 자기 권한 표면을 추가하지 않는다. 레이블은 엔티티가 노출하는 범위를 넓히지도 좁히지도 않으므로, 레이블을 추가하거나 제거할 때 다시 계산할 것이 없다. 그리고 레이블 가시성에는 자기 규칙이 필요 없다. 요청한 사용자가 읽을 수 없는 레이블은 그 엔티티를 읽을 수 없을 때 생긴다. 엔티티 자체의 필터링이 이미 그것을 제외한다.

## 이전과 호환

- **추가만 한다(additive only).** 새 테이블 하나와 연결한 엔티티마다 선택적 필터 field 하나. 기존 쿼리의 모양은 바뀌지 않고 기존 테이블에 column 이 늘지 않는다.
- **백필 없음.** 레이블은 빈 상태로 시작한다.

## 구현 계획

| 단계 | 작업 |
|-------|------|
| 1 | 도메인 타입과 레이블 테이블, alembic revision |
| 2 | repository 와 service 계층: 추가, 제거, 검색 |
| 3 | DTO, adapter, GraphQL, REST v2 표면 |
| 4 | session, deployment, vfolder, agent 의 `LabelFilter` 연결 |
| 5 | SDK 와 CLI |
| 6 | 계층 전반의 test, 그리고 실행 중인 서버에 대한 실제 검증 |

처음 네 엔티티를 넘어서는 엔티티는 필터 연결만 하면 된다.

## 열린 질문

남은 것이 없다.

## 참고

- [BEP-1060: Standardizing v2 Connection-Type Nested Filters](BEP-1060-v2-connection-type-nested-filters.md): `some`/`every`/`none` 의미와 `make_correlated_exists`
- [BEP-1069: Entity Lifecycle Deletion Management](BEP-1069-entity-lifecycle-deletion.md): 의존 row 로의 purge 전파
- `audit_log` v2 표면: `api/rest/v2/audit_log/`, `api/gql/audit_log/`, `common/dto/manager/v2/audit_log/`
