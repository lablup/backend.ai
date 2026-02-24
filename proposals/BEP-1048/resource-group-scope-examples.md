# BEP-1048 ResourceGroup ↔ Scope Mapping Examples

> Detail document for [BEP-1048](../BEP-1048-RBAC-entity-relationship-model.md)

This document provides concrete examples of how ResourceGroup ↔ Domain/Project/User scope mappings work with the CTE scope chain traversal. ResourceGroup uses **N:N auto edges** with scopes — one ResourceGroup can be mapped to multiple scopes, and one scope can contain multiple ResourceGroups.

## Conventions

- **ase** = `association_scopes_entities` table
- **permissions** = `permissions` table (columns: `role_id`, `scope_type`, `scope_id`, `entity_type`, `operation`)
- **user_roles** = `user_roles` table (columns: `user_id`, `role_id`)
- UUIDs are abbreviated for readability (e.g., `user-A`, `rg-1`, `proj-1`)
- CTE traversal follows only `AUTO` edges; `REF` edges terminate the chain
- **RBAC vs Listing separation**:
  - **RBAC**: Validates whether the user has permission at the **query scope** (e.g., `resource_group:read` at Project P1). This is a simple scope-level check — it does not traverse entity mappings.
  - **Listing**: Uses CTE scope chain traversal to collect all entities visible from the query scope upward. This is where domain-level mappings cascade to child scopes.

---

## 1. Domain-Level Mapping — Cascading Visibility

### Situation

ResourceGroup RG-1 is mapped to Domain D. Domain D contains Project P1 and Project P2.
User A belongs to Project P1, User B belongs to Project P2.
Both users should be able to access RG-1 without per-project mapping.

### DB Records

**ase (domain hierarchy — auto edges):**

| scope_type | scope_id | entity_type | entity_id | relation_type |
|------------|----------|-------------|-----------|---------------|
| domain     | dom-D    | project     | proj-P1   | auto          |
| domain     | dom-D    | project     | proj-P2   | auto          |
| domain     | dom-D    | user        | user-A    | auto          |
| domain     | dom-D    | user        | user-B    | auto          |

**ase (resource group assignment — auto edge at domain level):**

| scope_type | scope_id | entity_type    | entity_id | relation_type |
|------------|----------|----------------|-----------|---------------|
| domain     | dom-D    | resource_group | rg-1      | auto          |

Note: No per-project entries for RG-1 exist. The domain-level mapping alone provides visibility to all child scopes.

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

### Check: User A lists ResourceGroups from Project P1 scope

**Step 1 — RBAC validation (query scope check):**

Does User A have `resource_group:read` at the query scope (Project P1)?

```sql
permissions WHERE scope_type='project' AND scope_id='proj-P1'
  AND entity_type='resource_group' AND operation='read'
  AND role_id IN (User A's active roles)
→ MATCH (role-p1-user has resource_group:read at proj-P1)
```
Result: **passed** — User A is authorized to list ResourceGroups from Project P1 scope.

**Step 2 — Listing (CTE scope chain traversal):**

Build scope chain upward from the query scope, then collect all RGs at each level:

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

Result: **{rg-1}** — RG-1 is visible to User A via domain-level mapping, even though no project-level entry exists.

### Check: User B lists ResourceGroups from Project P2 scope

**Step 1 — RBAC:** `resource_group:read` at `proj-P2`? → **passed**.

**Step 2 — Listing:**
```
Scope chain: (project, proj-P2) → (domain, dom-D)

At (project, proj-P2): (none)
At (domain, dom-D):    rg-1

Result = {rg-1}
```

Result: **{rg-1}** — Same domain-level mapping cascades to all projects within the domain.

---

## 2. Project-Level Mapping — Scoped Visibility

### Situation

ResourceGroup RG-2 is mapped only to Project P1 (not to Domain D).
User A (in Project P1) should see RG-2. User B (in Project P2) should not.

### DB Records

**ase (resource group assignment — project-level only):**

| scope_type | scope_id | entity_type    | entity_id | relation_type |
|------------|----------|----------------|-----------|---------------|
| project    | proj-P1  | resource_group | rg-2      | auto          |

**permissions:**

