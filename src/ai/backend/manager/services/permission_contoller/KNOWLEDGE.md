---
name: permission-controller-service-shapes
type: decision-table
description: role service knowledge, why a role is created through two shapes, why role edits are guarded, why a permission entry is a field row of its role, why bulk add runs one entry at a time and bulk remove runs as a partial bulk, which operations still keep a service method
scope: src/ai/backend/manager/services/permission_contoller
keywords: [CreateRoleAction, CreateGlobalRoleAction, AddRolePermissionAction, BulkRemoveRolePermissionsAction, RoleCreator, GlobalRoleCreator, RolePermissionCreator, RolePermissionPurger, entity_create_ops, global_create_ops, partial_bulk_purge_ops, PermissionControllerService]
sources:
  - src/ai/backend/manager/services/permission_contoller
  - src/ai/backend/manager/models/rbac_models/role
  - src/ai/backend/manager/models/rbac_models/permission
generated:
  by: claude-code/fable-5.1
  at: 2026-09-08
status: draft
---

# Permission controller service — Knowledge

> Rules: `../AGENTS.md`. Spec selection: `../../models/specs/KNOWLEDGE.md`.

Roles and the permission entries a role holds. The role is the entity and its
permission entries are field rows of it. One role group is wired; the operations
over the entries come from the field sub-group that group hands out.

## The processor fields

`backend.ai mgr ops list --concern rbac` prints the wired list. Its output answers
the entity type, shape, operation, gate and backing.

## A role is created through two shapes

- A role created in scopes is `CreateRoleAction`. Scope-shaped, so CREATE on roles is
  checked at every scope, and each scope owns and governs the new role.
- A role created in no scope is `CreateGlobalRoleAction`. Global-shaped, so the gate is
  SUPERADMIN.
- Two shapes because the scope validator checks nothing when `scope_targets()` is
  empty. Taking the scope-less request through the scope action would leave the gate
  open.
- The role is registered in the virtual entity graph, not in
  `association_scopes_entities`. The readers still on that table — the project
  remaining-role count a revocation makes — do not see a role created this way.
- Granting a role to a user and taking it back are not here. Each writes a roster place
  beside the role row, so they sit with the other graph writes in `../rbac`.

## Role edits are guarded single-entity operations

- Update and soft delete are `single_guarded_*_ops`; purge is `entity_purge_ops`.
- A SYSTEM role is refused by the spec's guard. It is edited through its preset.

## A permission entry is a field row of its role

- The entry has an FK to the role with `ondelete=CASCADE` and grants nothing of its
  own.
- Adding or removing an entry is a change to the role, so it is recorded as `UPDATE`
  and the role's UPDATE permission answers for it. The previous wiring had no gate.
- `AddRolePermissionAction` takes the role id and one entry: there is no row to name
  yet.
- `BulkRemoveRolePermissionsAction` takes entry ids alone. The lookup answers which
  role each belongs to, and entries spanning several roles are checked per role. The
  answer is per entry, the record per role.
- An unknown id is silently ignored by the API contract. The processor refuses with
  not-found when no owner resolves and answers a missing entry with an error, so the
  adapter short-circuits an empty input and drops not-found from `failed`.

## Bulk add runs one entry at a time

- The API contract is partial per entry: a duplicate comes back in `failed` and the
  rest land. One request may carry entries for several roles.
- The field create factories are atomic under one owner (`atomic_create_ops`) or one
  row (`create_ops`). There is no partial create shape across several owners.
- So the adapter runs one `create_ops` action per entry and collects only
  `PermissionAlreadyGranted` and integrity errors into `failed`. A permission denial
  is raised for the whole request.

## Operations that keep a service method

| Operation | Why it stays |
|---|---|
| assign / revoke / bulk assign / bulk revoke | branch that also settles project membership |
| replace_role_permissions | two-step write clearing and refilling one role's entries |
| create_permission / update_permission / delete_permission | legacy single-entry paths, not yet moved to field operations |
| get / search operations | legacy read paths |
