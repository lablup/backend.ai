# BEP-1048 ResourceGroup 과 scope 매핑 예시

> [BEP-1048](../BEP-1048-RBAC-entity-relationship-model.md) 상세 문서

이 문서는 ResourceGroup 과 Domain/Project/User scope 매핑이 CTE scope chain 순회와 함께 어떻게 동작하는지 구체적인 예시를 제공한다. ResourceGroup 은 scope 와 **N:N auto edge** 를 사용한다. ResourceGroup 하나를 여러 scope 에 매핑할 수 있고, scope 하나가 여러 ResourceGroup 을 담을 수 있다.

## 관례

- **ase** = `association_scopes_entities` 테이블
- **permissions** = `permissions` 테이블 (column: `role_id`, `scope_type`, `scope_id`, `entity_type`, `operation`)
- **user_roles** = `user_roles` 테이블 (column: `user_id`, `role_id`)
- 가독성을 위해 UUID 를 줄인다(예: `user-A`, `rg-1`, `proj-1`)
- CTE 순회는 `AUTO` edge 만 따른다. `REF` edge 는 chain 을 끝낸다
- **RBAC 와 나열의 분리**:
  - **RBAC**: 사용자가 **질의 scope**(예: Project P1 의 `resource_group:read`)에 권한이 있는지 검증한다. scope 수준의 단순 검사이며 엔티티 매핑을 순회하지 않는다.
  - **나열**: CTE scope chain 순회로 질의 scope 에서 위로 보이는 엔티티를 모두 모은다. domain 수준 매핑이 자식 scope 로 이어지는 곳이다.

---

## 1. Domain 수준 매핑: 하위로 이어지는 가시성

### 상황

ResourceGroup RG-1 의 매핑 대상은 Domain D 다. Domain D 에는 Project P1 과 Project P2 가 있다.
User A 는 Project P1 에, User B 는 Project P2 에 속한다.
두 사용자 모두 project 별 매핑 없이 RG-1 에 접근할 수 있어야 한다.

### DB 레코드

**ase (domain 계층, auto edge):**

| scope_type | scope_id | entity_type | entity_id | relation_type |
|------------|----------|-------------|-----------|---------------|
| domain     | dom-D    | project     | proj-P1   | auto          |
| domain     | dom-D    | project     | proj-P2   | auto          |
| domain     | dom-D    | user        | user-A    | auto          |
| domain     | dom-D    | user        | user-B    | auto          |

**ase (resource group 배정, domain 수준 auto edge):**

| scope_type | scope_id | entity_type    | entity_id | relation_type |
|------------|----------|----------------|-----------|---------------|
| domain     | dom-D    | resource_group | rg-1      | auto          |

참고: RG-1 에 대한 project 별 항목은 없다. domain 수준 매핑만으로 모든 자식 scope 에 가시성을 제공한다.

**user_roles:**

| user_id | role_id       |
|---------|---------------|
| user-A  | role-p1-user  |
| user-B  | role-p2-user  |

**permissions:**

| role_id      | scope_type | scope_id | entity_type    | operation |
|--------------|------------|----------|----------------|-----------|
| role-p1-user | project    | proj-P1  | resource_group | read      |
| role-p1-user | project    | proj-P1  | session        | create    |
| role-p2-user | project    | proj-P2  | resource_group | read      |
| role-p2-user | project    | proj-P2  | session        | create    |

### 검증: User A 가 Project P1 scope 에서 ResourceGroup 을 나열한다

**1단계: RBAC 검증 (질의 scope 검사):**

User A 가 질의 scope(Project P1)에 `resource_group:read` 를 가지는가?

```sql
permissions WHERE scope_type='project' AND scope_id='proj-P1'
  AND entity_type='resource_group' AND operation='read'
  AND role_id IN (User A's active roles)
→ MATCH (role-p1-user has resource_group:read at proj-P1)
```
결과: **통과**. User A 는 Project P1 scope 에서 ResourceGroup 을 나열할 권한이 있다.

**2단계: 나열 (CTE scope chain 순회):**

질의 scope 에서 위로 scope chain 을 생성하고 각 수준의 RG 를 모두 모은다.

