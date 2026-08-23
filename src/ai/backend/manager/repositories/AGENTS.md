# Manager Repositories layer — Guardrails

> For background, see `KNOWLEDGE.md` in the same directory; for implementation patterns, the `/repository-guide` skill.

## Directory structure (per domain)

- `repository.py` (single-entity CRUD), `repositories.py` (multi-entity container / `RepositoryArgs`),
  `types.py` (SearchResult), `options.py` (QueryCondition/QueryOrder),
  `db_source/db_source.py` (queries). Optional: `updaters.py`, for the legacy
  `UpdaterSpec` only.
- Every v2 spec — read as well as write — is declared next to its row under `models/`:
  `queriers.py`, `searchers.py`, `lookups.py`, `updaters.py`, `creators.py`, `purgers.py`,
  `upserters.py`. `scopes.py` (OperationScope) is declared there too. What stays here is
  the repositories and the queries they run.
- Separate out db_source so it is clear which source a Repository uses.
- Do NOT write a `repository.py` / `db_source.py` for an operation that only hands a spec to
  ops and converts the row: `repositories/ops/repository.py` already does that for
  get / search / create / update / purge. Write the spec files and wire `OpsRepository`.
  Write the method yourself the moment the operation needs a branch, a multi-table write,
  or its own not-found error.

## Method naming

- Getters use the entity name without `get_`: `user(id)`, `session(id)`.
- The standard 6: `create` / `{entity}` / `search` / `update` / `delete` / `purge`.

## Data access

- New write specs use the `models/specs/` lineage only:
  - write specs: `GlobalEntity*` / `Entity*` / `RoleManagedEntity*` / `FieldEntity*` (Creator/Purger/Upserter)
  - read/update: `DataQuerier`, `DataLookup`, `Searcher`, `DataUpdater`
- No new use of the legacy specs — transition-only maintenance of existing code:
  - `repositories/base/`: `CreatorSpec`, `DataCreator`, `UpserterSpec`, `PurgerSpec`
  - `repositories/base/rbac/`: the `RBACEntityCreator` / `RBACEntityUpserter` / `RBACEntityPurger` set
  - Judge by import path (`models.specs.*` is v2) — `repositories.base` re-exports some
    v2 types and bridge classes like `DataBatchPurger` share names, so never judge by
    the class name alone.
- A v2 ops method that writes several rows names its failure mode: `atomic_*` raises and
  writes nothing on the first failure, `partial_*` isolates each item in a savepoint and
  answers per item. There is no unmarked default, and the two are never selected by an
  argument — the return type differs (`list` vs `BulkResultWithFailures`).
- The new path for the standard six operations is `OpsRepository` (`V2DBOpsProvider`).
  The legacy `DBOpsProvider` path (including `create_dependent` and
  `create_with_next_value`) is for existing code only — when a new domain needs those
  capabilities, report it as a v2 gap (see the demotion mapping in `services/KNOWLEDGE.md`).
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

## OperationScope

- `@dataclass(frozen=True)`, implement `to_condition() -> QueryCondition`.
- Declare it in `models/{domain}/scopes.py`, next to the row it filters.

## What does NOT belong here

- Business logic / domain validation (belongs to services/).
- Exposing `Row` directly — convert to a `data/` type before returning.
