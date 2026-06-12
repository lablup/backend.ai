# Manager Repositories layer — Guardrails

> For background, see `CONTEXTS.md` in the same directory; for implementation patterns, the `/repository-guide` skill.

## Directory structure (per domain)

- `repository.py` (single-entity CRUD), `repositories.py` (multi-entity container / `RepositoryArgs`),
  `types.py` (SearchScope + SearchResult), `options.py` (QueryCondition/QueryOrder),
  `db_source/db_source.py` (queries). Optional: `creators.py` / `updaters.py` / `purgers.py` / `upserters.py`.
- Separate out db_source so it is clear which source a Repository uses.

## Method naming

- Getters use the entity name without `get_`: `user(id)`, `session(id)`.
- The standard 6: `create` / `{entity}` / `search` / `update` / `delete` / `purge`.

## Data access

- For general API paths, prefer using `DBOpsProvider` (`write_ops` / `read_ops`). Internal operations may use db directly,
  but separating into a repository is the default.
- ops use the default provider; keep a separate provider only for common operations in specific situations such as sokovan.
- ops methods take only spec types (Querier/Creator/Updater/Upserter/Purger, `DependentCreatorSpec`).
  A single spec owns only a single table.
- Do NOT do multi-table writes inside a spec. The repository creates the parent first, then composes the dependent values
  from the result and passes them to `create_dependent` / `bulk_create_dependent` as a `DependentCreatorSpec`.
- The read default is `batch_query_with_scopes`. `batch_query_in_global` is for superadmin/internal paths only.

## Transactions

- The isolation level is always READ COMMITTED.
- Complete the work within a single method that received ops, so the tx is guaranteed.
- When using db directly, handle repository methods at once per service/operation. Split only when there is a clear layer
  boundary, and align repository methods to the service operation.
- Create db sessions only in public methods, and reuse them only in private methods.

## SearchScope

- `@dataclass(frozen=True)`, implement `to_condition() -> QueryCondition` (`types.py`).

## What does NOT belong here

- Business logic / domain validation (belongs to services/).
- Exposing `Row` directly — convert to a `data/` type before returning.