| role_id      | scope_type | scope_id | entity_type    | operation |
|--------------|------------|----------|----------------|-----------|
| role-p1-user | project    | proj-P1  | resource_group | read      |
| role-p2-user | project    | proj-P2  | resource_group | read      |

### Check: User A lists ResourceGroups from Project P1 scope

**Step 1 — RBAC:** `resource_group:read` at `proj-P1`? → **passed**.

**Step 2 — Listing:**
```
Scope chain: (project, proj-P1) → (domain, dom-D)

At (project, proj-P1): rg-2
At (domain, dom-D):    (none)

Result = {rg-2}
```
Result: **{rg-2}** — User A sees RG-2 via project-level mapping.

### Check: User B lists ResourceGroups from Project P2 scope

**Step 1 — RBAC:** `resource_group:read` at `proj-P2`? → **passed**.

**Step 2 — Listing:**
```
Scope chain: (project, proj-P2) → (domain, dom-D)

At (project, proj-P2): (none)
At (domain, dom-D):    (none)

Result = {}
```
Result: **{}** — RG-2 is not mapped to Project P2 or Domain D. User B cannot see it.

---

## 3. Union Behavior — Mixed Domain and Project Mappings

### Situation

- RG-A is mapped to Domain D (domain-level, accessible to all projects)
- RG-B is mapped only to Project P1
- RG-C is mapped only to Project P2
- User A (in Project P1) should see RG-A + RG-B
- User B (in Project P2) should see RG-A + RG-C

### DB Records

**ase (resource group assignments):**

| scope_type | scope_id | entity_type    | entity_id | relation_type |
|------------|----------|----------------|-----------|---------------|
| domain     | dom-D    | resource_group | rg-A      | auto          |
| project    | proj-P1  | resource_group | rg-B      | auto          |
| project    | proj-P2  | resource_group | rg-C      | auto          |

Note: RG-A has only a domain-level entry. No per-project materialization is needed — the CTE scope chain traversal naturally cascades domain-level mappings to child scopes.

### Listing: User A's accessible ResourceGroups from Project P1

**Step 1 — RBAC:** `resource_group:read` at `proj-P1`? → **passed**.

**Step 2 — Listing:**
```
Scope chain: (project, proj-P1) → (domain, dom-D)

At (project, proj-P1): rg-B
At (domain, dom-D):    rg-A

Result = {rg-A, rg-B}
```

### Listing: User B's accessible ResourceGroups from Project P2

**Step 1 — RBAC:** `resource_group:read` at `proj-P2`? → **passed**.

**Step 2 — Listing:**
```
Scope chain: (project, proj-P2) → (domain, dom-D)

At (project, proj-P2): rg-C
At (domain, dom-D):    rg-A

Result = {rg-A, rg-C}
```

This matches the current `query_allowed_sgroups()` behavior:
```
User's RGs = (domain RGs) ∪ (project RGs) ∪ (user RGs)
```

---

## 4. N:N Mapping — One ResourceGroup, Multiple Domains

### Situation

ResourceGroup RG-shared is a cross-domain resource pool mapped to both Domain D1 and Domain D2. Domain D1 admin lists RGs from their domain scope and sees RG-shared.

### DB Records

**ase (resource group — multi-domain mapping):**

| scope_type | scope_id | entity_type    | entity_id  | relation_type |
|------------|----------|----------------|------------|---------------|
| domain     | dom-D1   | resource_group | rg-shared  | auto          |
| domain     | dom-D2   | resource_group | rg-shared  | auto          |

### Check: Domain D1 admin lists ResourceGroups

**Step 1 — RBAC:** `resource_group:read` at `dom-D1`? → **passed**.

**Step 2 — Listing:**
```
Scope chain: (domain, dom-D1) → (global)

At (domain, dom-D1): rg-shared

Result = {rg-shared}
```
Result: **{rg-shared}** — D1 admin sees RG-shared via domain-level mapping.

Note: D2 also has RG-shared mapped, but D1 admin's scope chain does not include D2, so the listing only returns RGs visible from D1's scope chain. The N:N mapping does not create cross-domain visibility.

