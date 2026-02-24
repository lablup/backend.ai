# Manager Models Layer — Guardrails

> This layer defines ORM schema only. For query patterns see `/repository-guide`;
> for data type conventions see `manager/data/CLAUDE.md`.

## Directory Structure (per domain)

Every domain MUST follow: `models/{domain}/__init__.py` (re-exports only) + `row.py` (ORM class).
Single-file shortcuts (`models/simple.py`) are legacy — do not add new ones.

## Row Class Rules

- Inherit from `Base` (defined in `manager/models/base.py`).
- `__tablename__` is required on every Row class.
- Cross-entity relationships: put related Row imports inside `TYPE_CHECKING` blocks only.

## No Logic in Row Classes

- Do NOT add query builder methods to Row classes — that is `repositories/db_source/`'s job.
- Do NOT add business logic methods — that is `services/`'s job.
- `session/row.py` contains legacy query methods; do NOT follow that pattern.

## Custom Column Types

- Reuse existing `TypeDecorator` wrappers from `models/base.py` whenever possible.
- New `TypeDecorator` additions go in `models/base.py` only — not in individual row files.

## `__init__.py` Rule

- Only re-export the `Row` classes declared in `row.py` — nothing else.
