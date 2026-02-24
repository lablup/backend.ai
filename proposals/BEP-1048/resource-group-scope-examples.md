# BEP-1048 ResourceGroup ↔ Scope Mapping Examples

> Detail document for [BEP-1048](../BEP-1048-RBAC-entity-relationship-model.md)

This document provides concrete examples of how ResourceGroup ↔ Domain/Project/User scope mappings work with the CTE scope chain traversal. ResourceGroup uses **N:N auto edges** with scopes — one ResourceGroup can be mapped to multiple scopes, and one scope can contain multiple ResourceGroups.

## Conventions

- **ase** = `association_scopes_entities` table
- **permissions** = `permissions` table (columns: `role_id`, `scope_type`, `scope_id`, `entity_type`, `operation`)
- **user_roles** = `user_roles` table (columns: `user_id`, `role_id`)
- UUIDs are abbreviated for readability (e.g., `user-A`, `rg-1`, `proj-1`)
- CTE traversal follows only `AUTO` edges; `REF` edges terminate the chain

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

### Check: User A reads ResourceGroup RG-1

`check_permission_with_scope_chain(user_id=user-A, target=ResourceGroup:rg-1, op=read)`

**Layer 1 — Self-scope direct match:**
```sql
permissions WHERE scope_type='resource_group' AND scope_id='rg-1'
  AND entity_type='resource_group' AND operation='read'
  AND role_id IN (User A's active roles)
→ NO MATCH
```

**Layer 2 — CTE scope chain traversal:**
```sql
-- Base: AUTO edges for ResourceGroup:rg-1
ase WHERE entity_type='resource_group' AND entity_id='rg-1' AND relation_type='auto'
→ (domain, dom-D)

-- Recurse from (domain, dom-D): no AUTO parent → stop

-- Final scope set: {(domain, dom-D)}

-- Check permissions at discovered scopes
permissions WHERE (scope_type, scope_id) IN {(domain, dom-D)}
  AND entity_type='resource_group' AND operation='read'
  AND role_id IN (User A's active roles)
→ NO MATCH (User A has resource_group:read at project scope, not domain scope)
```

Result: **denied** — User A's `resource_group:read` is scoped to `proj-P1`, but the CTE only discovers `dom-D`. The permission scope does not match the discovered scope.

**Why?** This is the correct behavior. The CTE finds *where the entity lives* (Domain D), but the user's permission must cover that scope. To fix this, User A's role needs `resource_group:read` at domain scope, OR the admin creates a project-level mapping.

### Fix: Add project-level mapping OR domain-scope permission

**Option A — Add project-level ase entries (admin maps RG-1 to projects):**

| scope_type | scope_id | entity_type    | entity_id | relation_type |
|------------|----------|----------------|-----------|---------------|
| domain     | dom-D    | resource_group | rg-1      | auto          |
| project    | proj-P1  | resource_group | rg-1      | auto          |
| project    | proj-P2  | resource_group | rg-1      | auto          |

Now the CTE for RG-1 discovers: `{(domain, dom-D), (project, proj-P1), (project, proj-P2)}`
User A's `resource_group:read` at `proj-P1` matches → **allowed**.

**Option B — Grant domain-scope permission:**

| role_id      | scope_type | scope_id | entity_type    | operation |
|--------------|------------|----------|----------------|-----------|
| role-p1-user | domain     | dom-D    | resource_group | read      |

Now User A's permission matches `(domain, dom-D)` → **allowed**.

### Recommendation

Option A is the typical pattern. When an admin maps a ResourceGroup to a Domain, the system should also create per-project entries for all existing projects in that domain, and auto-create entries when new projects are added. This matches the current Backend.AI behavior where `sgroups_for_domains` cascades to all projects.

Alternatively, the system can implement "domain-level mapping implies project-level visibility" as a query-time expansion, without materializing per-project rows. This is covered in Section 5.

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

### Check: User A reads ResourceGroup RG-2

`check_permission_with_scope_chain(user_id=user-A, target=ResourceGroup:rg-2, op=read)`

**Layer 2 — CTE:**
```
Base: AUTO edges for ResourceGroup:rg-2
  → (project, proj-P1)

Recurse from (project, proj-P1): AUTO parent
  → (domain, dom-D)

Final scope set: {(project, proj-P1), (domain, dom-D)}

Check permissions for User A's roles at these scopes,
  entity_type=resource_group, op=read
→ MATCH at (project, proj-P1)
```
Result: **allowed**.