For Agent access through cross-domain ResourceGroups (entity-centric permission checks), see [permission-check-scope-chain-examples.md Section 3](permission-check-scope-chain-examples.md#3-domainproject--resourcegroup--agent-access-auto-edge-chain).

---

## 5. CTE Query — Full ResourceGroup Listing with Scope Chain

This section provides the complete SQL pattern for listing accessible ResourceGroups. The process is two-phase: RBAC validates the query scope permission first, then the listing query collects visible entities.

### Phase 1: RBAC Validation (application layer)

Before executing the listing query, verify the user has `resource_group:read` at the query scope:

```sql
SELECT 1 FROM permissions p
JOIN user_roles ur ON ur.role_id = p.role_id
WHERE ur.user_id = 'user-A'
  AND p.scope_type = 'project' AND p.scope_id = 'proj-P1'
  AND p.entity_type = 'resource_group' AND p.operation = 'read';
-- → EXISTS → proceed to listing
```

### Phase 2: Listing Query (CTE scope chain traversal)

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
SELECT sg.*
FROM scaling_groups sg
JOIN accessible_rgs ar ON sg.name = ar.rg_id
WHERE sg.is_active = true
ORDER BY sg.name;
```

**Scope chain expansion for Project P1 in Domain D:**
```
user_scope_chain:
  (project, proj-P1)            ← base
  (domain, dom-D)               ← Project:proj-P1 has AUTO parent Domain:dom-D
```

**ResourceGroups found:**
```
At (project, proj-P1): rg-B
At (domain, dom-D):    rg-A
→ UNION = {rg-A, rg-B}
```

---

## 6. Session Creation with ResourceGroup Selection

### Situation

User A creates a session in Project P1, selecting ResourceGroup RG-1. The system must verify that RG-1 is accessible from Project P1's scope chain.

### DB Records

**ase (resource group mapping):**

| scope_type | scope_id | entity_type    | entity_id | relation_type |
|------------|----------|----------------|-----------|---------------|
| domain     | dom-D    | resource_group | rg-1      | auto          |
| project    | proj-P1  | resource_group | rg-1      | auto          |

**permissions:**

| role_id      | scope_type | scope_id | entity_type    | operation |
|--------------|------------|----------|----------------|-----------|
| role-p1-user | project    | proj-P1  | session        | create    |
| role-p1-user | project    | proj-P1  | resource_group | read      |

### Check: Is RG-1 accessible from Project P1?

Before creating the session, the system verifies:

**Step 1 — RBAC:** `session:create` at `proj-P1`? → **passed**.

**Step 2 — RG visibility check (scope chain listing):**
```
Scope chain: (project, proj-P1) → (domain, dom-D)

At (project, proj-P1): rg-1
At (domain, dom-D):    rg-1

rg-1 ∈ {rg-1} → visible
```
Result: **allowed** — RG-1 is accessible from Project P1's scope chain. Session creation proceeds.

### Check: Is RG-X (unmapped) accessible from Project P1?

User A tries to select RG-X which is only mapped to Domain D2 (a different domain):

**ase for RG-X:**

| scope_type | scope_id | entity_type    | entity_id | relation_type |
|------------|----------|----------------|-----------|---------------|
| domain     | dom-D2   | resource_group | rg-X      | auto          |

**Step 2 — RG visibility check:**
```
Scope chain: (project, proj-P1) → (domain, dom-D)

At (project, proj-P1): (none matching rg-X)
At (domain, dom-D):    (none matching rg-X)

rg-X ∉ {} → not visible
```
Result: **denied** — RG-X is not in the scope chain. It exists only at Domain D2, which is outside User A's scope.

---

## Summary: Comparison with Current Implementation

| Current (`query_allowed_sgroups()`) | BEP-1048 (CTE scope chain) |
|---|---|
| `sgroups_for_domains` WHERE domain = D | `ase` WHERE scope=(domain, D) AND entity_type=resource_group AND auto |
| `sgroups_for_groups` WHERE group IN (P1, P2) | `ase` WHERE scope=(project, P) AND entity_type=resource_group AND auto |
| `sgroups_for_keypairs` WHERE access_key = K | `ase` WHERE scope=(user, U) AND entity_type=resource_group AND auto |
| Result = domain ∪ group ∪ keypair | Result = UNION across scope chain (CTE upward traversal) |

The BEP-1048 model unifies the three separate junction tables into a single `association_scopes_entities` table while preserving the same union-based cascading visibility semantics.
