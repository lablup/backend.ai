---
name: action-framework-design
type: design-rationale
description: v2 action shape families and derived permissions, audit recording principles (writes always, reads on subscription, failures always, DENIED), per-target rows for bulk, lookup existence-leak handling, public read gate, ops-backed backing axis
scope: src/ai/backend/manager/actions
keywords: [BaseSingleEntityAction, BaseScopeAction, BaseGlobalAction, BaseLookupAction, PublicActionProcessor, AuditLogPolicy, ProcessorRegistry, wired_specs, OpsBackendAction, RESTORE, soft-delete, atomic, partial]
sources:
  - src/ai/backend/manager/actions/v2
  - src/ai/backend/manager/actions/registry.py
  - src/ai/backend/manager/actions/audit_policy.py
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---

# Manager Actions layer — Knowledge

> Rules: `AGENTS.md` in the same directory.

## Why this layer exists

It wraps every service operation in a single uniform envelope so that
authorization, auditing, and metrics are enforced structurally instead of being
reimplemented per handler. An operation that bypasses it gets none of the three —
which is why handlers call processors, not services.

## Permissions are derived, not declared by actions

- The v2 bases classify actions by the shape of their target — the five families are defined in `AGENTS.md`.
- The required permission is derived from `operation_type()` — actions do not declare permissions, so the two cannot diverge.
- `RESTORE` is the only deliberate split: the behavior/audit label is restore, the checked permission is soft-delete — no new permission bit.

## Backing is orthogonal to shape

- The `OpsBackendAction` mixin (`actions/v2/ops/`) is a second independent axis: "how it executes".
- Pass-through actions carry repository specs (`to_creator()`, `to_searcher()`, ...) and run in the generic service — RBAC and auditing remain owned by the shape axis.
- The moment an operation grows branching, promote it to a service method — the generic path has no hook to hide branching in.

## A soft delete is an update the action reclassifies

- The DB operation is an UPDATE, so ops has no delete to generalize — one update
  path serves both. The split lives one layer up: the action declares
  `operation_type() == DELETE`, and that is what the RBAC check and the audit
  row's `operation` column read.
- The guard is therefore not in ops but in the spec: the general updater does
  not expose the lifecycle column, so the ordinary edit path has no field to
  make the transition with. Reaching the transition through an update-shaped
  action would record the deletion as `UPDATE` and lose it from the trail.
- The generic delete services are byte-identical to their update siblings on
  purpose. They exist to bind the delete-typed action classes at the wiring
  site, not to execute anything different.

## Many-row writes: the failure mode is named, never an argument

- `atomic_*` flushes every row together and raises on the first failure — the
  run records one failure with no entity named, because nothing was written and
  no row can be blamed.
- `partial_*` isolates each item in a savepoint and answers per item — the run
  itself succeeds and carries the verdicts.
- Not selectable by a flag: the return type differs (`list` vs
  `BulkResultWithFailures`), and that type propagates through the generic
  service, the action result and the processor. A value cannot decide four
  layers of types.
- `Bulk` names the `BaseBulkAction` shape — the caller named the entities, so
  each is answered for. A many-row write whose target is one scope, one owner or
  the system is not bulk-shaped, which is why the atomic creates are scope-,
  single-entity- and global-shaped.

## Audit principles: writes always, reads on subscription, failures always

- Write recording cannot be disabled by configuration, successful reads are recorded only when subscribed, and failures are always recorded including permission denials (`DENIED`) (`audit_policy.py`).
- Validation runs inside the monitor lifecycle so that denials leave a row.
- The reference structure is GCP audit configuration — admin activity always on / data access opt-in / policy denial always on.
- Bulk records one row per target, each with its own status — single-row alternatives (JSON arrays, child tables) trade per-target lookup for volume, and volume is a retention problem, not a schema problem.

## Lookup must not leak existence

- Lookup resolves keys before the permission check, so a distinguishable "not found" leaks existence to unauthorized callers — the reason a lookup miss and a permission denial must share the same response shape.
- Lookup metrics are labeled only by the shape of the key — value labels are a cardinality explosion.
- These metrics double as a legacy-drain indicator: a lookup whose counter stays at 0 can be deleted.

## Public means all authenticated users, not anonymous

- `PublicActionProcessor` replaces the SUPERADMIN gate with an authentication check and does nothing else.
- It is the only processor constructed together with the action class, so it rejects write operations at wiring time, not at request time.

## The registry is the catalog

- `ProcessorRegistry.wired_specs()` accumulates every wired entity-operation spec — the authoritative catalog of combinations in use.
- A sweep test compares the five bases' `__subclasses__()` against the wiring — an action that exists but is unwired is a test failure, not dead code.