```sql
-- Scope chain: (project, proj-P1) → (domain, dom-D)
-- Find RGs mapped at each scope in the chain:

ase WHERE scope_type='project' AND scope_id='proj-P1'
  AND entity_type='resource_group' AND relation_type='auto'
→ (none)

ase WHERE scope_type='domain' AND scope_id='dom-D'
  AND entity_type='resource_group' AND relation_type='auto'
→ rg-1

Result = {rg-1}
```

결과: **{rg-1}**. RG-1 은 project 수준 항목이 없어도 domain 수준 매핑으로 User A 에게 보인다.

### 검증: User B 가 Project P2 scope 에서 ResourceGroup 을 나열한다

**1단계: RBAC:** `proj-P2` 에 `resource_group:read`? → **통과**.

**2단계: 나열:**
```
Scope chain: (project, proj-P2) → (domain, dom-D)

At (project, proj-P2): (none)
At (domain, dom-D):    rg-1

Result = {rg-1}
```

결과: **{rg-1}**. 같은 domain 수준 매핑이 domain 안의 모든 project 로 이어진다.

---

## 2. Project 수준 매핑: scope 로 한정된 가시성

### 상황

ResourceGroup RG-2 의 매핑 대상은 Project P1 뿐이다(Domain D 는 아니다).
User A(Project P1 소속)는 RG-2 를 봐야 한다. User B(Project P2 소속)는 보면 안 된다.

### DB 레코드

**ase (resource group 배정, project 수준만):**

| scope_type | scope_id | entity_type    | entity_id | relation_type |
|------------|----------|----------------|-----------|---------------|
| project    | proj-P1  | resource_group | rg-2      | auto          |

**permissions:**

| role_id      | scope_type | scope_id | entity_type    | operation |
|--------------|------------|----------|----------------|-----------|
| role-p1-user | project    | proj-P1  | resource_group | read      |
| role-p2-user | project    | proj-P2  | resource_group | read      |

### 검증: User A 가 Project P1 scope 에서 ResourceGroup 을 나열한다

**1단계: RBAC:** `proj-P1` 에 `resource_group:read`? → **통과**.

**2단계: 나열:**
```
Scope chain: (project, proj-P1) → (domain, dom-D)

At (project, proj-P1): rg-2
At (domain, dom-D):    (none)

Result = {rg-2}
```
결과: **{rg-2}**. User A 는 project 수준 매핑으로 RG-2 를 본다.

### 검증: User B 가 Project P2 scope 에서 ResourceGroup 을 나열한다

**1단계: RBAC:** `proj-P2` 에 `resource_group:read`? → **통과**.

**2단계: 나열:**
```
Scope chain: (project, proj-P2) → (domain, dom-D)

At (project, proj-P2): (none)
At (domain, dom-D):    (none)

Result = {}
```
결과: **{}**. RG-2 의 매핑 대상에 Project P2 와 Domain D 가 없다. User B 는 볼 수 없다.

---

## 3. Union 동작: Domain 과 Project 매핑 혼합

### 상황

- RG-A 의 매핑 대상은 Domain D 다(domain 수준, 모든 project 접근 가능)
- RG-B 의 매핑 대상은 Project P1 뿐이다
- RG-C 의 매핑 대상은 Project P2 뿐이다
- User A(Project P1 소속)는 RG-A 와 RG-B 를 봐야 한다
- User B(Project P2 소속)는 RG-A 와 RG-C 를 봐야 한다

### DB 레코드

**ase (resource group 배정):**

| scope_type | scope_id | entity_type    | entity_id | relation_type |
|------------|----------|----------------|-----------|---------------|
| domain     | dom-D    | resource_group | rg-A      | auto          |
| project    | proj-P1  | resource_group | rg-B      | auto          |
| project    | proj-P2  | resource_group | rg-C      | auto          |

참고: RG-A 는 domain 수준 항목만 있다. project 별 row 를 생성할 필요가 없다. CTE scope chain 순회가 domain 수준 매핑을 자식 scope 로 자연스럽게 잇는다.

### 나열: Project P1 에서 User A 가 접근할 수 있는 ResourceGroup

**1단계: RBAC:** `proj-P1` 에 `resource_group:read`? → **통과**.

