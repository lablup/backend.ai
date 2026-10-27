---
name: system-session-environ-service-shapes
type: design-rationale
description: system_session_environ service knowledge - why the value source list has a service method, why it is public, what it is authorized against
scope: src/ai/backend/manager/services/system_session_environ
keywords: [PublicListSystemSessionEnvironValueSourcesAction, SystemSessionEnvironProcessors, SystemSessionEnvironService, public_list_value_sources]
sources:
  - src/ai/backend/manager/services/system_session_environ
  - src/ai/backend/common/data/system_session_environ/types.py
generated:
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
| `public_list_value_sources` | one run | authentication only |

## The value source list has a service method

- The value source list reads no row, so ops cannot back it; `SystemSessionEnvironService`
  answers it.

## The value source list is public

- The value sources are the manager's own list, not rows, so no row permission applies. It
  is wired through `public`, which checks only that the caller is logged in.
- The API carries a value source as its name rather than an enum, so a new value source
  leaves the schema unchanged.
