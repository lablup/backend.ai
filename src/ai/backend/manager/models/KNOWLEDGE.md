---
name: models-schema-declaration
type: design-rationale
description: models as the schema-declaration layer (per-domain row packages), why Rows carry no implementation, why models/specs specs are preferred over direct db-object manipulation (RBAC side effects), the rationale for avoiding direct session use and keeping implementation in repositories, why every id default is UUIDv7
scope: src/ai/backend/manager/models
keywords: [Row, ORM, specs, RBAC, session, repository, schema, alembic, uuid_generate_v7, server_default, creator_id, personal project, dangling]
sources:
  - src/ai/backend/manager/models/specs
  - src/ai/backend/manager/models/uuid7.py
  - src/ai/backend/manager/models/project/row.py
generated:
  by: claude-code/opus-5
  at: 2026-09-05
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

## Why every id default is v7

- The leading 60 bits of a UUIDv7 are the generation time, so a new row's id lands at the
  right edge of the primary key index instead of scattering across it the way v4 does. Two
  things follow. An insert always touches one page that is already cached, and reading
  recent rows keeps the hot index pages down to a few. Heap page placement is decided by
  insert order, so it is not part of this gain.
- The size of the gain is the product of how far the index exceeds the cache and how often
  the table is written. On a table of a few thousand rows the whole index stays resident and
  the difference is not measurable; on a table of millions it shows up directly as random
  disk reads.
- One generator for every table. Letting it vary per table forces the next person to make
  the judgement again.
- What v7 costs is that the holder of an id learns when it was made. In this schema whoever
  can see an id can also see the row's `created_at`, so nothing new leaks.
- 62 bits are random. The leading 48 hold a millisecond timestamp and the next 12 a
  sub-millisecond tick, leaving the rest. That is fewer than v4's 122, so a value that is
  relied on to be unguessable belongs in its own column rather than in the id.
- v4 and v7 are both the `uuid` type, so a column may hold a mix. Existing rows never need
  to be rewritten.
- The function is strictly increasing within a session: it remembers the last value it
  handed out in a session setting and steps up by the smallest unit when the clock has not
  advanced. This matches PostgreSQL 18's built-in `uuidv7()`; once 18 is the minimum, the
  body becomes `RETURN uuidv7();`.
- Because it mutates session state, it is not marked parallel safe.

## Creator columns and the rows left behind

Since BEP-1077, ownership is answered by the `scope -> virtual_entity -> entity` path
alone. That is why no row carries an `owner_*` column — it would leave two answers to
the same question, exactly the state the BEP set out to remove.

`creator_id` answers a different question: **which user did this row come into being
for**. Provenance, not ownership, so it takes no part in an access decision. The
distinction is forced by personal projects. One is created together with its user, so
something has to answer "which project is this user's", and reading that off the graph
would answer an ownership question with view membership. The roster is also due to be
rewritten as shares, so its shape moves; the column does not.

### After the user is gone

The foreign key is `ON DELETE SET NULL`. A user purge does not take the project.

- What the project holds outlives the account. Destroying a personal folder in the same
  transaction that removes the user row leaves no way to hand the data over.
- Deleting a project means clearing out the resources in it, which is asynchronous work.
  It does not belong in a synchronous purge transaction.
- So a personal project holding a NULL creator is **dangling**, and the retention sweep
  collects it. A delete request that wants the project gone too says so through an API
  option; the deletion itself stays asynchronous.

On a general project `creator_id` is plain audit information and an empty one means
nothing. That is why the key is not `RESTRICT`: a team project someone created long ago
must not block their purge.

### How many

A user has at most one personal project, held by a partial unique index. Dangling ones
carry NULL, and NULLs do not collide in a unique index, so any number of them coexist.