### Check: User B reads ResourceGroup RG-2

`check_permission_with_scope_chain(user_id=user-B, target=ResourceGroup:rg-2, op=read)`

**Layer 2 — CTE:**
```
Same scope set: {(project, proj-P1), (domain, dom-D)}

Check permissions for User B's roles at these scopes,
  entity_type=resource_group, op=read
→ NO MATCH (User B has resource_group:read at proj-P2, not proj-P1 or dom-D)
```
Result: **denied** — RG-2 is not mapped to Project P2 or Domain D. User B cannot access it.

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
| project    | proj-P1  | resource_group | rg-A      | auto          |
| project    | proj-P2  | resource_group | rg-A      | auto          |
| project    | proj-P1  | resource_group | rg-B      | auto          |
| project    | proj-P2  | resource_group | rg-C      | auto          |

Note: RG-A has both domain-level and per-project entries (materialized from domain mapping).

### Listing: User A's accessible ResourceGroups

To list all ResourceGroups accessible to User A in Project P1 scope:

```sql
-- Find all ResourceGroups reachable from User A's scope chain
WITH RECURSIVE scope_chain AS (
    -- Base: direct project-level RG mappings
    SELECT entity_id AS rg_id
    FROM ase
    WHERE scope_type = 'project' AND scope_id = 'proj-P1'
      AND entity_type = 'resource_group' AND relation_type = 'auto'

    UNION

    -- Recurse: domain-level RG mappings (parent scope)
    SELECT entity_id AS rg_id
    FROM ase
    WHERE scope_type = 'domain' AND scope_id = 'dom-D'
      AND entity_type = 'resource_group' AND relation_type = 'auto'
)
SELECT DISTINCT rg_id FROM scope_chain;
```

Result: `{rg-A, rg-B}` — Union of domain-level (rg-A) and project-level (rg-A, rg-B).

### Listing: User B's accessible ResourceGroups

Same query with `proj-P2`:

Result: `{rg-A, rg-C}` — Union of domain-level (rg-A) and project-level (rg-A, rg-C).

This matches the current `query_allowed_sgroups()` behavior:
```
User's RGs = (domain RGs) ∪ (project RGs) ∪ (user RGs)
```

---

## 4. N:N Mapping — One ResourceGroup, Multiple Domains

### Situation

ResourceGroup RG-shared is a cross-domain resource pool mapped to both Domain D1 and Domain D2. Each domain has its own projects and users.

### DB Records

**ase (resource group — multi-domain mapping):**

| scope_type | scope_id | entity_type    | entity_id  | relation_type |
|------------|----------|----------------|------------|---------------|
| domain     | dom-D1   | resource_group | rg-shared  | auto          |
| domain     | dom-D2   | resource_group | rg-shared  | auto          |

**ase (agent composition):**

| scope_type     | scope_id  | entity_type | entity_id | relation_type |
|----------------|-----------|-------------|-----------|---------------|
| resource_group | rg-shared | agent       | ag-1      | auto          |

**permissions:**

| role_id     | scope_type | scope_id | entity_type | operation |
|-------------|------------|----------|-------------|-----------|
| role-d1-adm | domain     | dom-D1   | agent       | read      |
| role-d2-adm | domain     | dom-D2   | agent       | read      |

### Check: Domain D1 admin reads Agent ag-1

`check_permission_with_scope_chain(user_id=user-D1-admin, target=Agent:ag-1, op=read)`

**Layer 2 — CTE:**
```
Base: AUTO edges for Agent:ag-1
  → (resource_group, rg-shared)

Recurse from (resource_group, rg-shared): AUTO edges
  → (domain, dom-D1), (domain, dom-D2)

Final scope set: {(resource_group, rg-shared), (domain, dom-D1), (domain, dom-D2)}

Check permissions for user-D1-admin's roles,
  entity_type=agent, op=read
→ MATCH at (domain, dom-D1)
```
Result: **allowed** — even though RG-shared is also mapped to D2, D1 admin's permission at D1 scope suffices.

### Note: Cross-domain visibility boundary

Domain D1 admin can see Agent ag-1 because the CTE reaches `dom-D1` through `rg-shared`. However, this does **not** grant any permission over Domain D2's resources — the scope set merely includes `dom-D2` as a reachable scope, but D1 admin has no roles at `dom-D2` scope.

