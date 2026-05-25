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

## DB Ops Wrapper (`ops/`)

`ops/provider.py` wraps `ExtendedAsyncSAEngine` and is the preferred way to run
standard operations. **Direction: db_sources are being migrated to ops gradually —
new and modified db_sources SHOULD use `DBOpsProvider` instead of holding the engine
and calling `session.execute` directly.** Existing db_sources stay as-is until touched.

- `DBOpsProvider(engine)` isolates the engine. Obtain session-bound ops via
  `async with provider.write_ops() as w` / `async with provider.read_ops() as r`.
  Both use READ COMMITTED. The raw engine/session is never exposed to callers.
- ops methods accept **only our spec types** (Querier/Creator/Updater/Upserter/Purger,
  `DependentCreatorSpec`) — never raw `Select/Insert/Update/Delete`.
- **Each spec owns exactly one table.** Do NOT build child-table rows inside a
  creator/updater spec. For multi-table writes, the repository coordinates the sequence
  procedurally: create the parent, build a dependency value from its result, then call
  `create_dependent` / `bulk_create_dependent` with a `DependentCreatorSpec`.
- Reads: `batch_query_with_scopes(query, querier, scopes)` is the default. Use
  `batch_query_in_global(query, querier)` **only** for superadmin-only or internal
  system paths — it bypasses RBAC scope filtering. Empty scopes raise `EmptySearchScopeError`.

## What Does NOT Belong Here

- Business logic or domain validation (belongs in `services/`).
- Exposing `Row` objects directly to callers — convert to `data/` types before returning.
