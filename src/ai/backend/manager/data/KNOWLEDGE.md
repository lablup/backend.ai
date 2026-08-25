---
name: data-boundary-and-sentinel
type: design-rationale
description: the data/views/dto boundary criterion (does the value leave the process), why EntityData/FieldData carries only its own domain's row, the Undefined sentinel for partial updates, the known gap between the stated purity rules and the current code
scope: src/ai/backend/manager/data
keywords: [dataclass, frozen, Undefined, sentinel, TriState, views, dto, value-object, EntityData, FieldData, MissingGreenlet, row projection]
sources:
  - src/ai/backend/manager/data/common/sentinel.py
generated:
  by: claude-code/opus-5
  at: 2026-08-22
status: draft
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

## Carrying only the domain's own row keeps reads to what was asked for

- A value from another table makes every read that produces it reach that row too. On a
  list read that cost is multiplied by the number of rows.
- In an async session such a read raises `MissingGreenlet`. An eager load stops the
  crash, not the cost.
- A domain covered by an eager load falls outside the single-entity read/write specs
  (`models/specs/`), which assume a read expressible as one `sa.select(Row)`.

## The Undefined sentinel is the "not provided" marker for partial updates

- `data/common/sentinel.py` defines the `Undefined`/`undefined` singleton and pairs it with `TriState`.
- Semantics: absent = keep, sentinel = reset, value = set.
- It is the manager-side counterpart of the DTO-level SENTINEL pattern (`common/dto/manager/v2/KNOWLEDGE.md`).

## The stated rules and the current code diverge

- The purity rules (frozen dataclasses, imports from stdlib + `common.types` only) are the target state, not the current state.
- Known gaps: pydantic in several session/deployment modules, filter types in `data/common/types.py` that know SQLAlchemy columns, more mutable creator/modifier dataclasses than frozen ones.
- Treat the rules as the direction for new code — do not cite existing violations as precedent, and do not mass-fix them outside a dedicated cleanup task.
