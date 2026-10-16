---
name: session-group-service-shapes
type: decision-table
description: session_group knowledge - why the reads by id keep a service while the two searches and the update run against ops, how a deployment's group is left out of every user read and write, why the bulk read is partial
scope: src/ai/backend/manager/services/session_group
keywords: [GetSessionGroupAction, BulkGetSessionGroupsAction, GlobalSearchSessionGroupsAction, ScopedSearchSessionGroupsAction, UpdateSessionGroupAction, SessionGroupUpdater, GuardCheck, SessionGroupService, OpsRepository, SessionGroupTarget, replica_groups, partial_bulk, single_entity]
sources:
  - src/ai/backend/manager/services/session_group
  - src/ai/backend/manager/repositories/ops/repository.py
  - src/ai/backend/manager/models/session_group
generated:
  by: claude-code/opus-5.5
  at: 2026-10-15
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

## A deployment's group is left out of every user read and write

| Operation | Where the group is left out |
|---|---|
| `get` | The action's searcher matches the row only when no replica group holds it; the service answers not found otherwise |
| `bulk_get_ids` | The same searcher for many ids; a held group answers empty |
| `scoped_search` | Every `SessionGroupTarget` adds the same condition to its scope condition |
| `global_search` | Not left out: the superadmin sees every group |
| `update` | `SessionGroupUpdater` carries the condition as a `GuardCheck` whose error is not found |

- The condition is `SessionGroupSearchableFields.linked.replica_groups.not_exists()`, one
  declaration every path reads.
- A held group answers not found, not a denial: the caller may hold READ on it through
  the project, so the permission is not what keeps it out.

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