**2단계: 나열:**
```
Scope chain: (project, proj-P1) → (domain, dom-D)

At (project, proj-P1): rg-B
At (domain, dom-D):    rg-A

Result = {rg-A, rg-B}
```

### 나열: Project P2 에서 User B 가 접근할 수 있는 ResourceGroup

**1단계: RBAC:** `proj-P2` 에 `resource_group:read`? → **통과**.

**2단계: 나열:**
```
Scope chain: (project, proj-P2) → (domain, dom-D)

At (project, proj-P2): rg-C
At (domain, dom-D):    rg-A

Result = {rg-A, rg-C}
```

현재 `query_allowed_sgroups()` 동작과 같다.
```
User's RGs = (domain RGs) ∪ (project RGs) ∪ (user RGs)
```

---

## 4. N:N 매핑: ResourceGroup 하나, domain 여럿

### 상황

ResourceGroup RG-shared 는 Domain D1 과 Domain D2 양쪽에 매핑된 cross-domain resource pool 이다. Domain D1 admin 은 자기 domain scope 에서 RG 를 나열하고 RG-shared 를 본다.

### DB 레코드

**ase (resource group, 여러 domain 매핑):**

| scope_type | scope_id | entity_type    | entity_id  | relation_type |
|------------|----------|----------------|------------|---------------|
| domain     | dom-D1   | resource_group | rg-shared  | auto          |
| domain     | dom-D2   | resource_group | rg-shared  | auto          |

### 검증: Domain D1 admin 이 ResourceGroup 을 나열한다

**1단계: RBAC:** `dom-D1` 에 `resource_group:read`? → **통과**.

**2단계: 나열:**
```
Scope chain: (domain, dom-D1) → (global)

At (domain, dom-D1): rg-shared

Result = {rg-shared}
```
결과: **{rg-shared}**. D1 admin 은 domain 수준 매핑으로 RG-shared 를 본다.

참고: D2 에도 RG-shared 매핑이 있지만 D1 admin 의 scope chain 은 D2 를 포함하지 않으므로 나열은 D1 의 scope chain 에서 보이는 RG 만 반환한다. N:N 매핑은 cross-domain 가시성을 부여하지 않는다.

