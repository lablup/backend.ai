---
name: views-decision-slices
type: design-rationale
description: Views as per-stage decision slices rather than entity mirrors, one-way dependency from views to data, derived aggregates as first-class fields, recommended use across internal-behavior layers
scope: src/ai/backend/manager/views
keywords: [view, projection, sokovan, reconcile, replica_group, read-model]
sources:
  - src/ai/backend/manager/views/replica_group.py
  - src/ai/backend/manager/views/sokovan
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---

# Manager views — Knowledge

> Rules: `AGENTS.md` in the same directory.

## Why this package exists

It is the read-projection space that holds the shapes of the inputs internal
decision-making (scheduler, coordinator, reconciler) receives. Keeping it
separate from API-bound values (`data/`) prevents decision shapes from being
dragged around by the API contract.

## A view is a decision slice, not an entity mirror

- A view is the shape of the input one decision receives — one entity having multiple views is normal (replica group has five, one per reconcile stage, named `{Entity}{Stage}View`).
- **Derived aggregates that exist in no table** (live/serving/target counts) are first-class fields — the repository performs the aggregation, and the view is the shape of that answer.
- Views may nest child views (a terminating session holds its terminating kernels) — `data/` types generally do not.

## Dependency is one-way, and views are recommended wherever internal behavior is handled

- `views/` may import identifiers/schemas from `data/` and `common` — never the reverse.
- The largest consumer today is sokovan (nearly every module under `views/sokovan/`), but it is not sokovan-exclusive — **using views is recommended for objects that deal only with internal behavior**.
- Planned consumers: entity lifecycle managers (objects handling the lifecycle of user, project, vfolder, image, etc.) will also primarily use views.
- The criterion for adding one: "is this a slice needed for an internal decision" — if the same shape would ever appear in an API payload, it belongs in `data/`.
