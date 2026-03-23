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

Core idea: The coordinator maintains a `HandlerRegistry` with a flat `(lifecycle_type, sub_step)` key. Simple lifecycle types (CHECK_PENDING, SCALING, etc.) register with `sub_step=None`. DEPLOYING registers two handlers — one for PROVISIONING and one for ROLLING_BACK. Each handler independently calls the strategy evaluator and applier.

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
│      (DEPLOYING, ROLLING_BACK)       → DeployingRollingBackHandler           │
│      (DESTROYING, None)              → DestroyingHandler                     │
│    }                                                                         │
│                                                                              │
│  _run_handler(handler):                                                      │
│    1. Query deployments by handler.target_statuses()                         │
│    2. Build DeploymentWithHistory from scheduling history                    │
│    3. Execute handler + handle status transitions                            │
│    4. Classify failures (give_up / expired / need_retry)                     │
│    5. Check skipped deployments for timeout → expired transition             │
│    6. Post-process (reschedule, trigger dependent lifecycles)                │
│                                                                              │
│  Result handling (same generic path for all handlers):                       │
│    successes  → success status (transition + history + sub_step update)      │
│    errors     → classified into give_up / expired / need_retry               │
│    skipped    → timeout check; if expired transition defined and timed out,  │
│                 transition to expired status                                 │
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
│  DEPLOYING handlers (2 total):                                               │
│  ├─ DeployingProvisioningHandler                                             │
│  │    targets: [(DEPLOYING, PROVISIONING)]                                   │
│  │    execute: evaluator.evaluate() + applier.apply()                        │
│  │    success → READY (all routes replaced)                                  │
│  │    need_retry → DEPLOYING/PROVISIONING (route mutations executed)         │
│  │    expired → DEPLOYING/ROLLING_BACK (timeout)                             │
│  │                                                                           │
│  └─ DeployingRollingBackHandler                                              │
│       targets: [(DEPLOYING, ROLLING_BACK)]                                   │
│       execute: clear deploying_revision                                      │
│       success → READY                                                        │
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
| **PROVISIONING** | New routes being created, strategy progressing, or waiting for routes to become healthy | DeployingProvisioningHandler | success → READY, need_retry → DEPLOYING/PROVISIONING, expired → DEPLOYING/ROLLING_BACK |
| **ROLLING_BACK** | Actively rolling back — clearing deploying_revision and restoring previous revision | DeployingRollingBackHandler | success → READY |

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
      deploy_B_id: PROVISIONING,
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
3. **Completion is detected by the evaluator**: When the strategy FSM determines all routes are replaced, it returns COMPLETED. The applier performs the revision swap (`deploying_revision` → `current_revision`). The provisioning handler returns these as successes, which the coordinator transitions to READY.
4. **ROLLING_BACK is a cleanup handler**: When the provisioning handler's skipped deployments exceed timeout (expired), the coordinator transitions them to DEPLOYING/ROLLING_BACK. The `DeployingRollingBackHandler` clears `deploying_revision` and transitions directly to READY. No multi-cycle rollback — it is a single-step cleanup.

### DEPLOYING Handlers

Two handlers cover all DEPLOYING sub-steps:

#### DeployingProvisioningHandler

Targets `(DEPLOYING, PROVISIONING)`. The main DEPLOYING handler — runs the strategy FSM each cycle to create/drain routes and check for completion.

- **success**: All routes replaced (COMPLETED) → transition to READY.
- **need_retry**: Route mutations executed (create/drain) → stays in PROVISIONING with history record.
- **skipped**: No changes, still waiting for routes → no transition. **Coordinator checks timeout**: if `phase_started_at` exceeds the DEPLOYING timeout threshold, transitions to ROLLING_BACK via the `expired` path.
- **errors**: Evaluation errors → classified into give_up/expired/need_retry.

