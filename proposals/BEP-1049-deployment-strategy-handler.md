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

### Flat Registry with Pre-Step Pattern

A single `evaluate()` call may produce different sub-steps for different deployments — some completed, others still PROGRESSING. To handle this, DEPLOYING sub-step handlers are registered **flat** in the coordinator's `HandlerRegistry` alongside other lifecycle handlers. A **pre-step** (`DeployingEvaluatePreStep`) runs once before handler dispatch to evaluate the strategy FSM, update the `sub_step` column, and apply route mutations. The coordinator then dispatches to individual sub-step handlers based on the registry key.

| Aspect | How it works |
|--------|-------------|
| **State transition** | Each sub-step handler returns explicit `status_transitions()` → coordinator's generic path handles all transitions |
| **Dispatch** | Coordinator iterates sub-steps derived from registry keys, runs each handler independently |
| **Pre-step** | `DeployingEvaluatePreStep` evaluates strategy FSM + applies route changes before any handler runs |


## Sub-documents

| Document | Description |
|----------|-------------|
| [Rolling Update](BEP-1049/rolling-update.md) | Gradual route replacement strategy — max_surge/max_unavailable control |
| [Blue-Green](BEP-1049/blue-green.md) | Atomic traffic switch strategy — INACTIVE staging + promotion |

## Proposed Design

### Overall Architecture

Core idea: The coordinator maintains a `HandlerRegistry` with a flat `(lifecycle_type, sub_step)` key. Simple lifecycle types (CHECK_PENDING, SCALING, etc.) register with `sub_step=None`. DEPLOYING registers multiple handlers, one per sub-step. Before dispatching DEPLOYING handlers, the coordinator runs an optional **pre-step** that evaluates the strategy FSM and updates the `sub_step` column in DB.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          Periodic Task Scheduler                             │
│                                                                              │
│  DeploymentTaskSpec                                                          │
│  ┌────────────────────────────┐                                              │
│  │ check_pending: 2s / 30s    │                                              │
│  │ check_replica: 5s / 30s    │                                              │
│  │ scaling:       5s / 30s    │                                              │
│  │ deploying:     5s / 30s    │  ← drives deployment strategy cycles         │
│  │ reconcile:     -- / 30s    │                                              │
│  │ destroying:    5s / 60s    │                                              │
│  └─────────────┬──────────────┘                                              │
│                │                                                             │
│                ▼                                                             │
│  DoDeploymentLifecycleEvent                                                  │
│  DoDeploymentLifecycleIfNeededEvent                                          │
│  (lifecycle_type: str)                                                       │
└────────────────┬─────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         DeploymentCoordinator                                │
│                                                                              │
│  process_deployment_lifecycle(type)                                          │
│    sub_steps = registry.sub_steps_for(type)                                  │
│    ├─ No sub-steps (simple lifecycle):                                       │
│    │    handler = registry.handlers[(type, None)]                            │
│    │    acquire lock if handler.lock_id                                      │
│    │    _run_handler(handler, type, sub_step=None)                           │
│    └─ Has sub-steps (DEPLOYING):                                             │
│         _run_pre_step(type)  ← DeployingEvaluatePreStep                     │
│         for sub_step in sub_steps:                                           │
│           handler = registry.handlers[(type, sub_step)]                      │
│           _run_handler(handler, type, sub_step=sub_step)                     │
│                                                                              │
│  HandlerRegistry:                                                            │
│    handlers: dict[(DeploymentLifecycleType, DeploymentSubStep | None),       │
│                   DeploymentHandler]                                          │
│    pre_steps: dict[DeploymentLifecycleType, LifecyclePreStep]                │
│                                                                              │
│    handlers = {                                                              │
│      (CHECK_PENDING, None)           → CheckPendingHandler                   │
│      (CHECK_REPLICA, None)           → CheckReplicaHandler                   │
│      (SCALING, None)                 → ScalingHandler                        │
│      (RECONCILE, None)               → ReconcileHandler                      │
│      (DEPLOYING, PROVISIONING)       → DeployingProvisioningHandler          │
│      (DEPLOYING, PROGRESSING)        → DeployingProgressingHandler           │
│      (DEPLOYING, COMPLETED)          → DeployingCompletedHandler             │
│      (DEPLOYING, ROLLED_BACK)        → DeployingRolledBackHandler            │
│      (DESTROYING, None)              → DestroyingHandler                     │
│    }                                                                         │
│    pre_steps = {                                                             │
│      DEPLOYING → DeployingEvaluatePreStep                                    │
│    }                                                                         │
│                                                                              │
│  Result handling (same generic path for all handlers):                       │
│    successes → next_status (transition + history + sub_step update)          │
│    errors → failure_status (transition + history)                            │
│    skipped → keep (no transition)                                            │
└────────────────┬─────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  DeploymentHandler (base)                                                    │
│  ├─ name()               → str                        ← abstract            │
│  ├─ lock_id              → LockID | None               ← abstract           │
│  ├─ target_statuses()    → list[EndpointLifecycle]     ← abstract           │
│  ├─ status_transitions() → DeploymentStatusTransitions ← abstract           │
│  ├─ execute(deployments) → DeploymentExecutionResult   ← abstract           │
│  └─ post_process(result) → None                        ← abstract           │
│                                                                              │
│  DeployingEvaluatePreStep (not a handler):                                   │
│  └─ run(): evaluator.evaluate() + update sub_steps + apply route changes    │
│                                                                              │
│  DEPLOYING sub-step handlers:                                                │
│  ├─ DeployingProvisioningHandler  (DEPLOYING → DEPLOYING/PROVISIONING)      │
│  ├─ DeployingProgressingHandler   (DEPLOYING → DEPLOYING/PROGRESSING)       │
│  ├─ DeployingCompletedHandler     (DEPLOYING → READY/COMPLETED)             │
│  └─ DeployingRolledBackHandler    (DEPLOYING → READY/ROLLED_BACK)           │
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

