# Manager Repositories layer — Contexts

> For rules, see `AGENTS.md` in the same directory.

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
bypasses the filter, so restrict it to superadmin/internal paths, and block empty scopes with `EmptySearchScopeError`.
