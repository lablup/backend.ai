---
Author: Gyubong Lee (gbl@lablup.com)
Status: Draft
Created: 2026-02-23
Created-Version: 26.3.0
Target-Version:
Implemented-Version:
---

# Zero-Downtime Deployment Strategy Architecture

## Related Issues

- Parent BEP: [BEP-1006: Service Deployment Strategy](BEP-1006-service-deployment-strategy.md)
- Related BEP: [BEP-1030: Sokovan Scheduler Status Transition Design](BEP-1030-sokovan-scheduler-status-transition.md)

## Motivation

BEP-1006 defined the high-level design for Blue-Green and Rolling Update deployment strategies. This BEP covers the **implementation architecture** — how these strategies integrate into the existing Sokovan deployment lifecycle system.

Core problem: **Deployment strategies are inherently multi-cycle, spanning multiple coordinator processing cycles before completion or rollback.**

Blue-Green deployment spans multiple coordinator cycles through several phases:

1. **Cycle 1**: Create Green routes with `INACTIVE` traffic → still `DEPLOYING`
2. **Cycle 2-N**: Green routes still provisioning → still `DEPLOYING`
3. **Cycle N+1**: All Green routes healthy → switch traffic, transition to `READY`

Rolling Update similarly progresses gradually across cycles. Both strategies **keep the deployment in `DEPLOYING` state across multiple processing cycles until strategy completion or rollback.**

### Flat Registry with Per-Handler Evaluation

DEPLOYING sub-step handlers are registered **flat** in the coordinator's `HandlerRegistry` alongside other lifecycle handlers, keyed by `(lifecycle_type, sub_step)`. Each DEPLOYING handler calls the strategy evaluator and applier **directly in its `execute()` method** — there is no separate pre-step phase. The evaluator determines sub-step assignments and route mutations; the applier persists them to DB.

| Aspect | How it works |
|--------|-------------|
| **State transition** | Each handler returns `status_transitions()` with `success/need_retry/expired/give_up` → coordinator's generic path handles all transitions |
| **Dispatch** | Coordinator looks up handler by `(lifecycle_type, sub_step)` key and runs it directly |
| **Evaluation** | Each handler calls `evaluator.evaluate()` + `applier.apply()` in its own `execute()` |


## Sub-documents

| Document | Description |
|----------|-------------|
| [Rolling Update](BEP-1049/rolling-update.md) | Gradual route replacement strategy — max_surge/max_unavailable control |
| [Blue-Green](BEP-1049/blue-green.md) | Atomic traffic switch strategy — INACTIVE staging + promotion |

## Proposed Design

### Overall Architecture