```python
class DeployingProvisioningHandler(DeploymentHandler):
    # targets: [(DEPLOYING, PROVISIONING)]
    # success → READY
    # need_retry → DEPLOYING/PROVISIONING
    # expired → DEPLOYING/ROLLING_BACK

    async def execute(self, deployments):
        summary = await self._evaluator.evaluate(deployment_infos)
        apply_result = await self._applier.apply(summary)
        # Classify by apply_result:
        #   completed_ids → successes (coordinator transitions to READY)
        #   route mutations → need_retry (stays in PROVISIONING)
        #   no changes → skipped (coordinator checks timeout)
        #   evaluation errors → errors
        return DeploymentExecutionResult(successes=..., errors=..., skipped=..., need_retry=...)
```

#### DeployingRollingBackHandler

Targets `(DEPLOYING, ROLLING_BACK)`. Clears `deploying_revision` and transitions directly to READY.

- **success**: Deploying revision cleared → transition to READY.

```python
class DeployingRollingBackHandler(DeploymentHandler):
    # targets: [(DEPLOYING, ROLLING_BACK)]
    # success → READY

    async def execute(self, deployments):
        await self._applier.clear_deploying_revision(deployment_ids)
        return DeploymentExecutionResult(successes=list(deployments))
```

### Failure Classification and Timeout Handling

The coordinator classifies handler errors and checks skipped deployments for timeout:

```
_handle_status_transitions(handler, result, records)
    │
    │  Success transitions:
    │    result.successes → transitions.success status
    │
    │  Need-retry transitions (explicit from handler):
    │    result.need_retry → transitions.need_retry status
    │    (never escalated to give_up — represents normal progress)
    │
    │  Skipped timeout check:
    │    If transitions.expired is defined and result.skipped is non-empty:
    │      For each skipped deployment, check phase_started_at against
    │      DEPLOYMENT_STATUS_TIMEOUT_MAP threshold.
    │      Timed-out deployments → transitions.expired status.
    │
    │  Failure classification (priority order):
    │    1. give_up:    phase_attempts >= SERVICE_MAX_RETRIES
    │    2. expired:    phase_started_at elapsed > timeout threshold
    │    3. need_retry: default (can be retried next cycle)
    │
    │  Each category uses its own transition from status_transitions():
    │    give_up  → transitions.give_up
    │    expired  → transitions.expired
    │    need_retry → transitions.need_retry
```

`DeploymentWithHistory` tracks per-deployment state from scheduling history:
- `phase_attempts`: Number of consecutive attempts in the same handler phase
- `phase_started_at`: Timestamp when the current phase's history record was first created (not reset on retries — history records with same phase/error_code/to_status are merged, incrementing `attempts` without changing `created_at`)

The skipped timeout check is critical for DEPLOYING: when deployments are simply waiting for routes to become healthy (no evaluation errors, no route mutations), they appear as `skipped`. Without this check, they would never hit the `expired` path since `_classify_failures` only processes `result.errors`.

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
    │    │  2. Build DeploymentWithHistory from scheduling history
    │    │  3. Enter DeploymentRecorderContext.scope()
    │    │  ┌───────────────────────────────────────────────────────┐
    │    │  │  result = handler.execute(deployments)                │
    │    │  │  all_records = pool.build_all_records()               │
    │    │  │  _handle_status_transitions(                          │
    │    │  │      handler, result, records)                        │
    │    │  └───────────────────────────────────────────────────────┘
    │    │  4. handler.post_process(result)
    │    │
    │    ▼
```

Key design points:
- The coordinator has **no DEPLOYING-specific logic**. All handlers (simple and sub-step) use the same `_run_handler()` and `_handle_status_transitions()` path.
- DB filtering uses `target_statuses()` from the handler: lifecycles are extracted via `.lifecycle`, sub-steps via `.sub_status`.
- `_handle_status_transitions()` applies `sub_status` from `status_transitions()` to `EndpointLifecycleBatchUpdaterSpec`, ensuring the `sub_step` column is updated alongside the lifecycle transition.
- Skipped timeout check is a generic mechanism: any handler that declares `transitions.expired` gets automatic timeout checking on skipped deployments.

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

**PROVISIONING cycle** — creating new routes / terminating old routes:

```
sub_steps:
  rollout       → SUCCESS (message: "1 new route(s)")
  drain         → SUCCESS (message: "1 route(s)")
  provisioning  → SUCCESS
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