---

## 5. CTE Query — Full ResourceGroup Listing with Scope Chain

This section provides the complete SQL pattern for listing accessible ResourceGroups for a user, implementing the scope chain traversal.

### Query: List ResourceGroups accessible to User A in Project P1

```sql
-- Step 1: Build scope chain upward from the user's active scope
WITH RECURSIVE user_scope_chain AS (
    -- Base: the user's direct scope (project)
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
At (project, proj-P1): rg-A, rg-B
At (domain, dom-D):    rg-A
→ UNION = {rg-A, rg-B}
```

### Query: Permission-filtered ResourceGroup listing

To additionally verify that the user has `resource_group:read` permission at the discovered scopes:

```sql
WITH RECURSIVE user_scope_chain AS (
    SELECT 'project'::text AS scope_type, 'proj-P1'::text AS scope_id
    UNION
    SELECT ase.scope_type, ase.scope_id
    FROM association_scopes_entities ase
    JOIN user_scope_chain usc
      ON ase.entity_type = usc.scope_type
     AND ase.entity_id = usc.scope_id
     AND ase.relation_type = 'auto'
),
-- Scopes where user has resource_group:read permission
permitted_scopes AS (
    SELECT p.scope_type, p.scope_id
    FROM permissions p
    JOIN user_roles ur ON ur.role_id = p.role_id
    JOIN user_scope_chain usc
      ON p.scope_type = usc.scope_type
     AND p.scope_id = usc.scope_id
    WHERE ur.user_id = 'user-A'
      AND p.entity_type = 'resource_group'
      AND p.operation = 'read'
),
accessible_rgs AS (
    SELECT DISTINCT ase.entity_id AS rg_id
    FROM association_scopes_entities ase
    JOIN permitted_scopes ps
      ON ase.scope_type = ps.scope_type
     AND ase.scope_id = ps.scope_id
    WHERE ase.entity_type = 'resource_group'
      AND ase.relation_type = 'auto'
)
SELECT sg.*
FROM scaling_groups sg
JOIN accessible_rgs ar ON sg.name = ar.rg_id
WHERE sg.is_active = true
ORDER BY sg.name;
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

Before creating the session, the system verifies ResourceGroup accessibility:

`check_permission_with_scope_chain(user_id=user-A, target=ResourceGroup:rg-1, op=read)`

**Layer 2 — CTE:**
```
Base: AUTO edges for ResourceGroup:rg-1
  → (domain, dom-D), (project, proj-P1)

Final scope set: {(domain, dom-D), (project, proj-P1)}

Check permissions for User A's roles,
  entity_type=resource_group, op=read
→ MATCH at (project, proj-P1)
```
Result: **allowed** — RG-1 is accessible. Session creation proceeds.

### Check: Is RG-X (unmapped) accessible from Project P1?

User A tries to select RG-X which is only mapped to Domain D2 (a different domain):

**ase for RG-X:**

| scope_type | scope_id | entity_type    | entity_id | relation_type |
|------------|----------|----------------|-----------|---------------|
| domain     | dom-D2   | resource_group | rg-X      | auto          |

**Layer 2 — CTE:**
```
Base: AUTO edges for ResourceGroup:rg-X
  → (domain, dom-D2)

Final scope set: {(domain, dom-D2)}

Check permissions for User A's roles at {(domain, dom-D2)}
→ NO MATCH (User A has no roles at dom-D2)
```
Result: **denied** — RG-X is not reachable from User A's scope chain.

---

## Summary: Comparison with Current Implementation

| Current (`query_allowed_sgroups()`) | BEP-1048 (CTE scope chain) |
|---|---|
| `sgroups_for_domains` WHERE domain = D | `ase` WHERE scope=(domain, D) AND entity_type=resource_group AND auto |
| `sgroups_for_groups` WHERE group IN (P1, P2) | `ase` WHERE scope=(project, P) AND entity_type=resource_group AND auto |
| `sgroups_for_keypairs` WHERE access_key = K | `ase` WHERE scope=(user, U) AND entity_type=resource_group AND auto |
| Result = domain ∪ group ∪ keypair | Result = UNION across scope chain (CTE upward traversal) |

The BEP-1048 model unifies the three separate junction tables into a single `association_scopes_entities` table while preserving the same union-based cascading visibility semantics.