Core idea: The coordinator maintains a `HandlerRegistry` with a flat `(lifecycle_type, sub_step)` key. Simple lifecycle types (CHECK_PENDING, SCALING, etc.) register with `sub_step=None`. DEPLOYING registers three handlers — one for PROVISIONING, one for PROGRESSING (which also handles COMPLETED and ROLLED_BACK terminal states), and one for ROLLING_BACK. Each handler independently calls the strategy evaluator and applier.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          Periodic Task Scheduler                             │
│                                                                              │
│  DeploymentTaskSpec                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐      │
│  │ check_pending:           2s / 30s                                  │      │
│  │ check_replica:           5s / 30s                                  │      │
│  │ scaling:                 5s / 30s                                  │      │
│  │ deploying/provisioning:  5s / 30s  ← drives PROVISIONING cycle    │      │
│  │ deploying/progressing:   5s / 30s  ← drives PROGRESSING cycle     │      │
│  │ deploying/rolling_back:  5s / 30s  ← drives ROLLING_BACK cycle    │      │
│  │ reconcile:               -- / 30s                                  │      │
│  │ destroying:              5s / 60s                                  │      │
│  └─────────────┬──────────────────────────────────────────────────────┘      │
│                │                                                             │
│                ▼                                                             │
│  DoDeploymentLifecycleEvent                                                  │
│  DoDeploymentLifecycleIfNeededEvent                                          │
│  (lifecycle_type: str, sub_step: str | None)                                 │
└────────────────┬─────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         DeploymentCoordinator                                │
│                                                                              │
│  process_deployment_lifecycle(lifecycle_type, sub_step=None)                 │
│    handler = registry.handlers[(lifecycle_type, sub_step)]                   │
│    acquire lock if handler.lock_id                                          │
│    _run_handler(handler)                                                     │
│                                                                              │
│  HandlerRegistry:                                                            │
│    handlers: dict[(DeploymentLifecycleType, DeploymentSubStep | None),       │
│                   DeploymentHandler]                                          │
│                                                                              │
│    handlers = {                                                              │
│      (CHECK_PENDING, None)           → CheckPendingHandler                   │
│      (CHECK_REPLICA, None)           → CheckReplicaHandler                   │
│      (SCALING, None)                 → ScalingHandler                        │
│      (RECONCILE, None)               → ReconcileHandler                      │
│      (DEPLOYING, PROVISIONING)       → DeployingProvisioningHandler          │
│      (DEPLOYING, PROGRESSING)        → DeployingProgressingHandler           │
│      (DEPLOYING, ROLLING_BACK)       → DeployingRollingBackHandler           │
│      (DESTROYING, None)              → DestroyingHandler                     │
│    }                                                                         │
│                                                                              │
│  _run_handler(handler):                                                      │
│    1. Query deployments by handler.target_statuses()                         │
│    2. Build attempt context from scheduling history                          │
│    3. Execute handler + handle status transitions                            │
│    4. Classify failures (give_up / expired / need_retry)                     │
│    5. Post-process (reschedule, trigger dependent lifecycles)                │
│                                                                              │
│  Result handling (same generic path for all handlers):                       │
│    successes  → success status (transition + history + sub_step update)      │
│    errors     → classified into give_up / expired / need_retry               │
│    skipped    → no transition (still in progress)                            │
└────────────────┬─────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  DeploymentHandler (base)                                                    │
│  ├─ name()               → str                              ← abstract      │
│  ├─ lock_id              → LockID | None                     ← abstract     │
│  ├─ target_statuses()    → list[DeploymentLifecycleStatus]   ← abstract     │
│  ├─ status_transitions() → DeploymentStatusTransitions       ← abstract     │
│  ├─ execute(deployments) → DeploymentExecutionResult         ← abstract     │
│  └─ post_process(result) → None                              ← abstract     │
│                                                                              │
│  DEPLOYING handlers (3 total):                                               │
│  ├─ DeployingProvisioningHandler                                             │
│  │    targets: [(DEPLOYING, PROVISIONING)]                                   │
│  │    execute: evaluator.evaluate() + applier.apply()                        │
│  │    success → DEPLOYING/PROGRESSING                                        │
│  │    expired/give_up → DEPLOYING/ROLLING_BACK                               │
│  │                                                                           │
│  ├─ DeployingProgressingHandler                                              │
│  │    targets: [(DEPLOYING, PROGRESSING),                                    │
│  │              (DEPLOYING, COMPLETED),                                      │
│  │              (DEPLOYING, ROLLED_BACK)]                                    │
│  │    execute: evaluator.evaluate() + applier.apply()                        │
│  │    success (COMPLETED/ROLLED_BACK) → READY                                │
│  │    skipped (still PROGRESSING) → no transition                            │
│  │    expired/give_up → DEPLOYING/ROLLING_BACK                               │
│  │                                                                           │
│  └─ DeployingRollingBackHandler                                              │
│       targets: [(DEPLOYING, ROLLING_BACK)]                                   │
│       execute: evaluator.evaluate() + applier.apply()                        │
│       success → DEPLOYING/ROLLED_BACK                                        │
│       expired/give_up → DEPLOYING/ROLLED_BACK                                │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Revision Activation Trigger Branching

Revision switching (`activate_revision`) and general updates (`update_deployment`) take different paths:

```
activate_revision(deployment_id, revision_id)
    │
    ├─ Guard: lifecycle == DEPLOYING?
    │    → Yes: raise DeploymentAlreadyInProgress
    │
    ├─ Policy lookup: deployment_policy exists with strategy?
    │
    ├─ No policy or no strategy (existing behavior)
    │    → current_revision = revision_id (immediate swap)
    │    → mark("check_replica")
    │
    └─ Policy with strategy (ROLLING / BLUE_GREEN)
         → begin_deployment(endpoint_id, revision_id)
            ├─ deploying_revision = revision_id
            └─ lifecycle = DEPLOYING
         → mark("deploying")

update_deployment(replica_count, metadata, ...)
    │
    └─ Always mark("check_replica")  ← strategy-independent
```

Replica count changes are additions/removals of the same revision, so no strategy is needed.
Only revision switching requires safe replacement of new code/models, so it uses the strategy path.

### Auto-Scaling Exclusion During Deployment