cross-domain ResourceGroup 을 통한 Agent 접근(엔티티 중심 권한 검사)은 [permission-check-scope-chain-examples.md Section 3](permission-check-scope-chain-examples.md#3-domainproject--resourcegroup--agent-access-auto-edge-chain)을 본다.

---

## 5. CTE 질의: scope chain 을 포함한 ResourceGroup 전체 나열

이 절은 접근 가능한 ResourceGroup 을 나열하는 전체 SQL 패턴을 제공한다. 과정은 두 단계다. RBAC 가 질의 scope 권한을 먼저 검증하고, 나열 질의가 보이는 엔티티를 모은다.

### 1단계: RBAC 검증 (application 계층)

나열 질의를 실행하기 전에 사용자가 질의 scope 에 `resource_group:read` 를 가지는지 확인한다.

```sql
SELECT 1 FROM permissions p
JOIN user_roles ur ON ur.role_id = p.role_id
WHERE ur.user_id = 'user-A'
  AND p.scope_type = 'project' AND p.scope_id = 'proj-P1'
  AND p.entity_type = 'resource_group' AND p.operation = 'read';
-- → EXISTS → proceed to listing
```

### 2단계: 나열 질의 (CTE scope chain 순회)

```sql
-- Step 1: Build scope chain upward from the query scope
WITH RECURSIVE user_scope_chain AS (
    -- Base: the user's query scope (project)
    SELECT 'project'::text AS scope_type, 'proj-P1'::text AS scope_id

    UNION

    -- Recurse: find parent scopes via AUTO edges
    -- Project → Domain
    SELECT ase.scope_type, ase.scope_id
    FROM association_scopes_entities ase
    JOIN user_scope_chain usc
      ON ase.entity_type = usc.scope_type
     AND ase.entity_id = usc.scope_id
     AND ase.relation_type = 'auto'
),
-- Step 2: Find all ResourceGroups mapped at any scope in the chain
accessible_rgs AS (
    SELECT ase.entity_id AS rg_id
    FROM association_scopes_entities ase
    JOIN user_scope_chain usc
      ON ase.scope_type = usc.scope_type
     AND ase.scope_id = usc.scope_id
    WHERE ase.entity_type = 'resource_group'
      AND ase.relation_type = 'auto'
)
-- Step 3: Join with scaling_groups table and filter active
-- Note: Current scaling_groups uses `name` (string) as PK.
-- After ResourceGroup migration, this join key may change to a UUID `id` column.
SELECT sg.*
FROM scaling_groups sg
JOIN accessible_rgs ar ON sg.name = ar.rg_id
WHERE sg.is_active = true
ORDER BY sg.name;
```

**Domain D 의 Project P1 에 대한 scope chain 확장:**
```
user_scope_chain:
  (project, proj-P1)            ← base
  (domain, dom-D)               ← Project:proj-P1 has AUTO parent Domain:dom-D
```

**찾은 ResourceGroup:**
```
At (project, proj-P1): rg-B
At (domain, dom-D):    rg-A
→ UNION = {rg-A, rg-B}
```

---

## 6. ResourceGroup 을 고르는 세션 생성

### 상황

User A 가 Project P1 에서 ResourceGroup RG-1 을 골라 세션을 생성한다. 시스템은 RG-1 이 Project P1 의 scope chain 에서 접근 가능한지 검증해야 한다.

### DB 레코드

**ase (resource group 매핑):**

| scope_type | scope_id | entity_type    | entity_id | relation_type |
|------------|----------|----------------|-----------|---------------|
| domain     | dom-D    | resource_group | rg-1      | auto          |
| project    | proj-P1  | resource_group | rg-1      | auto          |

**permissions:**

| role_id      | scope_type | scope_id | entity_type    | operation |
|--------------|------------|----------|----------------|-----------|
| role-p1-user | project    | proj-P1  | session        | create    |
| role-p1-user | project    | proj-P1  | resource_group | read      |

### 검증: RG-1 이 Project P1 에서 접근 가능한지

세션을 생성하기 전에 시스템은 다음을 검증한다.

**1단계: RBAC:** `proj-P1` 에 `session:create`? → **통과**.

**2단계: RG 가시성 검증 (scope chain 나열):**
```
Scope chain: (project, proj-P1) → (domain, dom-D)

At (project, proj-P1): rg-1
At (domain, dom-D):    rg-1

rg-1 ∈ {rg-1} → visible
```
결과: **허용**. RG-1 은 Project P1 의 scope chain 에서 접근 가능하다. 세션 생성을 진행한다.

### 검증: 매핑되지 않은 RG-X 가 Project P1 에서 접근 가능한지

User A 가 Domain D2(다른 domain)에만 매핑된 RG-X 를 고르려 한다.

**RG-X 의 ase:**

| scope_type | scope_id | entity_type    | entity_id | relation_type |
|------------|----------|----------------|-----------|---------------|
| domain     | dom-D2   | resource_group | rg-X      | auto          |

**2단계: RG 가시성 검증:**
```
Scope chain: (project, proj-P1) → (domain, dom-D)

At (project, proj-P1): (none matching rg-X)
At (domain, dom-D):    (none matching rg-X)

rg-X ∉ {} → not visible
```
결과: **거부**. RG-X 는 scope chain 에 없다. Domain D2 에만 존재하고, 그곳은 User A 의 scope 밖이다.

---

## 요약: 현재 구현과 비교

| 현재 (`query_allowed_sgroups()`) | BEP-1048 (CTE scope chain) |
|---|---|
| `sgroups_for_domains` WHERE domain = D | `ase` WHERE scope=(domain, D) AND entity_type=resource_group AND auto |
| `sgroups_for_groups` WHERE group IN (P1, P2) | `ase` WHERE scope=(project, P) AND entity_type=resource_group AND auto |
| `sgroups_for_keypairs` WHERE access_key = K | `ase` WHERE scope=(user, U) AND entity_type=resource_group AND auto |
| Result = domain ∪ group ∪ keypair | Result = UNION across scope chain (CTE upward traversal) |

BEP-1048 모델은 세 junction 테이블을 하나의 `association_scopes_entities` 테이블로 통합하면서 같은 union 기반 연쇄 가시성 의미를 유지한다.
