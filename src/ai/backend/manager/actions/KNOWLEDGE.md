---
name: action-framework-design
type: design-rationale
description: v2 action shape families and derived permissions, audit recording principles (writes always, reads on subscription, failures always, DENIED), per-target rows for bulk, lookup existence-leak handling, public read gate, ops-backed backing axis
scope: src/ai/backend/manager/actions
keywords: [BaseSingleEntityAction, BaseScopeAction, BaseGlobalAction, BaseLookupAction, PublicActionProcessor, AuditLogPolicy, ProcessorRegistry, wired_specs, OpsBackendAction, RESTORE]
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