Endpoints in `DEPLOYING` state are excluded from auto-scaling rule evaluation. During a strategy-based deployment, the evaluator is actively managing route creation and termination (surge/unavailable for Rolling Update, Green staging for Blue-Green). If auto-scaling were to concurrently add or remove routes, it would conflict with the evaluator's route management — potentially violating surge limits, terminating routes the evaluator expects to exist, or creating routes with the wrong revision.

Auto-scaling resumes automatically once the deployment completes and the endpoint returns to `READY`.

### Sub-Step Variants

Both Blue-Green and Rolling Update cycle FSMs share a common set of **sub-step variants**. The evaluator assigns each deployment a sub-step; the applier writes it to the `sub_step` column.

| Sub-Step | Description | Handled by | Transition |
|----------|-------------|------------|------------|
| **PROVISIONING** | New routes being created or still provisioning | DeployingProvisioningHandler | success → DEPLOYING/PROGRESSING, skipped (still provisioning) → no transition, failure → DEPLOYING/ROLLING_BACK |
| **PROGRESSING** | Strategy making active progress — routes being replaced | DeployingProgressingHandler | skipped (still progressing) → no transition, failure → DEPLOYING/ROLLING_BACK |
| **COMPLETED** | All strategy conditions met — revision swap done | DeployingProgressingHandler | success → READY |
| **ROLLING_BACK** | Actively rolling back — terminating new-revision routes, restoring previous revision | DeployingRollingBackHandler | success → DEPLOYING/ROLLED_BACK, failure → DEPLOYING/ROLLED_BACK |
| **ROLLED_BACK** | Rollback complete — deploying_revision cleared | DeployingProgressingHandler | success → READY |

### DeploymentStrategyEvaluator

`DeploymentStrategyEvaluator` evaluates DEPLOYING-state deployments and determines their sub-step assignments and route mutations. Each DEPLOYING handler owns an evaluator+applier pair and calls them in `execute()`.

#### Execution Flow

```
DeploymentStrategyEvaluator.evaluate(deployments)
    │
    │  Phase 1: Load policies and routes
    │  ┌─────────────────────────────────────────────────────────┐
    │  │  policy_map = load_policies(deployments)                │
    │  │  route_map = search_routes(non-terminated)               │
    │  └─────────────────────────────────────────────────────────┘
    │
    │  Phase 2: Run per-deployment strategy FSM
    │  ┌─────────────────────────────────────────────────────────┐
    │  │  for deployment in deployments:                         │
    │  │    policy = policy_map[deployment.id]                   │
    │  │    routes = route_map[deployment.id]                    │
    │  │                                                         │
    │  │    strategy_fsm = create_strategy(policy)                │
    │  │    cycle_result = strategy_fsm.evaluate_cycle(...)      │
    │  │                                                         │
    │  │    assignments[deployment.id] = cycle_result.sub_step   │
    │  │    route_changes.merge(cycle_result.route_changes)       │
    │  └─────────────────────────────────────────────────────────┘
    │
    ▼
  StrategyEvaluationSummary {
    assignments: {
      deploy_A_id: PROVISIONING,
      deploy_B_id: PROGRESSING,
      deploy_C_id: COMPLETED,
    },
    route_changes: RouteChanges {
      rollout_specs:    [Creator, ...],  # new routes to create
      drain_route_ids:  [UUID, ...],     # old routes to terminate
    },
    errors: [EvaluationErrorData, ...],
  }
```

#### Key Design Principles

1. **Evaluator + Applier are called per handler**: Each DEPLOYING handler calls `evaluator.evaluate()` then `applier.apply()` in its `execute()`. The applier persists sub_step assignments and route mutations atomically via `StrategyTransaction`.
2. **Strategy FSMs implement a common interface via registry**: All strategy implementations extend `AbstractDeploymentStrategy` and implement `evaluate_cycle()`. Concrete classes (`RollingUpdateStrategy`, `BlueGreenStrategy`) live in dedicated module files. The `DeploymentStrategyRegistry` is injected into the evaluator.
3. **COMPLETED and ROLLED_BACK terminal states are handled by ProgressingHandler**: The applier performs revision swap for COMPLETED deployments and clears deploying_revision for ROLLED_BACK deployments. The ProgressingHandler returns COMPLETED as successes and ROLLED_BACK as errors, both flowing through the coordinator's standard transition path to READY.
4. **ROLLING_BACK is an active handler**: When provisioning or progressing fails (expired/give_up), the coordinator transitions the deployment to ROLLING_BACK. The `DeployingRollingBackHandler` then actively manages the rollback process — terminating new-revision routes and restoring previous revision traffic — across one or more coordinator cycles. On completion, it transitions to DEPLOYING/ROLLED_BACK, which the ProgressingHandler picks up for the final lifecycle transition to READY.

