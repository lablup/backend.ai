---
name: error-log-service-shapes
type: decision-table
description: error log knowledge: why recording is user-scoped rather than global, why clearing is a soft delete addressed by id
scope: src/ai/backend/manager/services/user/error_log
keywords: [CreateErrorLogAction, DeleteErrorLogAction, SearchErrorLogsAction, AdminSearchErrorLogsAction, ErrorLogSoftDeleteUpdater, UserErrorLogOperationScope, entity_create_ops, scope_search_ops, single_delete_ops, is_cleared]
sources:
  - src/ai/backend/manager/services/user/error_log
  - src/ai/backend/manager/models/error_log
  - src/ai/backend/manager/repositories/error_log
generated:
  by: claude-code/opus-5
  at: 2026-08-14
status: stable
---

# Error log service — Knowledge

> Rules: `../AGENTS.md`. Spec selection: `../../models/specs/KNOWLEDGE.md`.

This package records the errors users and components hit, and answers who may
read them back. It exists as its own domain because the table has two kinds of
row — one owned by a user, one owned by nobody — and only the first goes through
the action layer.

## The processor fields

`backend.ai mgr ops list --field error_log` prints the wired list. Its output answers
the entity type, shape, operation, gate and backing.

## Recording is user-scoped, not global

- An error belongs to whoever hit it: the row carries a user FK and an
  `is_cleared` flag its owner dismisses it with.
- A global gate would mean only an installation administrator may report that
  something broke for them, which is not what the routes declare.
- `ErrorLogCreator` is therefore an `EntityCreator` whose `member_of` joins the
  owning user's scope, and empty when the row has no owner.

## The reads are two actions, not one that widens

- A super admin reads the whole table; everyone else reads inside their own
  scope. The REST handler picks between them.
- Keeping them separate is what lets each carry its own gate — one action that
  widened itself would have to be authorized for the narrow case and then
  return the wide result.

## Clearing is this domain's soft delete

- `is_cleared` is the lifecycle column: the owner's read excludes cleared rows
  while the admin read still returns them.
- It is therefore a `DELETE` carrying `ErrorLogSoftDeleteUpdater`, whose
  `build_values()` is a constant — a transition taken as an argument can be
  passed backwards.
- The action is single-entity because by then the row exists to name; the scope
  shape would authorize the caller's own scope rather than the row being cleared.

## Authorization moved to the permission layer and the rows are not seeded yet

- Ownership used to be enforced by a WHERE clause in the repository; it now
  rests on the RBAC validators.
- No `migrate_error_log_data_to_rbac` exists, so until the permission rows land
  a non-super-admin caller is refused.
- The component suite cannot see either state: it replaces the virtual-scope
  validators with mocks, so its fixtures admit every caller.
