# Manager Models layer — Guardrails

> This layer defines the ORM schema and the declarative write specs. For background, see `KNOWLEDGE.md`
> in the same directory; for query patterns see `/repository-guide`; for
> data type conventions see `manager/data/AGENTS.md`.

## Directory structure (per domain)

Every domain follows `models/{domain}/__init__.py` + `row.py` (ORM classes).
The single-file shorthand (`models/{domain}.py`) is legacy — do not add new ones.

Domains migrated to the v2 specs add them next to `row.py` — `creators.py` / `purgers.py` /
`upserters.py` / `updaters.py` for writes, `queriers.py` / `searchers.py` / `lookups.py` for
reads, `scopes.py` for the `OperationScope` subclasses that filter the row. The spec bases
live in `models/specs/` — read `models/specs/AGENTS.md` before touching them.

## Row class rules

- Inherit `Base` (defined in `manager/models/base.py`).
- Every Row class requires a `__tablename__`.
- Do NOT add new `relationship()` definitions — fetch related rows in `repositories/db_source/` queries. Existing relationships are being phased out; remove them (with their `back_populates` pair) once nothing references them.
- Inter-entity relationships: keep related Row imports inside a `TYPE_CHECKING` block only.

## Virtual entity references

- Only graph edge rows (`entity_memberships`, `scope_bindings`) reference `virtual_entities.id`
  by foreign key. A row attached to an entity (`entity_labels`, `entity_invitations`) carries the
  `(entity_type, entity_id)` pair.
- A node id never goes on a `data/` type. A Row's `to_data()` names the entity as an `EntityIdentifier`.

## No logic in Row classes

- Do NOT add query-builder methods to Row classes — that belongs to `repositories/db_source/`.
- Do NOT add business-logic methods — that belongs to `services/`.
- `session/row.py` has legacy query methods, but do not follow that pattern.

## How Rows are handled

- Handle create/delete/upsert through `models/specs/` spec declarations where possible —
  preferred over direct db-object manipulation because the RBAC side effects are enforced
  by the spec's type (rationale: `KNOWLEDGE.md`).
- Do NOT open a db session to manipulate Rows directly — the implementation belongs in a repository.

## Id column defaults

- Give every id column a `server_default`. Do not mint the value in Python.
- The generator is `uuid_generate_v7()`. No table departs from this today.
- Use `uuid_generate_v4()` only for **an id that is relied on to be unguessable**, such as
  an unsigned share link. The deciding number is the count of random bits: 62 for v7,
  122 for v4.
- Do not make a secret out of an id. Put it in its own column, the way
  `login_sessions.session_token`, `endpoint_tokens.token` and `keypairs.secret_key` do.
- Never read an id as a time. Ordering and creation time belong to the `created_at` columns.
- v7 tells the holder of an id when it was made. When a new id goes to an unauthenticated
  party, confirm that its creation time may be known.
- Changing a default changes two places: the Row declaration and an
  `ALTER COLUMN ... SET DEFAULT` in the migration. Editing only the Python declaration
  leaves a freshly created database and a migrated one with different schemas.
- A foreign key column naming an owner or a parent gets no default. An INSERT that omits
  the value must be rejected.
- The function DDL lives in `models/uuid7.py`. Execute that string rather than copying it.
- `IDColumn()`, `SessionIDColumn()` and `KernelIDColumn()` in `models/base.py` stay on v4:
  old migrations reproduce past schemas through them. Do not use them for a new table.

## Custom column types

- Where possible, reuse the existing `TypeDecorator` wrappers in `models/base.py`.
- Add new `TypeDecorator`s only to `models/base.py` — not in individual row files.
- A `SecretColumn` takes a `SecretValue`. Encrypt through the key provider pool before
  binding it — the column performs no cryptography and refuses a bare string.

## `__init__.py` rules

- Existing `__init__.py` re-export only the Row classes declared in `row.py` (nothing else) — the established pattern.
- For new code, do not add `__init__.py` re-exports; import the module directly (root global rule).