### DEPLOYING Handlers

Three handlers cover all DEPLOYING sub-steps:

#### DeployingProvisioningHandler

Targets `(DEPLOYING, PROVISIONING)`. Routes for the new revision are being created and waiting to become healthy.

- **success**: Routes provisioned → transition to PROGRESSING.
- **skipped**: Still provisioning → no transition, re-schedule.
- **expired/give_up**: Provisioning failed → transition to ROLLING_BACK.

```python
class DeployingProvisioningHandler(DeploymentHandler):
    # targets: [(DEPLOYING, PROVISIONING)]
    # success → DEPLOYING/PROGRESSING
    # expired/give_up → DEPLOYING/ROLLING_BACK

    async def execute(self, deployments):
        summary = await self._evaluator.evaluate(deployment_infos)
        await self._applier.apply(summary)
        # Classify by assigned sub_step:
        #   PROGRESSING → successes (coordinator transitions)
        #   still PROVISIONING → skipped (no state transition)
        #   evaluation errors → errors
        return DeploymentExecutionResult(successes=..., errors=..., skipped=...)
```

#### DeployingProgressingHandler

Targets `(DEPLOYING, PROGRESSING)`, `(DEPLOYING, COMPLETED)`, and `(DEPLOYING, ROLLED_BACK)`. This handler processes active progression and both terminal states:

- **COMPLETED**: Revision swap done → returned as success → coordinator transitions to READY.
- **ROLLED_BACK**: Deploying revision cleared → returned as error → coordinator transitions to READY.
- **PROGRESSING**: Still replacing routes → skipped (no state transition), re-evaluate next cycle.
- **expired/give_up**: Strategy failed → transition to ROLLING_BACK for active rollback.

```python
class DeployingProgressingHandler(DeploymentHandler):
    # targets: [(DEPLOYING, PROGRESSING), (DEPLOYING, COMPLETED), (DEPLOYING, ROLLED_BACK)]
    # success → READY
    # expired/give_up → DEPLOYING/ROLLING_BACK

    async def execute(self, deployments):
        summary = await self._evaluator.evaluate(deployment_infos)
        apply_result = await self._applier.apply(summary)
        # Classify:
        #   COMPLETED → successes (coordinator transitions to READY)
        #   ROLLED_BACK → errors (coordinator transitions to READY)
        #   still PROGRESSING → skipped (no state transition)
        #   evaluation errors → errors
        # Also filters out DESTROYING/DESTROYED deployments to prevent resurrection.
        return DeploymentExecutionResult(successes=..., errors=..., skipped=...)
```

#### DeployingRollingBackHandler

Targets `(DEPLOYING, ROLLING_BACK)`. Actively rolling back — terminates new-revision routes and restores traffic to previous revision routes.

- **success**: Rollback complete → transition to DEPLOYING/ROLLED_BACK (ProgressingHandler picks up and transitions to READY).
- **expired/give_up**: Rollback itself failed → transition to DEPLOYING/ROLLED_BACK (best-effort).

```python
class DeployingRollingBackHandler(DeploymentHandler):
    # targets: [(DEPLOYING, ROLLING_BACK)]
    # success → DEPLOYING/ROLLED_BACK
    # expired/give_up → DEPLOYING/ROLLED_BACK

    async def execute(self, deployments):
        summary = await self._evaluator.evaluate(deployment_infos)
        await self._applier.apply(summary)
        # All evaluated deployments → successes (coordinator transitions to ROLLED_BACK)
        # evaluation errors → errors
        return DeploymentExecutionResult(successes=..., errors=...)
```

**Design rationale**: ROLLING_BACK is an **active process** (terminating routes, restoring traffic) that may span multiple coordinator cycles, just like PROVISIONING and PROGRESSING. Making it a separate handler gives it its own retry/timeout classification via `_AttemptContext` and its own periodic task scheduling entry, ensuring rollback progress is independently tracked and rescheduled. Once complete, it transitions to ROLLED_BACK — a terminal marker that ProgressingHandler picks up for the final lifecycle transition to READY.

### Failure Classification and Retry Logic

The coordinator classifies handler errors using scheduling history to determine the appropriate response:

