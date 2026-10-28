---
name: system-session-environ-service-shapes
type: design-rationale
description: system_session_environ service knowledge - why the row operations have no service method while the value source list does, why the search is global, the list public, the update, the soft delete and the restore per row and the read by ids partial, what each is authorized against
scope: src/ai/backend/manager/services/system_session_environ
keywords: [GlobalSearchSystemSessionEnvironsAction, PublicListSystemSessionEnvironValueSourcesAction, UpdateSystemSessionEnvironAction, DeleteSystemSessionEnvironAction, RestoreSystemSessionEnvironAction, BulkGetSystemSessionEnvironsAction, SystemSessionEnvironProcessors, SystemSessionEnvironService, public_list_value_sources, global_searcher_ops, single_update_ops, single_delete_ops, single_restore_ops, partial_bulk_get_ops, BulkSystemSessionEnvironQuerier, global_search, bulk_get_ids]
sources:
  - src/ai/backend/manager/services/system_session_environ
  - src/ai/backend/manager/models/system_session_environ
  - src/ai/backend/manager/repositories/system_session_environ/repository.py
  - src/ai/backend/manager/models/alembic/versions/bf07cae92d86_grant_role_presets_on_system_session_environ.py
generated:
  by: claude-code/opus-5.5
  at: 2026-10-23
updated:
  by: claude-code/opus-5.5
  at: 2026-10-27
status: draft
---

# System session environ service — Knowledge

> Rules: `../AGENTS.md`. Wiring: `backend.ai mgr ops list`.

A system session environ row binds a value of a starting session to an environment variable
name at the public scope, a domain or a project. The launcher reads the rows through the
domain repository; this package holds the operations a caller reaches through the API.

## The processor fields

| Field | Failure mode | Authorized against |
|---|---|---|
| `global_search` | one run | the `global` singleton, by entity type |
| `public_list_value_sources` | one run | authentication only |
| `update` | one row | the named row |
| `delete` | one row | the named row |
| `restore` | one row | the named row |
| `bulk_get_ids` | partial bulk | each named row |

## Only the value source list has a service method

- The row operations hand a spec to the generic ops services and convert the row, so they
  have no `service.py` method.
- The value source list reads no row, so ops cannot back it; `SystemSessionEnvironService`
  answers it.
- The rows a session receives (per key the row at the most specific scope) are a branch over
  several rows; that read stays in the domain repository the launcher calls, not in ops.

## The search is global

- It reads every row at every scope, soft-deleted ones included, so it names no scope to check.
- The global gate passes a superadmin, and a monitor for reads.

## The value source list is public

- The value sources are the manager's own list, not rows, so no row permission applies. It
  is wired through `public`, which checks only that the caller is logged in.
- The API carries a value source as its name rather than an enum, so a new value source
  leaves the schema unchanged. The adapter refuses a name the manager does not provide.

## The update is per row

- It changes the key only. The scope and the value source stay fixed: moving a row to another
  scope would move its membership in the graph.
- The UPDATE grant on the row answers: a project's admins for its rows, a domain's admins for
  the domain's rows and its projects' (the graph binds a project under its domain), a
  superadmin for every row. Nobody else holds UPDATE on the public rows.
- The database refuses a key another row at the same scope holds, and a key that is not an
  environment variable name. The updater maps both to the domain errors.
- A soft-deleted row is refused; restore it first.

## Soft delete and restore are per row

- They write `deleted_at` through the shared soft delete updaters. The launcher leaves out a
  soft-deleted row, so the sessions started after a delete no longer receive it.
- The SOFT_DELETE grant on the row answers both, held by the same admins as UPDATE.
- A soft-deleted row keeps its key: no other row at the same scope takes it until the
  deleted row is purged, so a restore is never refused for its key.
- The seed upserts on the same key, soft-deleted rows included. After a delete it skips the
  key; an overwrite rewrites the deleted row's value source and leaves it deleted.

## The read by ids is partial

- It feeds the GQL DataLoader behind `node(id:)`, where one batch mixes ids from several
  resolvers. A row the caller may not read fails alone.
- Each row is checked on the graph: every user reads the public rows, a domain's or a
  project's members read its rows.
