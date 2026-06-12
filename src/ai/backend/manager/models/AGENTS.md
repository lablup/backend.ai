# Manager Models layer — Guardrails

> This layer defines only the ORM schema. For query patterns see `/repository-guide`; for data type conventions see
> `manager/data/AGENTS.md`.

## Directory structure (per domain)

Every domain follows `models/{domain}/__init__.py` (re-export only) + `row.py` (ORM classes).
The single-file shorthand (`models/{domain}.py`) is legacy — do not add new ones.

## Row class rules

- Inherit `Base` (defined in `manager/models/base.py`).
- Every Row class requires a `__tablename__`.
- Inter-entity relationships: keep related Row imports inside a `TYPE_CHECKING` block only.

## No logic in Row classes

- Do NOT add query-builder methods to Row classes — that belongs to `repositories/db_source/`.
- Do NOT add business-logic methods — that belongs to `services/`.
- `session/row.py` has legacy query methods, but do not follow that pattern.

## Custom column types

- Where possible, reuse the existing `TypeDecorator` wrappers in `models/base.py`.
- Add new `TypeDecorator`s only to `models/base.py` — not in individual row files.

## `__init__.py` rules

- Re-export only the Row classes declared in `row.py` — nothing else.
