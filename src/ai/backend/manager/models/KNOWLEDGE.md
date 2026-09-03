---
name: models-schema-declaration
type: design-rationale
description: models as the schema-declaration layer (per-domain row packages), why Rows carry no implementation, why models/specs specs are preferred over direct db-object manipulation (RBAC side effects), the rationale for avoiding direct session use and keeping implementation in repositories, why id defaults split between UUIDv7 and UUIDv4
scope: src/ai/backend/manager/models
keywords: [Row, ORM, specs, RBAC, session, repository, schema, alembic, uuid_generate_v7, server_default]
sources:
  - src/ai/backend/manager/models/specs
  - src/ai/backend/manager/models/uuid7.py
generated:
  by: claude-code/opus-5
  at: 2026-09-03
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

## Why id defaults split between v7 and v4

- The leading 60 bits of a UUIDv7 are the generation time, so a new row's id lands at the
  right edge of the primary key index instead of scattering across it the way v4 does.
  The busier the table is written, the more this is worth.
- The price is that the id reveals when it was made. That is harmless for an internal
  identifier, but an id handed to an untrusted holder leaks its issue time on its own.
  Tokens and invitations therefore stay on v4.
- v4 and v7 are both the `uuid` type, so a column may hold a mix. Existing rows never need
  to be rewritten.
- The function is strictly increasing within a session: it remembers the last value it
  handed out in a session setting and steps up by the smallest unit when the clock has not
  advanced. This matches PostgreSQL 18's built-in `uuidv7()`; once 18 is the minimum, the
  body becomes `RETURN uuidv7();`.
- Because it mutates session state, it is not marked parallel safe.
