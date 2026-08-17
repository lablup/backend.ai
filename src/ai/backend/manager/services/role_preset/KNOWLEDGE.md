---
name: role-preset-service-shapes
type: decision-table
description: role preset processor fields and their entity/operation/scope, why a preset is global state that owns field rows, why creation is one action, why delete and purge both exist, where the name template is validated
scope: src/ai/backend/manager/services/role_preset
keywords: [CreateRolePresetAction, BulkDeleteRolePresetsAction, BulkRestoreRolePresetsAction, RolePresetCreator, RolePermissionPresetCreator, RoleNameTemplateCarrier, global_create_with_fields_ops, field_atomic_create_ops, partial_bulk_delete_ops, deleted]
sources:
  - src/ai/backend/manager/services/role_preset
  - src/ai/backend/manager/models/rbac_models/role_preset
  - src/ai/backend/manager/models/rbac_models/role_permission_preset
generated:
  by: claude-code/opus-5
  at: 2026-08-18
status: stable
---

# Role preset service — Knowledge

> Rules: `../AGENTS.md`. Spec selection: `../../models/specs/KNOWLEDGE.md`.

A role preset declares which roles a scope type provisions when an entity of
that type is created, and which permissions each of those roles carries. The
package covers two tables because the permission rows have no life apart from
the preset that owns them.

## The processor fields

| Field | Action | Entity type | Shape | Operation |
|---|---|---|---|---|
| `create` | `CreateRolePresetAction` | ROLE_PRESET | global + fields | CREATE |
| `get` | `GetRolePresetAction` | ROLE_PRESET | global | GET |
| `search` | `SearchRolePresetsAction` | ROLE_PRESET | global | SEARCH |
| `update` | `UpdateRolePresetAction` | ROLE_PRESET | global | UPDATE |
| `bulk_delete` | `BulkDeleteRolePresetsAction` | ROLE_PRESET | partial bulk | DELETE |
| `bulk_restore` | `BulkRestoreRolePresetsAction` | ROLE_PRESET | partial bulk | RESTORE |
| `purge` | `PurgeRolePresetAction` | ROLE_PRESET | global | PURGE |
| `bulk_purge` | `BulkPurgeRolePresetsAction` | ROLE_PRESET | partial bulk | PURGE |
| `search_permission_presets` | `SearchRolePermissionPresetsAction` | ROLE_PRESET | global | SEARCH |
| `bulk_add_permissions` | `BulkAddRolePermissionPresetsAction` | ROLE_PRESET | single entity, atomic | UPDATE |
| `bulk_remove_permissions` | `BulkRemoveRolePermissionPresetsAction` | ROLE_PRESET | bulk field, partial | UPDATE |

One `ProcessorGroup` is wired. The preset is the entity and its permission entries
are field rows of it, so the last three come from the field sub-group that group hands
out. The entity recorded is always the preset.

## A preset is global state that owns field rows

- The preset sits outside the scope hierarchy: it declares what a scope type
  gets, joins no scope, and is never shared — so `RolePresetCreator` is a
  `GlobalEntityCreator`.
- Its permission rows are a `FieldCreator`: FK to the preset with
  `ondelete=CASCADE`, unique on the `(preset, entity_type, operation)` triple,
  and referenced by nothing else.
- A global owner is not a contradiction. Field means the row's membership is only
  knowable through its owner, not that the owner sits under something.

## Creation is one action so the two tables share a transaction

- `global_create_with_fields_ops` takes the preset's creator and the permission
  creators together; a preset that survived a failed permission row would grant
  less than it declares.
- The field creators build from the parent's id, which does not exist until the
  parent row does — `FieldCreator.build_row(owner_id)` is what makes that
  orderable inside one write.

## A permission entry is answered for by its preset

- Adding or removing an entry is a change to the preset, so it is recorded as `UPDATE`.
  An entry carries no permission bit of its own.
- `bulk_add` takes the preset id: there is no entry yet to name. `bulk_remove` takes
  entry ids alone and the owning preset is what the lookup answers.
- The entries `bulk_remove` takes may belong to different presets. Their owners are
  read in one go and every one is checked. The answer is per entry, the record per
  preset.

## Delete and purge are different operations, not duplicates

- `role_presets.deleted` is the lifecycle column, so `bulk_delete` is an UPDATE
  at the DB recorded as `DELETE`, and `bulk_restore` is the same update reversed.
- `purge` and `bulk_purge` remove the row, taking the permission rows with it by
  FK cascade.
- The lifecycle column is not exposed on the general updater, so an ordinary edit
  cannot make the transition.

## The name template is validated at the action layer

- `RoleNameTemplateCarrier` is a separate mixin, and the validator picks actions
  out by `isinstance` — create and update both carry a template, and neither
  should reach a transaction with a malformed one.
- Rendering happens in a sandboxed Jinja environment against a dummy scope, so a
  template that cannot render is refused and recorded like any other denial.
