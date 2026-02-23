---
Author: Sanghun Lee (sanghun@lablup.com)
Status: Draft
Created: 2026-02-21
Parent: BEP-1048-RBAC-entity-relationship-model.md
---

# BEP-1048 Permission Check Examples

This document provides concrete examples of how `check_permission_with_scope_chain()` resolves permissions by walking the `association_scopes_entities` table. Each scenario shows the exact DB records required and how the two-layer check (self-scope direct match + CTE scope chain traversal) produces a result.

## Conventions

- **ase** = `association_scopes_entities` table
- **permissions** = `permissions` table (columns: `role_id`, `scope_type`, `scope_id`, `entity_type`, `operation`)
- **user_roles** = `user_roles` table (columns: `user_id`, `role_id`)
- UUIDs are abbreviated for readability (e.g., `user-A`, `vf-1`, `proj-1`)
- CTE traversal follows only `AUTO` edges; `REF` edges terminate the chain

---

## 1. VFolder Sharing (Ref Edge + Entity-Scope Permission)

### Situation

User A owns VFolder X in Project P. User A invites User B with write permission to VFolder X.

### DB Records

**ase (ownership — auto edges):**

| scope_type | scope_id | entity_type | entity_id | relation_type |
|------------|----------|-------------|-----------|---------------|
| project    | proj-1   | vfolder     | vf-1      | auto          |
| user       | user-A   | vfolder     | vf-1      | auto          |

**ase (sharing — ref edge):**

| scope_type | scope_id | entity_type | entity_id | relation_type |
|------------|----------|-------------|-----------|---------------|
| user       | user-B   | vfolder     | vf-1      | ref           |

**user_roles:**

| user_id | role_id    |
|---------|------------|
| user-A  | role-owner |
| user-B  | role-member|

