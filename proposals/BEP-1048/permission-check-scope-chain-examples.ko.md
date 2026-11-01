# BEP-1048 권한 검사 예시

> [BEP-1048](../BEP-1048-RBAC-entity-relationship-model.md) 상세 문서

이 문서는 `check_permission_with_scope_chain()` 이 `association_scopes_entities` 테이블을 따라가며 권한을 결정하는 구체적인 예시를 제공한다. 각 시나리오는 정확히 필요한 DB 레코드와 두 계층 검사(자체 scope 직접 일치 + CTE scope chain 순회)가 어떻게 결과를 내는지 보여 준다.

## 관례

- **ase** = `association_scopes_entities` 테이블
- **permissions** = `permissions` 테이블 (column: `role_id`, `scope_type`, `scope_id`, `entity_type`, `operation`)
- **user_roles** = `user_roles` 테이블 (column: `user_id`, `role_id`)
- 가독성을 위해 UUID 를 줄인다(예: `user-A`, `vf-1`, `proj-1`)
- CTE 순회는 `AUTO` edge 만 따른다. `REF` edge 는 chain 을 끝낸다

---

## 1. VFolder 공유 (ref edge + 엔티티 scope 권한)

### 상황

사용자 A 가 Project P 의 VFolder X 를 own 한다. 사용자 A 가 사용자 B 를 VFolder X 에 쓰기 권한으로 초대한다.

### DB 레코드

**ase (own, auto edge):**

| scope_type | scope_id | entity_type | entity_id | relation_type |
|------------|----------|-------------|-----------|---------------|
| project    | proj-1   | vfolder     | vf-1      | auto          |
| user       | user-A   | vfolder     | vf-1      | auto          |

**ase (공유, ref edge):**

| scope_type | scope_id | entity_type | entity_id | relation_type |
|------------|----------|-------------|-----------|---------------|
| user       | user-B   | vfolder     | vf-1      | ref           |

**user_roles:**

| user_id | role_id    |
|---------|------------|
| user-A  | role-owner |
| user-B  | role-member|

**permissions (사용자 B 의 role, project scope vfolder 권한 없음):**

사용자 B 는 Project P 의 멤버가 아니고 project scope vfolder 권한이 없다. 사용자 B 가 가진 vfolder 접근은 초대 때 생성한 엔티티 scope 부여뿐이다.

**permissions (사용자 B 의 role, 초대 때 부여한 엔티티 scope):**

| role_id     | scope_type | scope_id | entity_type | operation |
|-------------|------------|----------|-------------|-----------|
| role-member | vfolder    | vf-1     | vfolder     | read      |
| role-member | vfolder    | vf-1     | vfolder     | write     |

### 검사: 사용자 B 가 VFolder X 를 읽는다

`check_permission_with_scope_chain(user_id=user-B, target=VFolder:vf-1, op=read)`

**1계층: 자체 scope 직접 일치:**
```sql
-- Does User B have a permission where scope = VFolder:vf-1?
permissions WHERE scope_type='vfolder' AND scope_id='vf-1'
  AND entity_type='vfolder' AND operation='read'
  AND role_id IN (User B's active roles)
→ MATCH (entity-scope read grant)
```
결과: **허용**.

### 검사: 사용자 B 가 VFolder X 를 삭제한다

`check_permission_with_scope_chain(user_id=user-B, target=VFolder:vf-1, op=delete)`

**1계층: 자체 scope 직접 일치:**
```sql
permissions WHERE scope_type='vfolder' AND scope_id='vf-1'
  AND entity_type='vfolder' AND operation='delete'
→ NO MATCH (no entity-scope delete grant)
```