Both Blue-Green and Rolling Update cycle FSMs share a common set of **sub-step variants**. The evaluator assigns each deployment a sub-step by writing to the `sub_step` column. The coordinator then dispatches to the matching handler based on the `(DEPLOYING, sub_step)` registry key.

| Sub-Step | Description | Handler | Transition |
|----------|-------------|---------|------------|
| **PROVISIONING** | New routes being created or still in PROVISIONING state | DeployingProvisioningHandler | DEPLOYING → DEPLOYING |
| **PROGRESSING** | Strategy making active progress — routes being replaced | DeployingProgressingHandler | DEPLOYING → DEPLOYING |
| **COMPLETED** | All strategy conditions met — revision swap pending | DeployingCompletedHandler | DEPLOYING → READY |
| **ROLLED_BACK** | Strategy failed — rolled back to previous revision | DeployingRolledBackHandler | DEPLOYING → READY |

### DeployingEvaluatePreStep

`DeployingEvaluatePreStep` runs **once** before the coordinator dispatches to individual sub-step handlers. It is **not** a handler — it implements the `LifecyclePreStep` protocol. The coordinator calls it via `_run_pre_step()`.

#### Responsibilities

1. **Evaluate strategy FSM** for all DEPLOYING deployments via `DeploymentStrategyEvaluator.evaluate()`
2. **Update the `sub_step` column** in DB based on evaluation results (including COMPLETED/ROLLED_BACK)
3. **Apply route mutations** (rollout new routes, drain old routes) aggregated from strategy FSMs

After the pre-step completes, each deployment's `sub_step` column reflects its current state. The coordinator then queries deployments filtered by each sub-step and dispatches to the corresponding handler.

### DeploymentStrategyEvaluator

`DeploymentStrategyEvaluator` evaluates DEPLOYING-state deployments and determines their sub-step assignments and route mutations. It is owned by `DeployingEvaluatePreStep`.

#### Execution Flow

```
DeploymentStrategyEvaluator.evaluate(deployments)
    │
    │  Phase 1: Load policies and routes
    │  ┌─────────────────────────────────────────────────────────┐
    │  │  policy_map = load_policies(deployments)                │
    │  │  route_map = fetch_routes_by_endpoint_ids(...)           │
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
  EvaluationResult {
    assignments: {
      deploy_A_id: PROVISIONING,
      deploy_B_id: PROGRESSING,
      deploy_C_id: COMPLETED,
      deploy_D_id: ROLLED_BACK,
    },
    route_changes: RouteChanges {
      rollout_specs:    [Creator, ...],  # new routes to create
      drain_route_ids:  [UUID, ...],     # old routes to terminate
    },
  }
```

#### Key Design Principles

1. **Route changes are aggregated by the evaluator, applied by the pre-step**: The evaluator collects route mutations (rollout/drain) from each strategy FSM into `EvaluationResult.route_changes`. `DeployingEvaluatePreStep._apply_route_changes()` applies them. Individual sub-step handlers do not touch routes.
2. **Strategy FSMs implement a common interface via registry**: All strategy implementations extend `AbstractDeploymentStrategy` and implement `evaluate_cycle()`. Concrete classes (`RollingUpdateStrategy`, `BlueGreenStrategy`) live in dedicated module files. The `DeploymentStrategyRegistry` is injected into the evaluator.
3. **Only assignments and route changes are returned**: The evaluator determines which sub-step each deployment should be in; actual processing (revision swap, deploying_revision cleanup, etc.) is delegated to the corresponding sub-step handlers.

### Per-Sub-Step Handlers

Sub-step handlers are registered directly in the coordinator's `HandlerRegistry`. Each queries only deployments matching its sub-step (passed from the registry key, not from the handler itself).

#### State Transition Type: `DeploymentLifecycleStatus`

`status_transitions()` returns `DeploymentStatusTransitions` containing `DeploymentLifecycleStatus` values. This type bundles `EndpointLifecycle` with an optional `DeploymentSubStatus`:

