---
name: system-session-environ-service-shapes
type: design-rationale
description: system_session_environ service knowledge - why the domain has no service, why the search is global and the read by ids partial, what each is authorized against
scope: src/ai/backend/manager/services/system_session_environ
keywords: [GlobalSearchSystemSessionEnvironsAction, BulkGetSystemSessionEnvironsAction, SystemSessionEnvironProcessors, global_searcher_ops, partial_bulk_get_ops, BulkSystemSessionEnvironQuerier, global_search, bulk_get_ids]
sources:
  - src/ai/backend/manager/services/system_session_environ
  - src/ai/backend/manager/models/system_session_environ
  - src/ai/backend/manager/repositories/system_session_environ/repository.py
  - src/ai/backend/manager/models/alembic/versions/bf07cae92d86_grant_role_presets_on_system_session_environ.py
generated:
  by: claude-code/opus-5.5
  at: 2026-10-23
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
| `bulk_get_ids` | partial bulk | each named row |

## The domain has no service

- Both operations hand a spec to the generic ops services and convert the row, so no
  `service.py` method is written.
- The rows a session receives (per key the row at the most specific scope) are a branch over
  several rows; that read stays in the domain repository the launcher calls, not in ops.

## The search is global

- It reads every row at every scope, disabled ones included, so it names no scope to check.
- The global gate passes a superadmin, and a monitor for reads.

## The read by ids is partial

- It feeds the GQL DataLoader behind `node(id:)`, where one batch mixes ids from several
  resolvers. A row the caller may not read fails alone.
- Each row is checked on the graph: every user reads the public rows, a domain's or a
  project's members read its rows.