**2계층: CTE scope chain 순회:**
```sql
-- Base: find AUTO edges for VFolder:vf-1
ase WHERE entity_type='vfolder' AND entity_id='vf-1' AND relation_type='auto'
→ (project, proj-1), (user, user-A)
-- NOTE: (user, user-B) edge is REF → excluded from CTE

-- Check permissions at discovered scopes
permissions WHERE (scope_type, scope_id) IN {(project, proj-1), (user, user-A)}
  AND entity_type='vfolder' AND operation='delete'
  AND role_id IN (User B's active roles)
→ NO MATCH (User B has no permissions at project or user-A scope)
```
결과: **거부**. 사용자 B 에는 project scope 권한이 없고 ref edge 는 CTE 에서 제외된다. 명시적으로 부여한 엔티티 scope 권한(읽기, 쓰기)만 적용된다.

### 검사: 사용자 A 가 VFolder X 를 읽는다

`check_permission_with_scope_chain(user_id=user-A, target=VFolder:vf-1, op=read)`

**1계층: 자체 scope 직접 일치:** user-A 에 대한 엔티티 scope 권한이 없다. 일치 없음.

**2계층: CTE scope chain 순회:**
```
Base: AUTO edges for VFolder:vf-1 → (project, proj-1), (user, user-A)
Recurse from (user, user-A): find AUTO edges where entity=user:user-A
  → (domain, dom-1) [if Domain ━auto━► User edge exists]
Recurse from (project, proj-1): find AUTO edges where entity=project:proj-1
  → (domain, dom-1) [Domain ━auto━► Project]

Check permissions at {(project, proj-1), (user, user-A), (domain, dom-1)}
  for role-owner, entity_type=vfolder, op=read
→ MATCH
```
결과: **허용**.

---

## 2. 세션과 kernel 정보 접근 (auto edge chain)

### 상황

사용자 C 가 Project P 에 세션을 생성한다. 세션에는 ResourceGroup rg-1 의 Agent ag-1 에 할당한 kernel 2개가 있다. 사용자 C 가 kernel 상세를 읽으려 한다.

### DB 레코드

**ase (scope 계층, auto edge):**

| scope_type | scope_id | entity_type | entity_id | relation_type |
|------------|----------|-------------|-----------|---------------|
| domain     | dom-1    | project     | proj-1    | auto          |
| project    | proj-1   | session     | sess-1    | auto          |
| user       | user-C   | session     | sess-1    | auto          |

**ase (세션 구성, auto edge):**

| scope_type | scope_id | entity_type | entity_id | relation_type |
|------------|----------|-------------|-----------|---------------|
| session    | sess-1   | kernel      | kern-1    | auto          |
| session    | sess-1   | kernel      | kern-2    | auto          |

**ase (resource group 구성, auto edge):**

| scope_type | scope_id | entity_type | entity_id | relation_type |
|------------|----------|-------------|-----------|---------------|
| resource_group | rg-1 | agent       | ag-1      | auto          |
| agent      | ag-1     | kernel      | kern-1    | auto          |
| agent      | ag-1     | kernel      | kern-2    | auto          |

**ase (세션 ref edge, 읽기 전용 참조):**

| scope_type | scope_id | entity_type | entity_id | relation_type |
|------------|----------|-------------|-----------|---------------|
| session    | sess-1   | agent       | ag-1      | ref           |
| session    | sess-1   | resource_group | rg-1   | ref           |

### 검사: 사용자 C 가 Kernel kern-1 을 읽는다

`check_permission_with_scope_chain(user_id=user-C, target=Kernel:kern-1, op=read)`

**1계층: 자체 scope 직접 일치:** `kernel:kern-1` 을 scope 로 하는 권한이 없다. 일치 없음.

**2계층: CTE scope chain 순회:**
```
Base: AUTO edges for Kernel:kern-1
  → (session, sess-1), (agent, ag-1)

Recurse from (session, sess-1): AUTO edges where entity=session:sess-1
  → (project, proj-1), (user, user-C)

Recurse from (agent, ag-1): AUTO edges where entity=agent:ag-1
  → (resource_group, rg-1)

Recurse from (project, proj-1): AUTO edges where entity=project:proj-1
  → (domain, dom-1)

Recurse from (user, user-C): AUTO edges where entity=user:user-C
  → (domain, dom-1)  [deduplicated by UNION]

Recurse from (resource_group, rg-1): AUTO edges where entity=resource_group:rg-1
  → (domain, dom-1) or (project, proj-1)  [if such edges exist]

Final scope set: {(session, sess-1), (agent, ag-1), (project, proj-1),
                  (user, user-C), (resource_group, rg-1), (domain, dom-1)}

Check permissions at these scopes for user-C's roles,
  entity_type=kernel, op=read
→ MATCH at (project, proj-1) if role has kernel:read at project scope
```
결과: **허용**. 권한이 `Project ━auto━► Session ━auto━► Kernel` 을 통해 흐른다.