**permissions (User B's role — no project-scope vfolder permissions):**

User B is not a member of Project P and has no project-scope vfolder permissions. The only vfolder access User B has is through the entity-scope grants created on invite.

**permissions (User B's role — entity-scope, granted on invite):**

| role_id     | scope_type | scope_id | entity_type | operation |
|-------------|------------|----------|-------------|-----------|
| role-member | vfolder    | vf-1     | vfolder     | read      |
| role-member | vfolder    | vf-1     | vfolder     | write     |

### Check: User B reads VFolder X

`check_permission_with_scope_chain(user_id=user-B, target=VFolder:vf-1, op=read)`

**Layer 1 — Self-scope direct match:**
```sql
-- Does User B have a permission where scope = VFolder:vf-1?
permissions WHERE scope_type='vfolder' AND scope_id='vf-1'
  AND entity_type='vfolder' AND operation='read'
  AND role_id IN (User B's active roles)
→ MATCH (entity-scope read grant)
```
Result: **allowed**.

### Check: User B deletes VFolder X

`check_permission_with_scope_chain(user_id=user-B, target=VFolder:vf-1, op=delete)`

**Layer 1 — Self-scope direct match:**
```sql
permissions WHERE scope_type='vfolder' AND scope_id='vf-1'
  AND entity_type='vfolder' AND operation='delete'
→ NO MATCH (no entity-scope delete grant)
```

**Layer 2 — CTE scope chain traversal:**
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
Result: **denied** — User B has no project-scope permissions, and the ref edge is excluded from the CTE. Only the explicitly granted entity-scope permissions (read/write) apply.

### Check: User A reads VFolder X

`check_permission_with_scope_chain(user_id=user-A, target=VFolder:vf-1, op=read)`

**Layer 1 — Self-scope:** no entity-scope permission for user-A → no match.

**Layer 2 — CTE:**
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
Result: **allowed**.

---

## 2. Session and Kernel Info Access (Auto Edge Chain)

### Situation

User C creates a session in Project P. The session has 2 kernels allocated on Agent ag-1 in ResourceGroup rg-1. User C wants to read kernel details.

### DB Records

**ase (scope hierarchy — auto edges):**

| scope_type | scope_id | entity_type | entity_id | relation_type |
|------------|----------|-------------|-----------|---------------|
| domain     | dom-1    | project     | proj-1    | auto          |
| project    | proj-1   | session     | sess-1    | auto          |
| user       | user-C   | session     | sess-1    | auto          |

**ase (session composition — auto edges):**

| scope_type | scope_id | entity_type | entity_id | relation_type |
|------------|----------|-------------|-----------|---------------|
| session    | sess-1   | kernel      | kern-1    | auto          |
| session    | sess-1   | kernel      | kern-2    | auto          |

**ase (resource group composition — auto edges):**

| scope_type | scope_id | entity_type | entity_id | relation_type |
|------------|----------|-------------|-----------|---------------|
| resource_group | rg-1 | agent       | ag-1      | auto          |
| agent      | ag-1     | kernel      | kern-1    | auto          |
| agent      | ag-1     | kernel      | kern-2    | auto          |

**ase (session ref edges — read-only references):**

| scope_type | scope_id | entity_type | entity_id | relation_type |
|------------|----------|-------------|-----------|---------------|
| session    | sess-1   | agent       | ag-1      | ref           |
| session    | sess-1   | resource_group | rg-1   | ref           |

### Check: User C reads Kernel kern-1

`check_permission_with_scope_chain(user_id=user-C, target=Kernel:kern-1, op=read)`

**Layer 1 — Self-scope:** no permission scoped to `kernel:kern-1` → no match.

**Layer 2 — CTE:**
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
Result: **allowed** — permission flows through `Project ━auto━► Session ━auto━► Kernel`.

### Check: User C reads Kernel kern-1 via Agent path

The CTE discovers both paths simultaneously:
- **Session path**: `Kernel ← Session ← Project ← Domain`
- **Agent path**: `Kernel ← Agent ← ResourceGroup`

Both paths consist of AUTO edges, so both contribute to the scope set. If User C's role has `kernel:read` at *any* of the discovered scopes, the check passes. The CTE's UNION deduplicates overlapping scopes (e.g., `domain:dom-1` reached from both paths).

### Check: User C writes Kernel kern-1 (no write permission)

`check_permission_with_scope_chain(user_id=user-C, target=Kernel:kern-1, op=write)`

**Layer 1 — Self-scope:** no match.

**Layer 2 — CTE:** same scope set as above, but:
```
Check permissions for entity_type=kernel, op=write
→ NO MATCH (User C's role only has kernel:read, not kernel:write)
```
Result: **denied**.

---

## 3. Domain/Project — ResourceGroup — Agent Access (Auto Edge Chain)

### Situation

Domain D has Project P. ResourceGroup RG-1 is assigned to Domain D and Project P. Agent ag-1 belongs to RG-1. Three users exist:
- User M: domain manager (has `agent:read` at domain scope)
- User PA: project admin (has `agent:read` at project scope)
- User PM: project member (no `agent:read` permission)

### DB Records

**ase (domain hierarchy — auto edges):**

| scope_type | scope_id | entity_type | entity_id | relation_type |
|------------|----------|-------------|-----------|---------------|
| domain     | dom-D    | project     | proj-P    | auto          |
| domain     | dom-D    | user        | user-M    | auto          |
| domain     | dom-D    | user        | user-PA   | auto          |
| domain     | dom-D    | user        | user-PM   | auto          |

**ase (resource group assignment — auto edges):**

| scope_type | scope_id | entity_type    | entity_id | relation_type |
|------------|----------|----------------|-----------|---------------|
| domain     | dom-D    | resource_group | rg-1      | auto          |
| project    | proj-P   | resource_group | rg-1      | auto          |

**ase (agent composition — auto edge):**

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

Note: `role-proj-mem` has `resource_group:read` but **not** `agent:read`. Having `resource_group:read` does not imply `agent:read` — each entity type requires an explicit permission grant.

### Check: User M reads Agent ag-1 (domain manager)

`check_permission_with_scope_chain(user_id=user-M, target=Agent:ag-1, op=read)`

**Layer 1 — Self-scope:** no permission scoped to `agent:ag-1` → no match.

**Layer 2 — CTE:**
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
Result: **allowed**.

### Check: User PA reads Agent ag-1 (project admin)

`check_permission_with_scope_chain(user_id=user-PA, target=Agent:ag-1, op=read)`

**Layer 1 — Self-scope:** no match.

**Layer 2 — CTE:**
```
Same scope set: {(resource_group, rg-1), (domain, dom-D), (project, proj-P)}

Check permissions for user-PA's roles,
  entity_type=agent, op=read
→ MATCH at (project, proj-P) — role-proj-adm has agent:read at project scope
```
Result: **allowed** — permission flows through `Project ━auto━► ResourceGroup ━auto━► Agent`.

### Check: User PM reads Agent ag-1 (project member)

`check_permission_with_scope_chain(user_id=user-PM, target=Agent:ag-1, op=read)`

**Layer 1 — Self-scope:** no match.

**Layer 2 — CTE:**
```
Same scope set: {(resource_group, rg-1), (domain, dom-D), (project, proj-P)}

Check permissions for user-PM's roles,
  entity_type=agent, op=read
→ NO MATCH (role-proj-mem has resource_group:read but not agent:read)
```
Result: **denied** — the AUTO edge path exists, but User PM's role does not include `agent:read` at any reachable scope. `resource_group:read` permission does not cascade to `agent:read`.

### Check: User M reads Agent ag-1 (resource group not assigned to domain)

If the `(domain, dom-D) ━auto━► (resource_group, rg-1)` edge does not exist (e.g., RG-1 is assigned to a different domain):

```
Base: AUTO edges for Agent:ag-1
  → (resource_group, rg-1)

Recurse from (resource_group, rg-1): AUTO edges where entity=resource_group:rg-1
  → (domain, dom-X)  [different domain]

Final scope set: {(resource_group, rg-1), (domain, dom-X)}

Check permissions for user-M's roles at these scopes
→ NO MATCH (user-M has permissions at dom-D, not dom-X)
```
Result: **denied** — the scope chain does not reach a scope where User M has permissions.

### Multi-Project ResourceGroup Assignment

ResourceGroup RG-1 can be assigned to multiple projects:

**ase (additional project assignment):**

| scope_type | scope_id | entity_type    | entity_id | relation_type |
|------------|----------|----------------|-----------|---------------|
| project    | proj-P   | resource_group | rg-1      | auto          |
| project    | proj-Q   | resource_group | rg-1      | auto          |

Now the CTE for Agent ag-1 discovers:
```
Base: (resource_group, rg-1)
Recurse: (domain, dom-D), (project, proj-P), (project, proj-Q)
```

A project admin of proj-P with `agent:read` at project scope can access ag-1, while a project admin of proj-R (not assigned) cannot.
