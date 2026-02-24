# Manager Repositories Layer — Guardrails

> For full implementation patterns, see the `/repository-guide` skill.

## Directory Structure (per domain)

Core files per domain: `repository.py` (single-entity CRUD interface), `repositories.py`
(multi-entity container / `RepositoryArgs`), `types.py` (SearchScope + SearchResult),
`options.py` (QueryCondition/QueryOrder enums), `db_source/db_source.py` (all queries).
Optional per-operation helpers: `creators.py`, `updaters.py`, `purgers.py`, `upserters.py`.

## Method Naming

- Getter method uses the entity name, not `get_`: e.g., `user(id)`, `session(id)`.
- Standard six operations: `create` / `{entity}` / `search` / `update` / `delete` / `purge`.

## Transaction Rules

- `begin_session()` for writes, `begin_readonly_session()` for reads.
- Each public method owns its own transaction boundary.
- NEVER accept a DB session from the caller (Service layer does not manage sessions).

## SearchScope Rules

- Must be `@dataclass(frozen=True)`.
- Must implement `to_condition() -> QueryCondition` (singular, defined in `types.py`).

## DB Source Rules

- All SQLAlchemy query code belongs in `db_source/db_source.py`.
- `repository.py` only delegates — no query logic allowed there.

## What Does NOT Belong Here

- Business logic or domain validation (belongs in `services/`).
- Exposing `Row` objects directly to callers — convert to `data/` types before returning.
