---
name: action-framework-design
type: design-rationale
description: v2 action shapes and derived permissions, why a field row's operations are answered for by its owning entity, why a bulk field answers per row but records per entity, audit recording principles (writes always, reads on subscription, failures always, DENIED), lookup existence-leak handling, public read gate, ops-backed backing axis
scope: src/ai/backend/manager/actions
keywords: [BaseSingleEntityAction, BaseScopeAction, BaseGlobalAction, BaseLookupAction, BaseBulkLookupAction, BaseSingleFieldAction, BaseBulkFieldAction, FieldOwnerLookup, PublicActionProcessor, AuditLogPolicy, ProcessorRegistry, wired_actions, RESTORE, soft-delete]
sources:
  - src/ai/backend/manager/actions/v2
  - src/ai/backend/manager/actions/registry.py
  - src/ai/backend/manager/actions/audit_policy.py
generated:
  by: claude-code/opus-5
  at: 2026-08-18
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

- The v2 bases classify actions by the shape of their target — the shapes are listed in `AGENTS.md`.
- The required permission is derived from `operation_type()` — actions do not declare permissions, so the two cannot diverge.
- `RESTORE` is the only deliberate split: the behavior/audit label is restore, the checked permission is soft-delete — no new permission bit.

## An entity with no scope of its own is still designated by id

- A super-admin passes the entity gate, so the admin path stays open whether the
  operation is `single_entity` or `bulk`.
- No flow grants a permission on one entity yet, but a super-admin may still issue
  one. Raising the operation to `global` removes that path.
- `global` designates nothing, so it carries no `entity_id()`. Adding one for the
  audit trail invites reading it as an authorization input.

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

## A field row's operations are answered for by its owner

- Both validation and the audit trail ask which entity it was about. A field row
  carries no membership of its own, so an operation naming one has to read the owning
  entity before it has anything to answer with.
- That read runs as a lookup action. A request naming a row that is gone leaves a
  lookup failure with the key in `lookup_kind` / `lookup_key` — the one place a field
  id belongs in the trail.
- The owning entity's id is not taken from the request. Confirming that the two stand
  in that relation takes the same query anyway, and trusting it without confirming
  lets a caller pass its own owner beside somebody else's row.
- Every field write is an `UPDATE`. Adding or removing a row is a change to that
  entity, and it is that entity's permission that answers for it; a separate permission
  bit would diverge from it.

## A field bulk answers per row and records per entity

- The answer is per row the caller named. Folding it to the owner loses which item
  failed within one owner.
- The record is per owning entity, because a field id cannot go in the entity columns.
  Which row it was goes in the description.
- Rows of one owner that end differently are not folded either. Failures carry
  distinct descriptions and would not collapse anyway, and volume is a retention
  problem.
- The batch owner read is a lookup action too. Going straight to the repository leaves
  that read unrecorded and a missing row unmentioned. `bulk_lookup` answers per key,
  and a key that named nothing is a failed key rather than a failed run.

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

- `ProcessorRegistry.wired_actions()` accumulates every wired action class — the
  authoritative catalog of what is actually in use.
- A sweep test compares the v2 bases' `__subclasses__()` against the wiring — an action
  that exists but is unwired is a test failure, not dead code.
- The same sweep asserts that `action_name()` is unique. An entity type is no longer
  readable off a class — a single-entity action derives it from the id, and a field
  action has none until its owner is read — so the name alone has to tell two runs
  apart.
