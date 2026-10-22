---
name: session-group-service-shapes
type: decision-table
description: session_group knowledge - why the reads by id keep a service while the two searches, the creation, the update and the purge run against ops, how a deployment's group is left out of every user read and refused by the update and the purge, why the bulk read is partial
scope: src/ai/backend/manager/services/session_group
keywords: [GetSessionGroupAction, BulkGetSessionGroupsAction, GlobalSearchSessionGroupsAction, ScopedSearchSessionGroupsAction, CreateSessionGroupAction, SessionGroupCreator, UpdateSessionGroupAction, SessionGroupUpdater, GuardCheck, PurgeSessionGroupAction, SessionGroupPurger, SessionGroupService, OpsRepository, SessionGroupTarget, replica_groups, partial_bulk, single_entity]
sources:
  - src/ai/backend/manager/services/session_group
  - src/ai/backend/manager/repositories/ops/repository.py
  - src/ai/backend/manager/models/session_group
generated:
  by: claude-code/opus-5.5
  at: 2026-10-15
updated:
  by: claude-code/opus-5.5
  at: 2026-10-22
status: draft
---

# Session group service — Knowledge

> Rules: `../AGENTS.md`. Placement policy: `proposals/BEP-1064-session-group-placement.md`.

A session group holds the placement policy of its member sessions. It is owned by a
project and a user. A deployment makes one with every replica group, and that group is
managed with its deployment, not by the user.

## The processor fields

`backend.ai mgr ops list` prints the wired list. Its output answers the entity type,
shape, operation, gate and backing.

## A deployment's group is left out of every user read

| Operation | Where the group is left out |
|---|---|
| `get` | The action's searcher matches the row only when no replica group holds it; the service answers not found otherwise |
| `bulk_get_ids` | The same searcher for many ids; a held group answers empty |
| `scoped_search` | Every `SessionGroupTarget` adds the same condition to its scope condition |
| `global_search` | Not left out: the superadmin sees every group |
| `update` | `SessionGroupUpdater` carries the condition as a `GuardCheck`; a held group is refused as in use (409) |
| `purge` | The purger's guard rides on the DELETE; a held group is refused as in use (409) |

- The condition is `SessionGroupSearchableFields.linked.replica_groups.not_exists()`, one
  declaration every path reads.
- A read answers a held group as not found, not a denial: the caller may hold READ on it
  through the project, so the permission is not what keeps it out.
- The update and the purge refuse a held group as in use: only a caller holding UPDATE or
  PURGE on the group reaches the guard, and the deployment manages the group it references.

## The reads by id keep a service

- The generic ops get and bulk get read a row by its id and nothing else, so they cannot
  leave a held group out.
- `get` is wired through `single_entity` and `bulk_get_ids` through `partial_bulk`; the
  gate is the same READ check the ops shapes run.
- The searcher goes to the generic `OpsRepository`; the service holds the not-found answer
  and the per-id answer, so no domain repository is written.
- `bulk_get_ids` is partial: the gate answers per id, and the service answers each id
  that passed with the group or empty.
- An id the graph has no node for cannot be checked, so to anyone but a superadmin it is
  a denial rather than an empty slot.

## The update runs against ops

- Only `placement_direction` and `placement_enforcement` can change; the scheduler reads
  them at every placement, so members placed afterwards follow the new policy.
- The guard rides on the UPDATE statement, so the generic update needs no service method.
- Ops reads the row without its guards when there is nothing to set. The update input
  therefore refuses a call that names neither field.

## The searches run against ops

- A search takes the scope from the action, so the held-group condition rides on the
  Target rather than on the searcher.
- Groups marked deleted are left out unless the top-level filter names `deleted_at`; one
  inside `AND`/`OR`/`NOT` does not lift it. That default is the adapter's, as
  `role_preset` does it.

## The creation runs against ops

- `create` is wired through `entity_create_ops` with no service method. The action's
  scope target is the project, so the gate is session_group CREATE on that project.
- The caller becomes the owner, and the row joins its project and its owner. The domain
  is the project's, resolved by the insert, so a caller from another domain cannot put
  the group in its own.

## The purge runs against ops

- `purge` is wired through `entity_purge_ops` with no service method: the purger's guard
  carries the held-group condition, so nothing is left to branch on.
- The row and its virtual entity go together. Member sessions stay; the FK
  (`ON DELETE SET NULL`) clears their `session_group_id`.
- A replica group a concurrent transaction attaches is past the guard's snapshot, so the
  DELETE fails the FK (`replica_groups.session_group_id`, NO ACTION). Ops raises that as
  `ForeignKeyViolationError` (409).