### 검사: 사용자 C 가 Agent 경로로 Kernel kern-1 을 읽는다

CTE 는 두 경로를 동시에 찾는다.
- **Session 경로**: `Kernel ← Session ← Project ← Domain`
- **Agent 경로**: `Kernel ← Agent ← ResourceGroup`

두 경로 모두 auto edge 로 이뤄지므로 scope 집합에 기여한다. 찾은 scope 중 **어느 하나**에서 사용자 C 의 role 이 `kernel:read` 를 가지면 검사를 통과한다. CTE 의 union 은 겹치는 scope(예: 두 경로에서 모두 이르는 `domain:dom-1`)를 중복 제거한다.

### 검사: 사용자 C 가 Kernel kern-1 에 쓴다 (쓰기 권한 없음)

`check_permission_with_scope_chain(user_id=user-C, target=Kernel:kern-1, op=write)`

**1계층: 자체 scope 직접 일치:** 일치 없음.

**2계층: CTE scope chain 순회:** 위와 같은 scope 집합이지만:
```
Check permissions for entity_type=kernel, op=write
→ NO MATCH (User C's role only has kernel:read, not kernel:write)
```
결과: **거부**.

---

## 3. Domain/Project, ResourceGroup, Agent 접근 (auto edge chain)

### 상황

Domain D 에 Project P 가 있다. ResourceGroup RG-1 을 Domain D 와 Project P 에 배정한다. Agent ag-1 은 RG-1 에 속한다. 사용자 세 명이 있다.
- User M: domain manager (`agent:read` 를 domain scope 에 가짐)
- User PA: project admin (`agent:read` 를 project scope 에 가짐)
- User PM: project member (`agent:read` 권한 없음)

### DB 레코드

**ase (domain 계층, auto edge):**

| scope_type | scope_id | entity_type | entity_id | relation_type |
|------------|----------|-------------|-----------|---------------|
| domain     | dom-D    | project     | proj-P    | auto          |
| domain     | dom-D    | user        | user-M    | auto          |
| domain     | dom-D    | user        | user-PA   | auto          |
| domain     | dom-D    | user        | user-PM   | auto          |

**ase (resource group 배정, auto edge):**

| scope_type | scope_id | entity_type    | entity_id | relation_type |
|------------|----------|----------------|-----------|---------------|
| domain     | dom-D    | resource_group | rg-1      | auto          |
| project    | proj-P   | resource_group | rg-1      | auto          |

**ase (agent 구성, auto edge):**

| scope_type | scope_id | entity_type | entity_id | relation_type |
|------------|----------|-------------|-----------|---------------|
| resource_group | rg-1 | agent       | ag-1      | auto          |

**user_roles:**

| user_id | role_id       |
|---------|---------------|
| user-M  | role-dm       |
| user-PA | role-proj-adm |
| user-PM | role-proj-mem |

**permissions:**

| role_id       | scope_type | scope_id | entity_type | operation |
|---------------|------------|----------|-------------|-----------|
| role-dm       | domain     | dom-D    | agent       | read      |
| role-dm       | domain     | dom-D    | resource_group | read   |
| role-proj-adm | project    | proj-P   | agent       | read      |
| role-proj-adm | project    | proj-P   | resource_group | read   |
| role-proj-mem | project    | proj-P   | resource_group | read   |

참고: `role-proj-mem` 은 `resource_group:read` 를 가지지만 `agent:read` 는 **없다**. `resource_group:read` 가 있다고 `agent:read` 가 따라오지 않는다. entity 타입마다 명시적인 권한 부여가 필요하다.

