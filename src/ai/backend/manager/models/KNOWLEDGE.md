---
name: models-schema-declaration
type: design-rationale
description: models as the schema-declaration layer (per-domain row packages), why Rows carry no implementation, why models/specs specs are preferred over direct db-object manipulation (RBAC side effects), the rationale for avoiding direct session use and keeping implementation in repositories
scope: src/ai/backend/manager/models
keywords: [Row, ORM, specs, RBAC, session, repository, schema, alembic]
sources:
  - src/ai/backend/manager/models/specs
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---

# Manager models — Knowledge

> Rules: `AGENTS.md` in the same directory.

## Why this package exists

It is the declaration layer of the DB schema — per-domain packages
(`models/{domain}/row.py`) hold the table structure, and `models/specs/` holds
the write declarations. This document covers why it holds "declarations only,
no implementation".

## Rows are declarations and carry no implementation

- A Row is a declaration of table structure — the moment query builders or business methods attach to it, logic appears that gets called outside session/transaction boundaries and the layering collapses.
- The per-domain package split exists to narrow the blast radius of a schema change to that domain.
- The legacy query methods in `session/row.py` are a remaining counterexample, not something to imitate.

## Object manipulation should go through specs

- Handle create/delete/upsert via the spec declarations in `models/specs/` where possible — preferred over manipulating db objects directly.
- Reason: RBAC side effects (scope provisioning, membership registration) are decided by the **spec's type** — inserting a Row directly silently skips those side effects ([specs/KNOWLEDGE.md](specs/KNOWLEDGE.md)).

## Do not manipulate models directly through a session

- Avoid code that opens a db session and manipulates Rows directly — implementation belongs in the repository.
- Reason one: transaction boundaries are the repository's responsibility, so scattered direct sessions break atomicity guarantees.
- Reason two: direct sessions become the channel through which Rows leak into layers above the repository — a bypass of the layering rule that Rows do not rise above `repositories/`.
