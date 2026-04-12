# RBAC Role-Scope Binding Redesign — Review Notes

> Review of the `docs/rbac-role-scope-binding-redesign` branch changes against BEP-1008, BEP-1012, and BEP-1048.
> Date: 2026-04-11

## Resolved During Review

### Project Membership — Single Source of Truth

**Decision**: Project membership is managed exclusively via `user_roles` + role-scope binding (`association_scopes_entities` where `entity_type='role'`).

The edge catalog entry `Project ━━ref━━► User` should be removed or reclassified. `AssocGroupUserRow` is fully replaced by role-scope binding — no ref edge in `association_scopes_entities` is used for membership.

**Action**: Update `entity-edge-catalog.md` to remove `Project ━━ref━━► User` from the Ref Edges section.

### Scope Constraint Rule Removed

**Decision**: The rule "A permission's scope must be one of the role's bound scopes" is removed from the design. Permissions can reference any scope, including entity-scopes (e.g., `scope_type=vfolder, scope_id=vf-1`) that are not pre-declared as role-scope bindings.

**Action**: Remove the scope constraint language from BEP-1008 and BEP-1012.

---

## Open Issues

### HIGH — Schema Defect

#### 1. `association_scopes_entities` unique constraint missing `entity_type`

**Current**:
```sql
UNIQUE(scope_type, scope_id, entity_id)
```

**Problem**: `entity_id` is `VARCHAR(64)`, not strictly UUID. Some entities use string-based PKs (e.g., `scaling_groups` uses `name` as PK). If two different entity types share the same string ID within the same scope, the constraint fails silently or causes unexpected conflicts.

**Fix**:
```sql
UNIQUE(scope_type, scope_id, entity_type, entity_id)
```

---

### MEDIUM — Functional Regressions / Gaps

#### 2. `user_roles.state` removal — no soft-delete for role assignments

The redesign removes `state` from `user_roles`. This means role assignments can only be hard-deleted — there is no way to temporarily deactivate an assignment while preserving the audit record (`granted_by`, `granted_at`).

**Impact**: If compliance or audit requires "who had access and when it was revoked", the deletion event must be captured externally (e.g., audit log), since the `user_roles` row itself is gone.

**Options**:
1. Keep `state` column (or rename to `status` for consistency with `roles.status`).
2. Accept hard-delete only and rely on audit log for history.

#### 3. `user_roles.expires_at` removal vs Future Features

BEP-1012 Section "Future Features" lists "Temporary Role Assignments with Expiration" with `expires_at` as a planned attribute. The redesign removes this column entirely.

**Action needed**: Either keep the column (nullable, unused for now) or update the Future Features section to note that the column will be added when the feature is implemented.

#### 4. Role name uniqueness not enforced

The old schema had `UNIQUE(name, scope_type, scope_id)` on `roles`, preventing duplicate names within a scope. Since roles are no longer bound to a single scope, this constraint was dropped.

**Result**: Multiple roles with identical names can exist, causing confusion in admin UIs and API responses.

**Options**:
1. `UNIQUE(name)` — globally unique role names.
2. `UNIQUE(name, source)` — unique within system/custom partition.
3. No constraint — rely on application-layer validation.

#### 5. Superadmin handling after Global scope removal

The redesign removes Global scope from the grant hierarchy, but does not define how superadmin permissions work:

- Superadmin-only entities still exist: `DomainRow`, `ResourcePresetRow`, `UserResourcePolicyRow`, `KeyPairResourcePolicyRow`, `ProjectResourcePolicyRow`, `RoleRow`, `AuditLogRow`, `EventLogRow`.
- Without Global scope, these entities have no scope to bind permissions to.

**Questions to resolve**:
1. Is superadmin a code-level bypass that skips RBAC entirely?
2. Does superadmin automatically receive permissions at every domain scope?
3. Is there a synthetic "system" scope that replaces Global?

---

### LOW — Performance / Implementation Notes

#### 6. Membership query performance

Current (single-table lookup):
```sql
SELECT user_id FROM association_groups_users WHERE group_id = ?
```

After redesign (JOIN required):
```sql
SELECT DISTINCT ur.user_id
FROM user_roles ur
JOIN association_scopes_entities ase
  ON ase.entity_type = 'role' AND ase.entity_id = ur.role_id::text
WHERE ase.scope_type = 'project' AND ase.scope_id = ?
```

Project member listing is a high-frequency query (used in permission checks, UI, etc.). Consider:
- Composite index on `association_scopes_entities(scope_type, scope_id, entity_type)`.
- Materialized view or denormalized cache if query latency becomes an issue.

#### 7. Recursive CTE cost for deep entity hierarchies

Every permission check runs a recursive CTE over `association_scopes_entities`. Deep composition chains (e.g., `Domain → Project → Session → Kernel → KernelSchedulingHistory`) increase traversal depth.

Consider:
- Setting a max recursion depth (PostgreSQL `RECURSIVE` has no built-in limit guard).
- Caching resolved scope chains for hot paths (e.g., session/kernel access).
- Benchmarking with realistic data volumes.

#### 8. `OperationType` helper methods return full set

In `src/ai/backend/common/data/permission/types.py`, the methods `owner_operations()`, `admin_operations()`, and `member_operations()` all return `{op for op in cls}` (the complete operation set). These are placeholder implementations that need role-specific subsets before system roles can be auto-provisioned with correct default permissions.

#### 9. Share revocation atomicity

Revoking a share requires two operations:
1. DELETE ref edge from `association_scopes_entities`
2. DELETE entity-scope permissions from `permissions`

These must execute within a single transaction. If partially applied:
- Edge deleted but permissions remain → orphaned permission rows (harmless but wasteful).
- Permissions deleted but edge remains → user sees entity in listings but cannot operate on it (confusing UX).

Implementation should use `begin_session()` to wrap both operations.