```
_handle_status_transitions(handler, result, records, attempt_ctx_map)
    │
    │  Success transitions:
    │    result.successes → transitions.success status
    │
    │  Failure classification (priority order):
    │    1. give_up:    attempts >= SERVICE_MAX_RETRIES
    │    2. expired:    elapsed > DEPLOYMENT_STATUS_TIMEOUT_MAP threshold
    │    3. need_retry: default (can be retried next cycle)
    │
    │  Each category uses its own transition from status_transitions():
    │    give_up  → transitions.give_up
    │    expired  → transitions.expired
    │    need_retry → transitions.need_retry
```

`_AttemptContext` tracks per-deployment retry state from scheduling history:
- `attempts`: Number of consecutive attempts in the same handler phase
- `started_at`: Timestamp when the current phase began
- `should_give_up(max_retries)`: Returns true if max retries exceeded
- `is_expired(lifecycle, current_dbtime)`: Returns true if timeout exceeded (e.g., DEPLOYING: 30 min)

### Coordinator Flow

The coordinator uses a **single dispatch path** for all handlers:

```
process_deployment_lifecycle(lifecycle_type, sub_step=None)
    │
    │  handler = registry.handlers[(lifecycle_type, sub_step)]
    │  acquire lock if handler.lock_id
    │
    │  _run_handler(handler):
    │    │
    │    │  1. Query deployments by handler.target_statuses()
    │    │     (lifecycles + sub_steps extracted from DeploymentLifecycleStatus list)
    │    │  2. Build attempt_ctx_map from scheduling history
    │    │  3. Enter DeploymentRecorderContext.scope()
    │    │  ┌───────────────────────────────────────────────────────┐
    │    │  │  result = handler.execute(deployments)                │
    │    │  │  all_records = pool.build_all_records()               │
    │    │  │  _handle_status_transitions(                          │
    │    │  │      handler, result, records, attempt_ctx_map)       │
    │    │  └───────────────────────────────────────────────────────┘
    │    │  4. handler.post_process(result)
    │    │
    │    ▼
```

Key design points:
- The coordinator has **no DEPLOYING-specific logic**. All handlers (simple and sub-step) use the same `_run_handler()` and `_handle_status_transitions()` path.
- DB filtering uses `target_statuses()` from the handler: lifecycles are extracted via `.lifecycle`, sub-steps via `.sub_status`.
- `_handle_status_transitions()` applies `sub_status` from `status_transitions()` to `EndpointLifecycleBatchUpdaterSpec`, ensuring the `sub_step` column is updated alongside the lifecycle transition.

### Sub-Step Recording

Each cycle evaluation produces sub-step variants recorded via the existing `DeploymentRecorderContext`. The coordinator's `_handle_status_transitions()` calls `extract_sub_steps_for_entity()` for each handler's result, including the deployment's sub-step information in the history.

#### Sub-Step Recording: Route Mutation Granularity

Sub-steps are recorded at the **route mutation level** by the evaluator's `_record_route_changes()`. Each route mutation type (rollout, drain) is recorded as a separate sub-step entry with the count of affected routes.

**PROVISIONING cycle** — new routes created:

```
sub_steps:
  rollout       → SUCCESS (message: "3 new route(s)")
  provisioning  → SUCCESS
```

**PROGRESSING cycle** — creating new routes / terminating old routes:

```
sub_steps:
  rollout       → SUCCESS (message: "1 new route(s)")
  drain         → SUCCESS (message: "1 route(s)")
  progressing   → SUCCESS
```

**COMPLETED cycle (Rolling Update)** — final drain:

```
sub_steps:
  drain         → SUCCESS (message: "1 route(s)")
```

This enables:

- **Observability**: Each deployment's progress is tracked per-entity with route mutation granularity
- **Debugging**: The sub-step history shows exactly which route mutations occurred at each cycle
- **Consistency**: All handlers use the same coordinator generic path

### Per-Strategy Configuration

| Strategy | Setting | Description |
|----------|---------|-------------|
| **Blue-Green** | `auto_promote: bool` | Automatically switch traffic when all Green are healthy |
| | `promote_delay_seconds: int` | Wait time before promotion |
| **Rolling Update** | `max_surge: int` | Maximum additional routes to create simultaneously |
| | `max_unavailable: int` | Maximum unavailable routes to allow |

On strategy failure (all new routes fail), automatic rollback always occurs.

## References

- [BEP-1006: Service Deployment Strategy](BEP-1006-service-deployment-strategy.md) — High-level design for Blue-Green and Rolling Update
- [BEP-1030: Sokovan Scheduler Status Transition Design](BEP-1030-sokovan-scheduler-status-transition.md) — State transition patterns of the Sokovan scheduler
