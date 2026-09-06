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
- ❌ MUST NOT construct an ops object. `V2WriteOps(session)`, `V2ReadOps(session)` and
  every form of it are forbidden, with no exception. ✅ Take ops from a provider's
  `write_ops()` / `read_ops()`. The transaction boundary has to belong to the provider,
  or nothing holds the work to the transaction the method opened.
- ✅ MUST inject a provider into a repository — never a session, never an engine. A
  repository holding an engine can open a session inside itself, which is the rule above
  broken. The new path is `V2DBOpsProvider`.
- A primitive only one domain uses does NOT go on the general ops. Write ops extending
  `V2WriteOps` and a provider extending `V2DBOpsProvider` that overrides `write_ops()`,
  and inject that provider only into the repositories needing the primitive
  (`ops/v2/reconciler/`, `ops/rbac/`, `ops/user/`).
- Separating into a repository is the default; internal operations may use db directly.
- ops methods take only spec types (Querier/Creator/Updater/Upserter/Purger, `DependentCreatorSpec`).
  A single spec owns only a single table.
- Do NOT do multi-table writes inside a spec. The repository creates the parent first, then composes the dependent values
  from the result and passes them to `create_dependent` / `bulk_create_dependent` as a `DependentCreatorSpec`.
- The read default is `batch_query_with_scopes`. `batch_query_in_global` is for superadmin/internal paths only.
- Graph relations are written through three provider / ops pairs only. Entity write
  (`V2DBOpsProvider` / `V2WriteOps`: create and delete, own and govern written at
  creation), relation write (`RelationOpsProvider` / `V2RelationWriteOps`: create and
  purge a relation), share write (`ShareOpsProvider` / `V2ShareWriteOps`: share, widen,
  narrow, unshare, accept an invitation, transfer). A repository is injected the one
  pair it needs.
- Do NOT assume the graph ops are reachable from anywhere. The own and govern
  primitives live on the base the three ops share (`V2GraphWriteOpsBase`), and no
  provider hands that base out.

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