### 검사: User M 이 Agent ag-1 을 조회한다 (domain manager)

`check_permission_with_scope_chain(user_id=user-M, target=Agent:ag-1, op=read)`

**1계층: 자체 scope 직접 일치:** `agent:ag-1` 을 scope 로 하는 권한이 없다. 일치 없음.

**2계층: CTE scope chain 순회:**
```
Base: AUTO edges for Agent:ag-1
  → (resource_group, rg-1)

Recurse from (resource_group, rg-1): AUTO edges where entity=resource_group:rg-1
  → (domain, dom-D), (project, proj-P)

Recurse from (domain, dom-D): no AUTO parent → stop

Final scope set: {(resource_group, rg-1), (domain, dom-D), (project, proj-P)}

Check permissions at these scopes for user-M's roles,
  entity_type=agent, op=read
→ MATCH at (domain, dom-D) — role-dm has agent:read at domain scope
```
결과: **허용**.

### 검사: User PA 가 Agent ag-1 을 조회한다 (project admin)

`check_permission_with_scope_chain(user_id=user-PA, target=Agent:ag-1, op=read)`

**1계층: 자체 scope 직접 일치:** 일치 없음.

**2계층: CTE scope chain 순회:**
```
Same scope set: {(resource_group, rg-1), (domain, dom-D), (project, proj-P)}

Check permissions for user-PA's roles,
  entity_type=agent, op=read
→ MATCH at (project, proj-P) — role-proj-adm has agent:read at project scope
```
결과: **허용**. 권한이 `Project ━auto━► ResourceGroup ━auto━► Agent` 를 통해 흐른다.

### 검사: User PM 이 Agent ag-1 을 조회한다 (project member)

`check_permission_with_scope_chain(user_id=user-PM, target=Agent:ag-1, op=read)`

**1계층: 자체 scope 직접 일치:** 일치 없음.

**2계층: CTE scope chain 순회:**
```
Same scope set: {(resource_group, rg-1), (domain, dom-D), (project, proj-P)}

Check permissions for user-PM's roles,
  entity_type=agent, op=read
→ NO MATCH (role-proj-mem has resource_group:read but not agent:read)
```
결과: **거부**. auto edge 경로는 있지만 User PM 의 role 은 접근 가능한 scope 어디에도 `agent:read` 를 포함하지 않는다. `resource_group:read` 권한은 `agent:read` 로 이어지지 않는다.

### 검사: User M 이 Agent ag-1 을 조회한다 (resource group 이 domain 에 배정되지 않음)

`(domain, dom-D) ━auto━► (resource_group, rg-1)` edge 가 없으면(예: RG-1 을 다른 domain 에 배정) 다음과 같다.

```
Base: AUTO edges for Agent:ag-1
  → (resource_group, rg-1)

Recurse from (resource_group, rg-1): AUTO edges where entity=resource_group:rg-1
  → (domain, dom-X)  [different domain]

Final scope set: {(resource_group, rg-1), (domain, dom-X)}

Check permissions for user-M's roles at these scopes
→ NO MATCH (user-M has permissions at dom-D, not dom-X)
```
결과: **거부**. scope chain 이 User M 에게 권한이 있는 scope 에 이르지 않는다.

### 여러 project 로의 ResourceGroup 배정

ResourceGroup RG-1 은 여러 project 에 배정될 수 있다.

**ase (추가 project 배정):**

| scope_type | scope_id | entity_type    | entity_id | relation_type |
|------------|----------|----------------|-----------|---------------|
| project    | proj-P   | resource_group | rg-1      | auto          |
| project    | proj-Q   | resource_group | rg-1      | auto          |

이제 Agent ag-1 의 CTE 는 다음을 찾는다.
```
Base: (resource_group, rg-1)
Recurse: (domain, dom-D), (project, proj-P), (project, proj-Q)
```

project scope 에서 `agent:read` 를 가진 proj-P 의 project admin 은 ag-1 에 접근할 수 있지만, 배정되지 않은 proj-R 의 project admin 은 접근할 수 없다.
