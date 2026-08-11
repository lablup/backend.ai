---
name: data-boundary-and-sentinel
type: design-rationale
description: The data/views/dto boundary criterion (does the value leave the process), the Undefined sentinel for partial updates, the known gap between the stated purity rules and the current code
scope: src/ai/backend/manager/data
keywords: [dataclass, frozen, Undefined, sentinel, TriState, views, dto, value-object]
sources:
  - src/ai/backend/manager/data/common/sentinel.py
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---

# Manager data — Knowledge

> Rules: `AGENTS.md` in the same directory.

## The boundary criterion

There are four package axes that handle data — `data/`, `dto/`, `schema/`,
`views/`. They can exist in common and per component, but only the manager
touches the DB, so `views/` (and DB-coupled schema declarations) exist only in
the manager. Ask where the value goes:

| The value... | Location |
|---|---|
| leaves the process as (part of) an API response | `data/` — converted to a DTO in the adapter |
| is the wire format itself (validated request/response) | `dto/` (manager-only) or `common/dto/` (shared) |
| is a declaration of structure (a validatable schema type) | `schema/` — e.g. `common/schema/` |
| is an internal read projection for decisions (scheduler, coordinator) | `views/` — manager-only |

`data/` is what repositories return instead of ORM rows. It flows upward
freely; rows do not.

## The Undefined sentinel is the "not provided" marker for partial updates

- `data/common/sentinel.py` defines the `Undefined`/`undefined` singleton and pairs it with `TriState`.
- Semantics: absent = keep, sentinel = reset, value = set.
- It is the manager-side counterpart of the DTO-level SENTINEL pattern (`common/dto/manager/v2/KNOWLEDGE.md`).

## The stated rules and the current code diverge

- The purity rules (frozen dataclasses, imports from stdlib + `common.types` only) are the target state, not the current state.
- Known gaps: pydantic in several session/deployment modules, filter types in `data/common/types.py` that know SQLAlchemy columns, more mutable creator/modifier dataclasses than frozen ones.
- Treat the rules as the direction for new code — do not cite existing violations as precedent, and do not mass-fix them outside a dedicated cleanup task.