```python
@dataclass(frozen=True)
class DeploymentLifecycleStatus:
    lifecycle: EndpointLifecycle
    sub_status: DeploymentSubStatus | None = None
```

The coordinator's `_handle_status_transitions()` extracts `.lifecycle` for the DB lifecycle update and `.sub_status` for the `sub_step` column update and history recording. When `sub_status` is `None`, the `sub_step` column is cleared (e.g., transitioning from DEPLOYING to READY clears COMPLETED/ROLLED_BACK).

#### DeployingInProgressHandler (base) → Provisioning / Progressing

PROVISIONING and PROGRESSING share the same logic (pre-step already applied route changes; handler returns success + reschedules), so `DeployingInProgressHandler` base class defines common behavior, and subclasses hard-code their `status_transitions()`:

```python
class DeployingInProgressHandler(DeploymentHandler):
    """PROVISIONING / PROGRESSING common base."""

    @classmethod
    def target_statuses(cls) -> list[EndpointLifecycle]:
        return [EndpointLifecycle.DEPLOYING]

    @classmethod
    def status_transitions(cls) -> DeploymentStatusTransitions:
        # Stay in DEPLOYING — no transition.
        return DeploymentStatusTransitions(success=None, failure=None)

    async def execute(self, deployments):
        # Route changes already applied by pre-step
        return DeploymentExecutionResult(successes=list(deployments))

    async def post_process(self, result):
        # Re-schedule DEPLOYING for the next coordinator cycle
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.DEPLOYING
        )
        # Trigger route provisioning so new routes get sessions
        await self._route_controller.mark_lifecycle_needed(
            RouteLifecycleType.PROVISIONING
        )


class DeployingProvisioningHandler(DeployingInProgressHandler):
    @classmethod
    def status_transitions(cls) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.PROVISIONING,
            ),
            failure=None,
        )


class DeployingProgressingHandler(DeployingInProgressHandler):
    @classmethod
    def status_transitions(cls) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.PROGRESSING,
            ),
            failure=None,
        )
```

`status_transitions().success.lifecycle == DEPLOYING` so the coordinator keeps the deployment in DEPLOYING state with the sub_step column preserved. The deployment is re-evaluated next cycle.

#### DeployingCompletedHandler

Performs revision swap via `complete_deployment_revision_swap()`. The coordinator's standard `_handle_status_transitions()` transitions to READY with history recording.

#### DeployingRolledBackHandler

Clears `deploying_revision` only; `current_revision` is preserved. The coordinator transitions to READY.

```python
class DeployingRolledBackHandler(DeploymentHandler):
    async def execute(self, deployments):
        endpoint_ids = {d.id for d in deployments}
        await self._deployment_repo.clear_deploying_revision(endpoint_ids)
        return DeploymentExecutionResult(successes=list(deployments))
```

### Coordinator Flow

The coordinator uses a **two-path** dispatch based on whether sub-steps exist:

```
process_deployment_lifecycle(lifecycle_type)
    │
    │  sub_steps = registry.sub_steps_for(lifecycle_type)
    │
    ├─ No sub-steps (simple lifecycle):
    │    handler = registry.handlers[(lifecycle_type, None)]
    │    acquire lock if handler.lock_id
    │    _run_handler(handler, lifecycle_type, sub_step=None)
    │
    └─ Has sub-steps (e.g., DEPLOYING):
         _run_pre_step(lifecycle_type)
         for sub_step in sub_steps:
           handler = registry.handlers[(lifecycle_type, sub_step)]
           _run_handler(handler, lifecycle_type, sub_step=sub_step)

_run_handler(handler, lifecycle_type, sub_step):
    │
    │  1. Query deployments by handler.target_statuses() + sub_step
    │  2. Enter DeploymentRecorderContext.scope()
    │  ┌───────────────────────────────────────────────────────┐
    │  │  result = handler.execute(deployments)                │
    │  │  all_records = pool.build_all_records()               │
    │  │  _handle_status_transitions(handler, result, records) │
    │  └───────────────────────────────────────────────────────┘
    │  3. handler.post_process(result)
    │
    ▼
```

Key design points:
- The coordinator has **no DEPLOYING-specific logic** in `_run_handler()` or `_handle_status_transitions()`. All handlers use the same generic path.
- The sub-step for DB filtering comes from the **registry key**, not from the handler. Handlers do not declare their target sub-step.
- `_handle_status_transitions()` passes `sub_status` from `status_transitions()` to `EndpointLifecycleBatchUpdaterSpec`, ensuring the `sub_step` column is updated alongside the lifecycle transition.

### Sub-Step Recording

Each cycle evaluation produces sub-step variants recorded via the existing `DeploymentRecorderContext`. Both the pre-step and handlers execute within the same RecorderContext scope, so all sub-steps are collected into a single execution record.

The coordinator's `_handle_status_transitions()` calls `extract_sub_steps_for_entity()` for each handler's result, including the deployment's sub-step information in the history.

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
