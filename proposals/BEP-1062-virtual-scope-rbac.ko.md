# 가상 스코프 RBAC 소유 모델

## 관련 이슈

- Epic **BA-6567**: 가상 스코프 도입, 일반화된 RBAC 소유 계층
- 이 BEP: **BA-6568**
- 이미 완료된 하위 이슈(이 BEP 의 구현 근거):
  - **BA-6603**: 가상 스코프 도메인 타입 정의 (#12419)
  - **BA-6604**: 가상 스코프 DB 테이블(ORM + Alembic) (#12503)
  - **BA-6605**: 가상 스코프 DB ops (#12528)
  - **BA-6606**: 가상 스코프 체인 권한 검사 함수 (#12814)
  - **BA-6863**: 가상 스코프 권한 해석용 커버링 인덱스 (#12817)
- 상위(여기서 확장한다): **[BEP-1048](BEP-1048-RBAC-entity-relationship-model.md)** 는 scope-entity relation 모델이다. 함께 보기: BEP-1008, BEP-1012(RBAC), BEP-1056(virtual_scope 참조)

## 1. 목표

RBAC 권한 해석의 **재귀 순회를 재귀 없는 2-hop 소유 모델로 대체한다.** 소유를 `scope → virtual_scope → entity` 로 표현하고 그 위에서 권한을 해석한다.

**지금 변경하는 이유.** 지금의 해석은 `association_scopes_entities` 를 **재귀 CTE** 로 순회하며(domain → project → user) 상위 스코프의 권한을 아래로 상속한다. 이 재귀에는 문제가 둘 있다.

1. 무언가 깨졌을 때 **어느 hop 에서 권한이 유출됐는지 추적하기 어렵다.**
2. 상속을 미리 구체화하면 `scope × entity` 규모의 **연결이 폭증한다.**

**가상 스코프는 두 문제를 한 번에 해결하는 중간 계층이다.** 소유자마다 소유를 허브 노드(가상 스코프) 하나에 모으고, 두 개의 범위가 정해진 관계로 나눈다.

- `scope_bindings`: 어느 스코프가 어느 VS 를 통해 권한을 행사하는가(scope → VS)
- `entity_memberships`: 어느 엔티티가 어느 VS 에 속하는가(VS → entity)

그 결과:

- 해석이 **경로 하나, hop 하나**로 끝난다. 재귀가 사라진다.
- 연결 수가 `scope × entity` 에서 `scope × VS` + `VS × entity` 로 준다.
- BEP-1048 의 `auto`/`ref` 간선 구분이 **더는 필요 없다**(3.(e), 3.(h)).

**갖춘 것과 갖추지 않은 것.** 가상 스코프는 **테이블, 타입, DB ops, 해석 함수를 코드에 갖췄지만 아직 어떤 운영 경로에도 연결되지 않았다(호출하는 곳이 없다).** 이 BEP 는 그 구현 표면을 기록하고(2절, 영역별 현재 상태와 범위), 남은 설계를 채우며(3~4절, 구현 설계와 마이그레이션), 나머지를 후속 이슈로 나눈다.

## 2. 영역별 현재 상태와 범위

영역마다 **✅ 이미 있는 것 / ➕ 추가할 것**을 나눈다.

### 2.1 데이터 모델 (DB 테이블)

BA-6604(테이블)와 BA-6863(커버링 인덱스)로 스키마가 완성된다.

| | 항목 |
|---|---|
| ✅ | `virtual_scopes`: 소유 스코프마다 허브 노드 하나. `id` PK, `UNIQUE(scope_type, scope_id)`, `created_at`. **스코프마다 VS 가 정확히 하나** |
| ✅ | `scope_bindings`: 들어오는 방향 `scope → VS`. PK `(virtual_scope_id, scope_type, scope_id)`, `permission_cap`(nullable = 상한 없음), FK → `virtual_scopes` `ON DELETE CASCADE` |
| ✅ | `entity_memberships`: 나가는 방향 `VS → entity`. PK `(virtual_scope_id, entity_type, entity_id)`, `permission_cap`(nullable), FK `ON DELETE CASCADE` |
| ✅ | 커버링 인덱스(BA-6863): `ix_entity_memberships_entity (entity_type, entity_id) INCLUDE (virtual_scope_id, permission_cap)`, `ix_scope_bindings_virtual_scope (virtual_scope_id) INCLUDE (scope_type, scope_id, permission_cap)`, `ix_permissions_scope_entity ... INCLUDE (permission, role_id)`. 정방향과 역방향 join 을 인덱스만으로 처리한다 |
| ➕ | 마이그레이션 규칙: `association_scopes_entities`(auto/ref)와 엔티티 단위 `permissions` 를 세 테이블로 옮긴다(4절, 마이그레이션과 호환성) |

### 2.2 도메인 타입

| | 항목 |
|---|---|
| ✅ | `common/entity/types.py`: `ScopeType`/`EntityType` 은 **열린 `NewType(str)`** 이다. `ScopeRef`/`EntityRef`. 고정 enum 을 늘리지 않고 어떤 소유자 타입도 받는다(핵심 설계) |
| ✅ | `common/data/permission/virtual_scope.py`: `VirtualScopeData`, `ScopeBindingData`, `EntityMembershipData`(frozen) |
| ✅ | `common/identifier/virtual_scope.py`: `VirtualScopeID = NewType(UUID)` |
| ✅ | `manager/data/permission/virtual_scope.py`: `VirtualScopePermissionCheckKey(user_id, entity)` |

### 2.3 DB write ops (BA-6605)

`RBACWriteOps`/`RBACOpsProvider`(`repositories/ops/rbac/provider.py`)는 CRUD 를 모두 갖췄다. **그러나 아래 가상 스코프 write 는 모두 호출하는 곳이 없다(아직 연결되지 않았다).**

| | 항목 |
|---|---|
| ✅ | 생성/삭제: `create_scope`/`bulk_create_scopes`/`delete_scope`/`batch_delete_scopes`. 실제 소유자 row 와 그 VS 노드를 함께 생성한다. VS 가 없으면 `_resolve_virtual_scope_id` 가 `VirtualScopeNotFound(500)` 를 발생시킨다 |
| ✅ | 스코프 바인딩: `bind_scope(scope, owner, permission_cap)` / `unbind_scope` |
| ✅ | 엔티티 멤버십: `add_entity_members(scope, entities, permission_cap)` / `remove_entity_members`. 초대도 이 경로로 표현한다(3.(e)) |
| ✅ | (가상 스코프 아님) `add_users_to_scope`(스코프에 사용자를 등재하고 자동 배정 역할을 부여한다), `bulk_create_scoped`: `association_scopes_entities` 에 기록한다. **지금 실제로 연결된 유일한 ops** |
| ➕ | **RBAC ops provider 의 grant 메서드**가 VS write(자기 scope_binding 생성 포함)를 맡고, domain/project/user/resource_group 동작이 그 provider/ops 를 사용하게 한다(연결 전 → 연결) |
| ➕ | `add_users_to_scope` 이름을 하는 일(등재 + 역할 자동 배정)에 맞게 변경한다(2.7, 후속) |

### 2.4 권한 해석 (읽기, BA-6606)

`repositories/permission_controller/db_source/db_source.py` 에 있다. **그러나 호출하는 곳은 단위 테스트뿐이다. repository 에 노출되지 않았고 어떤 validator 에도 연결되지 않았다(아직 연결되지 않았다).**

| | 항목 |
|---|---|
| ✅ | `resolve_effective_permissions_via_virtual_scope(keys)`: `entity → entity_memberships → scope_bindings → scope → permissions → roles → user_roles` 를 **경로 하나, hop 하나**로 join 한다. `granted & scope_cap & entity_cap`(nullable = 상한 없음)으로 자르고 OR 로 합친다. `(user_id, entity_type)` 묶음마다 질의 하나 |
| ✅ | `check_permission_via_virtual_scope` / `check_bulk_permission_via_virtual_scope`: bitwise 검사 |
| ✅ | (지금 사용 중) 재귀 스코프 순회: `_build_scope_walk_cte(..., recursive=True)` 가 스코프 계층을 재귀 순회한다 |
| ✅ | 해석은 scope_binding 을 거쳐 스코프에 도달한다. 소유(소유자가 자기 엔티티를 보는 것)는 **자기 scope_binding** 을 거친다. 이는 엔티티를 프로비저닝할 때 VS 노드와 함께 기록한다(3.(c)) |
| ➕ | 역방향 조회: `scope → 읽을 수 있는 엔티티`, `entity → 권한을 주는 스코프`(RBAC 화면, 3.(b)) |
| ➕ | validator 에 연결하고 재귀 스코프 순회를 제거한다(3.(d), 4절의 마이그레이션) |

### 2.5 적용 토글

| | 항목 |
|---|---|
| ✅ | `config/unified.py` 의 `RBACConfig.enforcement_enabled`(기본 True). action validator 셋만 읽는다 |
| ✅ | 활성화하면 validator 가 재귀 스코프 순회를 실행하고, 비활성화하면 일찍 반환한다(legacy 경로). **재귀 스코프 순회만 제어하며 가상 스코프와는 무관하다** |
| ➕ | **가상 스코프 해석용 설정을 따로 둔다**(예: `rbac.resolution_backend`). `enforcement_enabled` 를 재사용하지 않는다. 적용 여부와 해석 전략은 다른 축이다. **이 설정과 기존 재귀 순회는 임시 스위치이고 전환 뒤 둘 다 제거한다**(4절, 마이그레이션과 호환성) |

### 2.6 가능/불가능 relation 모델

| | 항목 |
|---|---|
| ✅ | `common/data/permission/scope_entity_combinations.py` 의 `VALID_SCOPE_ENTITY_COMBINATIONS`(직접 작성한 dict) → GQL `rbac_scope_entity_combinations` |
| ✅ | RBAC action 마다 `permission_scope()`(스코프)와 `required_permission()`(엔티티, 연산)을 선언한다. `get_permission_matrix`(service.py:412)가 이를 순회해 `scope→entity→operation` 표를 만들고 GQL `rbac_permission_matrix` 로 노출한다 |
| ➕ | **action 에서 도출한 전용 dataclass 를 정의**하고 필드로 노출하며 그것을 통해 접근한 뒤 `VALID_SCOPE_ENTITY_COMBINATIONS` 상수를 삭제한다. dataclass 는 (a) 스코프 도달 가능성(스코프 action)과 (b) 엔티티별 연산(단일 엔티티 action)을 **읽어 합친다**(3.(f)) |
| ➕ | 선행 조건: 모든 action 을 RBAC action 3종으로 정규화한다(2.7) |

### 2.7 action 정규화

| | 항목 |
|---|---|
| ✅ | RBAC action/validator 3종이 있다: `ScopeActionValidator`, `SingleEntityActionValidator`, `BulkActionValidator`(+ `BaseRBACAction.permission_scope()`) |
| ➕ | 모든 domain action 을 이 3종으로만 정규화한다. 그러면 권한 검사가 세 갈래(스코프 대상 / 단일 엔티티 대상 / bulk 대상)로 줄고 가능/불가능 도출(2.6)이 완성된다 |

## 3. 구현 설계

**전체 흐름.** 소유자 엔티티를 만들면 그 VS 노드와 **자기 scope_binding**(소유 스코프 → 자기 VS)을 함께 생성한다(Scope Creator). 소유자가 가진 자식 엔티티는 그 VS 의 멤버가 된다(소유). 계층이나 연관 relation 이 만들어지면 그 시점에 상위나 연관 스코프를 하위 VS 에 바인딩한다. 다른 스코프와 공유하려면 같은 엔티티를 `permission_cap` 과 함께 대상의 VS 멤버로 추가한다(초대). 해석은 `entity → VS → 바인딩된 스코프 → 그 스코프의 역할 권한`을 **경로 하나, hop 하나**로 계산한다.

### (a) 가상 스코프 그래프와 바인딩 시나리오

```
scope(self)     ─(self scope_binding, at creation)─┐
scope(parent)   ─(hierarchy binding, at creation)──┼─► virtual_scope(owner S) ─(entity_memberships)─► entity X, Y
scope(assoc.)   ─(association binding)─────────────┘
```

- 소유 스코프 S 마다 VS 가 하나다(`UNIQUE(scope_type, scope_id)`).
- 엔티티는 **직접 연결된 VS 에만** 붙는다. 자기 소유자의 VS(소유)와 초대받은 쪽의 VS(초대)다. VS 에서 VS 로 전파하지 않는다(재귀 없음).
- `scope_binding` 을 생성할 때:
  - **self**: 스코프 생성 시 자기 VS 에 바인딩한다(소유자가 자기 엔티티를 본다).
  - **hierarchy**: domain 아래 project 를 만들면 `domain → VS_project`, user 를 만들면 `domain → VS_user`, project 에 user 를 등재하면 `project → VS_user`.
  - **association**: 자원 그룹의 agent 는 `VS_resource_group` 의 멤버다. 연관 project 를 `project → VS_resource_group` 로 바인딩하면 **그 project 가 agent 를 읽을 수 있다.**
- `entity_membership` 을 생성할 때:
  - **ownership/enrollment**: 엔티티가 소유자의 VS 멤버가 된다. **project 에 속한 user 도 entity_membership 으로 표현한다.** user 엔티티는 `VS_project` 의 멤버다.
  - **invitation**: 특정 엔티티를 `permission_cap` 과 함께 초대받은 쪽의 VS 에 추가한다(3.(e)).

### (b) 재귀 없는 단일 경로 해석 (정방향/역방향)

해석은 **경로 하나**이고 self/hierarchy/association/invitation 분기가 없다.

```
entity → entity_memberships → scope_bindings → scope → permissions → roles → user_roles
```

- self scope_binding 덕분에 소유(소유자가 자기 엔티티를 보는 것)도 이 경로 하나를 지난다. 예외가 없다.
- RBAC 화면의 양방향 조회도 같은 두 테이블 join 이다(인덱스는 2.1 에 이미 있다).

| 방향 | 경로 | 용도 |
|-----------|------|-----|
| 정방향 | `scope → scope_bindings → VS → entity_memberships → entities` | "이 스코프가 볼 수 있는 엔티티" |
| 역방향 | `entity → entity_memberships → VS → scope_bindings → scopes` | "이 엔티티에 권한을 주는 스코프" |

**재귀가 없다.** 모든 경로가 두세 테이블의 단순 join 이고 CTE 재귀가 없다.

**소유/가시성과 권한은 다른 축이다.** VS 그래프(`scope_bindings` + `entity_memberships`)는 "누가 무엇을 own 하고 볼 수 있는가"를 정한다(project 에 속한 user 도 여기다). `roles`/`permissions` 는 "어떤 연산이 허용되는가"를 정한다. 해석은 VS 그래프를 거쳐 스코프에 도달한 뒤 그 스코프의 역할 권한을 적용한다. **둘을 합친다.** 그래서 등재 기록(association)과 권한 부여(`user_roles`)는 겹치지 않고 각자 역할이 있다.

### (c) Scope Creator: 생성 시 VS + 자기 scope_binding

- **생성:** 소유자 엔티티(domain/project/user/resource_group/…)를 만들면 `create_scope` 가 실제 row + VS 노드 + **자기 scope_binding**(소유 스코프 → 자기 VS)을 함께 생성한다(get-or-create 이므로 반복 호출해도 안전하다).
- **자기 scope_binding 이 필요한 이유:** 해석은 scope_bindings 를 따라간다(3.(b)). 소유자가 자기 VS 의 엔티티를 보려면 그 VS 에 바인딩이 하나 필요하다. 생성 시 이 row 하나를 추가하면 소유도 계층, 연관, 초대와 **같은 경로 하나**로 해석된다. (질의에 소유자 전용 분기를 추가하는 안보다 낫다.)
- **삭제:** `delete_scope` 가 VS 노드를 삭제하고 FK `ON DELETE CASCADE` 가 그 바인딩과 멤버십을 삭제한다.
- **불변 조건:** 모든 소유 스코프에 VS 가 있다(없으면 `_resolve_virtual_scope_id` 가 500 을 발생시킨다).
- **연결 지점:** 엔티티 write ops 가 어떤 엔티티를 만들든 한 단계로 VS 노드, 자기 entity_membership, 자기 scope_binding 을 프로비저닝하고 제거할 때 함께 정리한다. domain 코드는 VS 테이블을 직접 건드리지 않는다.

### (d) 재귀 없이 계층 표현

재귀 제거가 이 BEP 의 목표이므로 domain→project→user 상속은 **재귀가 아니라 생성 시점 바인딩**으로 표현한다.

- **relation 이 만들어질 때** 계층 바인딩을 생성한다. domain→project 생성, domain→user 생성, project→user 등재.
- 그러면 하위 엔티티는 `entity → 하위 VS → 상위 스코프 바인딩`으로 상위 스코프 권한에 **여전히 hop 하나**로 도달한다.
- 허브가 연결 수를 제한하므로 상속을 미리 구체화해도 바인딩이 대략 `scope × VS` 규모로 유지된다.

### (e) 연관과 초대: 멤버십으로 통일

| 연결 종류 | 뜻 | 저장 | permission_cap |
|-----------|---------|---------|----------------|
| **연관(association)** - 소유 | 소유자가 가진 자식 | 자기 소유 VS 의 `entity_memberships` | 없음(상한 없음) |
| **초대(invitation)** - 공유 | 특정 대상에게 특정 엔티티 접근을 부여 | **대상의 VS** 의 `entity_memberships` | 부여한 것만(예: read\|write) |

- 초대는 별도 테이블이나 직접 권한 계층이 아니다. **그 엔티티를 초대받은 쪽 VS 의 멤버로 추가하는 방식**이다.
- 수락하면 그 엔티티를 제안받은 `permission_cap` 을 담은 채 **초대받은 쪽 자기 VS** 에 추가한다. 초대받은 쪽은 자기 바인딩 경로로 그 엔티티에 도달하고, 그곳에서 할 수 있는 일은 자기 권한을 그 cap 으로 자른 값이다.
- `permission_cap` 이 "부여한 것만"을 강제한다. 대상이 자기 스코프에서 더 강한 역할을 가져도 `role permission & entity_cap` 으로 잘리므로 **권한이 유출되지 않는다**(cap 이 BEP-1048 의 권한 상승 방지를 대신한다).

### (f) 가능/불가능 = action 에서 도출한 dataclass

- "이 스코프에서 이 엔티티에 어떤 연산이 가능한가"를 **action 에서 도출한 전용 dataclass** 로 표현하고 필드로 노출한다.
- 두 가지를 **읽어 합친다:**
  1. **스코프 도달 가능성**: 스코프 action 에서 "이 스코프가 이 엔티티에 도달할 수 있는가"
  2. **엔티티별 연산**: 단일 엔티티 action 에서 "이 엔티티에 어떤 연산이 있는가"
- **합치는 이유:** 스코프 action 은 READ 만 갖는 경우가 많고 UPDATE/DELETE 는 없다. 그러나 스코프 권한을 가지면 개별 접근도 되므로, 스코프 action 에 없고 엔티티의 단일 엔티티 action 에 있는 UPDATE/DELETE 도 가능한 연산으로 **포함해야 한다.**
- 접근을 이 dataclass 로 라우팅하고 `VALID_SCOPE_ENTITY_COMBINATIONS`(직접 작성)와 별도 DB 테이블을 **둘 다** 제거한다.
- 선행 조건: 도출이 완전하려면 action 이 RBAC action 3종으로 정규화되어야 한다(2.7).

### (g) permission_cap 으로 상한 두기

- `scope_bindings.permission_cap` 와 `entity_memberships.permission_cap` 는 hop 별 상한이다(nullable = 상한 없음).
- 최종 적용 권한 = `role-granted permission & scope_cap & entity_cap`(bitwise AND). 여러 경로는 OR 로 합친다.
- `Permission` 은 `IntFlag`(READ/UPDATE/CREATE/SOFT_DELETE/HARD_DELETE)이므로 모든 검사가 bitwise 다.

### (h) auto / ref 제거

- BEP-1048 의 `RelationType`(auto/ref) 구분은 가상 스코프 모델에서 **사라진다.**
- auto(권한 위임) → 소유자 VS 멤버십 + (계층이나 연관이면) scope_binding.
- ref(읽기 전용 참조 / 초대) → 초대받은 쪽 VS 멤버십 + `permission_cap`(3.(e)).
- `association_scopes_entities.relation_type` column 과 그 분기는 마이그레이션 뒤 제거한다.
- 이것이 BEP-1048 의 위임 대 참조 축이다. **공유 맥락과는 다르다.** 초대가 담는 것은 cap 이지 relation 종류가 아니다.

### (i) 스코프 자체도 엔티티

- 스코프(project/domain/…)도 소유자 VS 에 **`entity_membership` 으로 등록된다.** 그래서 "스코프 객체 자체에 대한 접근"(예: projectA 를 볼 수 있는가)도 다른 엔티티와 **같은 경로 하나**로 해석된다. 별도 스코프 권한 개념이 없다.
- 소유 규칙은 똑같이 적용된다. projectA 는 `VS_domain` 의 멤버이고 domain 의 자기 scope_binding 이 그것에 대한 접근을 해석한다.

### (j) 클라이언트에 노출하는 API 없음

- 가상 스코프는 **클라이언트에 노출하지 않는다.** `virtual_scopes` / `scope_bindings` / `entity_memberships` 에 CRUD API 가 없다.
- 소유 엔티티 수명 주기(Scope Creator, 3.(c))와 RBAC ops provider 의 grant 메서드의 부수 효과로만 관리하는 내부 파생 구조다.

## 4. 마이그레이션 / 호환성

**방향: 재귀 스코프 순회를 재귀 없는 가상 스코프 해석으로 대체한다.** 가상 스코프 값은 모두 내부 값이므로 한 번의 백필로 옮길 수 있다.

| 단계 | 내용 |
|------|---------|
| 1. action 정규화 | 모든 domain action 을 RBAC action 3종으로 맞춘다(2.7). 검사와 도출의 선행 조건 |
| 2. Scope Creator 연결 | VS write(자기 scope_binding 포함)를 RBAC ops provider 의 grant 메서드에 두고, domain/project/user/resource_group 동작이 그 provider/ops 를 사용하게 한다(3.(c)). 생성 시 계층 바인딩(3.(d)) |
| 3. 데이터 이동 | `association_scopes_entities` 의 auto→소유자 VS 멤버십, ref→초대받은 쪽 VS 멤버십(+cap), 상위 상속→scope_binding 을 한 번에 백필한다 |
| 4. resolver 연결 | validator 를 가상 스코프 해석(경로 하나)으로 전환한다. 정방향/역방향 조회를 추가한다 |
| 5. 재귀 제거 | 재귀 CTE(`_build_scope_walk_cte`)와 재귀 순회 경로를 제거하고 `relation_type` column 을 제거한다 |
| 6. 정리 | `VALID_SCOPE_ENTITY_COMBINATIONS` 를 삭제하고 action dataclass 로 대체한다(3.(f)). `add_users_to_scope` 이름을 변경한다 |

**별도 설정(임시 스위치).** 가상 스코프 해석은 **새 설정**으로 토글하며 `enforcement_enabled` 를 재사용하지 않는다. "적용할 것인가"와 "어떤 해석 전략인가"는 다른 축이고 전환 중에 독립적으로 조정해야 한다. 이 설정은 **임시 스위치**다. 순서는 (1) 가상 스코프 구현과 연결 → (2) 백필 마이그레이션 → (3) 설정으로 한 번에 전환 → (4) 검증 뒤 재귀 순회 경로와 이 설정을 함께 제거한다. 다른 전환 대상도 같은 순서를 따른다.

**기존 동작과의 동등성.**

- 소유/가시성: association 을 소유자 VS 멤버십 + 자기 바인딩으로 옮겨도 결과가 같다.
- 공유(초대): ref 를 초대받은 쪽 VS 멤버십 + cap 으로 옮겨도 결과가 같다(cap 이 권한 상승을 차단한다).
- 상속: 재귀를 생성 시점 계층 바인딩(hop 하나)으로 대체해도 결과가 같다.

## 5. 결정 요약

| 결정 | 내용 |
|----------|---------|
| 소유 모델 | `scope → virtual_scope → entity`, 2-hop. 소유자마다 허브 VS 하나 |
| 스코프도 엔티티 | 스코프도 `entity_membership` 이므로 스코프 객체 자체 접근이 같은 경로 하나로 해석된다. 별도 스코프 권한 개념 없음 |
| 클라이언트 노출 | 가상 스코프는 내부 전용이다. **CRUD API 없음.** 소유 엔티티 수명 주기의 부수 효과로 관리한다 |
| 해석 | **재귀 없음**, 경로 하나. self/hierarchy/association/invitation 이 같은 join 이다. 정방향과 역방향이 대칭이다 |
| Scope Creator | 소유자 생성 시 VS + **자기 scope_binding** 을 만들고 삭제 시 FK CASCADE. VS write 는 RBAC ops provider 가 맡고 domain 동작이 그것을 사용한다 |
| 계층 바인딩 | relation 이 만들어질 때 바인딩한다(domain→project, domain→user, project→user) |
| 연관과 초대 | 둘 다 `entity_memberships` 다. 소유 = 소유자 VS(cap 없음) / 초대 = 대상 VS(cap = 부여분). 별도 직접 권한 계층 없음 |
| possible/impossible | action 에서 도출한 dataclass(스코프 도달 가능성 + 엔티티별 연산)를 필드로 노출한다. 직접 작성 표와 DB 테이블을 둘 다 제거한다 |
| auto/ref | 제거. 멤버십(+cap) / scope-binding 으로 대체 |
| permission_cap | hop 별 상한(bitwise AND). 경로는 OR 로 합친다. 초대의 권한 상승 방지를 강제한다 |
| 해석 토글 | `enforcement_enabled` 가 아니라 **새 설정**이다. 전환 뒤 재귀 순회와 함께 제거하는 임시 스위치 |
| action 정규화 | 모든 action 을 3종(Scope/SingleEntity/Bulk)으로 맞춘다 |

## 6. 열린 질문

없다. 주요 설계 결정은 정해졌다. 구현 수준의 세부(예: `add_users_to_scope` 이름, 바인딩이 필요한 association 목록, 전환 설정의 이름과 기본값)는 후속 이슈에서 다룬다.

## 7. 참고

- [BEP-1048: RBAC Entity Relationship Model](BEP-1048-RBAC-entity-relationship-model.md)
- [BEP-1008: RBAC](BEP-1008-RBAC.md), [BEP-1012: RBAC](BEP-1012-RBAC.md)
- [BEP-1056: Scope-Linked Metric Catalog](BEP-1056-scope-linked-metric-catalog.md)(virtual_scope RBAC 으로 읽기 권한 처리)
