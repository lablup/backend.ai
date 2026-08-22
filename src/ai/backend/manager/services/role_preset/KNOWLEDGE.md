---
name: role-preset-service-shapes
type: decision-table
description: role preset knowledge: why a preset is global state that owns field rows, why creation is one action, why delete and purge both exist, why the two template-settling writes have a service
scope: src/ai/backend/manager/services/role_preset
keywords: [CreateRolePresetAction, BulkDeleteRolePresetsAction, BulkRestoreRolePresetsAction, RolePresetCreator, RolePermissionPresetCreator, RolePresetService, role_name_template, field_atomic_create_ops, partial_bulk_delete_ops, deleted]
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

배선된 목록은 `backend.ai mgr ops list --concern role_preset`이 낸다. entity type, 모양,
연산, 관문, 실행 주체는 그 출력이 답한다.

`ProcessorGroup` 하나가 배선된다. preset이 entity이고 권한 항목은 그 field 행이라,
권한 항목을 다루는 연산은 그 그룹이 내주는 field 하위 그룹에서 나온다. 기록되는 entity는
언제나 preset이다.

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

## Only the two writes that settle the template have a service

- The render at use time swallows its own failure and falls back to a generated name,
  because entity creation must not fail on role naming. That makes the write the only
  point a caller learns the template is broken.
- Create and update are the only operations that take a template, so they are the only
  ones that branch. The rest still run straight against ops.
- The check renders the template against a dummy scope in a sandboxed Jinja
  environment, refusing syntax errors, undefined variables and an empty result.
- Length is not checked: the render truncates to the column limit, so there is nothing
  to refuse.
