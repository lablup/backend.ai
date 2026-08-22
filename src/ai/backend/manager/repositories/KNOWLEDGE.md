---
name: repository-tx-and-ops
type: design-rationale
description: choosing between v2 ops, generic OpsRepository, and db objects, rationale for single-method transactions, single-table specs with DependentCreatorSpec, batch_query_with_scopes as the read default
scope: src/ai/backend/manager/repositories
keywords: [DBOpsProvider, transaction, spec, DependentCreatorSpec, batch_query_with_scopes, EmptyOperationScopeError]
sources:
  - src/ai/backend/manager/repositories/ops
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---
# Manager Repositories layer — Knowledge

> For rules, see `AGENTS.md` in the same directory.

## Choosing the data-access path

| Situation | Path |
|---|---|
| Operation serving the external API | v2 ops (`V2DBOpsProvider` + `models/specs/` types) — preferred |
| Pure pass-through (spec in, data out, no branch) | the generic `OpsRepository` through the ops-generic services — write no domain repository at all |
| Complex internal operation (multi-table, scheduler internals) | repository method over the db objects (`db_source`) |

The default is the first row; drop to db objects only when the operation genuinely
cannot be expressed as specs, and skip the repository entirely when nothing but a
pass-through would remain.

## What each spec carries, per operation

| Operation | Spec | What it carries |
|---|---|---|
| get | `DataQuerier` | row class, pk, `to_data` |
| lookup | `DataLookup` | row class, key conditions, `to_data` |
| search | `Searcher` | select, options, `to_data` |
| create | `GlobalEntityCreator` | the row alone |
| | `EntityCreator` | also provisions its scope and memberships |
| | `RoleManagedEntityCreator` | entity plus preset roles |
| update | `DataUpdater` | row class, pk, values, `to_data` |
| upsert | `EntityUpserter` | conflict keys, scope kept provisioned |
| purge | `GlobalEntityPurger` | symmetric with create |
| | `EntityPurger` | tears the scope down with the row |

- The create / purge / upsert methods are split by what the write registers, so a
  scoped spec cannot flow through a registration-free path.
- There is no `delete`: which column marks a row deleted is domain knowledge, so a
  delete action carries a `DataUpdater` and runs the update path.
- `OpsRepository` turns a missing row into `EntityNotFoundError` rather than `None` —
  that seam is the only thing it adds over ops.

## Gradual migration to the ops provider

`DBOpsProvider` in `ops/base/provider.py` is the standard path. db_source is gradually migrating to ops —
use ops for new/modified code, and leave existing code until you touch it. Isolate the engine so a raw session does not leak to the caller,
and take only spec types so arbitrary SQL cannot cross layers.

## Why the tx is gathered into a single method

Open and close the session in a public method to keep the tx boundary clear. Grouping multiple operations into a single service call
guarantees atomicity without partial commits. Splitting a method into small pieces makes the caller lose consistency across multiple txs.

## Why a spec owns only a single table

Hiding multi-table writes in a spec obscures ordering and dependencies. The repository reveals the parent→child order procedurally
and makes the dependency explicit with `DependentCreatorSpec`.

## Scope filter default

`batch_query_with_scopes` is the default in order to enforce RBAC scopes. `batch_query_in_global`
bypasses the filter, so restrict it to superadmin/internal paths, and block empty scopes with `EmptyOperationScopeError`.
