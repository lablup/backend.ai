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

### Composite Handler Pattern (DeployingHandler)

A single `evaluate()` call may produce different sub-steps for different deployments — some completed, others still PROGRESSING. To handle this, DEPLOYING is represented as a **composite handler** (`DeployingHandler`) that internally owns the strategy evaluator and sub-step handlers. The coordinator treats DEPLOYING identically to every other lifecycle type through the unified `prepare → execute → finalize → post_process` flow.

| Aspect | How it works |
|--------|-------------|
| **State transition** | Each sub-step handler returns explicit `status_transitions()` → coordinator's generic path handles all transitions |
| **Routing** | No special branching — `DeployingHandler.prepare()` runs the evaluator and returns sub-step handler tasks |
| **Cycles** | `prepare()`: evaluator runs strategy FSM + applies route changes → coordinator executes sub-step handlers → `finalize()`: records evaluation outcomes + transitions completed deployments |


## Sub-documents

| Document | Description |
|----------|-------------|
| [Rolling Update](BEP-1049/rolling-update.md) | Gradual route replacement strategy — max_surge/max_unavailable control |
| [Blue-Green](BEP-1049/blue-green.md) | Atomic traffic switch strategy — INACTIVE staging + promotion |

## Proposed Design

### Overall Architecture

Core idea: All lifecycle types — including DEPLOYING — follow a **single coordinator code path**: `prepare → execute → finalize → post_process`. The base `DeploymentHandler` provides default `prepare()` (returns self as single task) and `finalize()` (no-op). The composite `DeployingHandler` overrides these to run strategy evaluation, apply route changes, dispatch to sub-step handlers, and transition completed deployments.

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
│  process_deployment_lifecycle(type)  ← single unified code path              │
│    handler = handlers[type]                                                  │
│    ├─ handler.prepare(deployments) → handler_tasks                           │
│    ├─ _execute_and_transition_handlers(handler_tasks)                        │
│    ├─ handler.finalize(records)                                              │
│    └─ _post_process_handlers(results)                                        │
│                                                                              │
│  Handler map: Mapping[DeploymentLifecycleType, DeploymentHandler]            │
│    ├─ CHECK_PENDING → CheckPendingHandler                                    │
│    ├─ CHECK_REPLICA → CheckReplicaHandler                                    │
│    ├─ SCALING       → ScalingHandler                                         │
│    ├─ RECONCILE     → ReconcileHandler                                       │
│    ├─ DEPLOYING     → DeployingHandler (composite)                           │
│    └─ DESTROYING    → DestroyingHandler                                      │
│                                                                              │
│  Result handling (same generic path for all handlers):                       │
│    successes → next_status (transition + history)                            │
│    errors → failure_status (transition + history)                            │
│    skipped → keep (no transition)                                            │
└────────────────┬─────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  DeploymentHandler (base)                                                    │
│  ├─ prepare(deployments) → [(self, deployments)]   ← default: single task   │
│  ├─ execute(deployments) → result                  ← abstract               │
│  ├─ finalize(records)    → no-op                   ← default                │
│  └─ post_process(result) → ...                     ← abstract               │
│                                                                              │
│  Simple handlers (CheckPending, Scaling, etc.):                              │
│    Use defaults — prepare returns self, finalize is no-op                    │
│                                                                              │
│  DeployingHandler (composite):                                               │
│  ├─ prepare(): evaluator.evaluate() + apply route changes                    │
│  │             → [(sub_handler, subset), ...] for each sub-step              │
│  ├─ finalize(): record evaluation outcomes + transition completed            │
│  └─ owns:                                                                    │
│      ├─ DeploymentStrategyEvaluator                                          │
│      └─ sub_step_handlers:                                                   │
│          ├─ PROVISIONING → DeployingProvisioningHandler                      │
│          ├─ PROGRESSING  → DeployingProgressingHandler                       │
│          └─ ROLLED_BACK  → DeployingRolledBackHandler                        │
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

Both Blue-Green and Rolling Update cycle FSMs share a common set of **sub-step variants**. Each cycle evaluation directly returns one of these variants — no strategy-specific statuses or mapping layer exists:

| Sub-Step | Description | Handler | Transition |
|----------|-------------|---------|------------|
| **provisioning** | New routes being created or still in PROVISIONING state | DeployingProvisioningHandler | DEPLOYING → DEPLOYING |
| **progressing** | Strategy making active progress — health checks pending, promotion waiting, or routes being replaced | DeployingProgressingHandler | DEPLOYING → DEPLOYING |
| **rolled_back** | Strategy failed — rolled back to previous revision | DeployingRolledBackHandler | DEPLOYING → READY |

Completion is not a sub-step but a signal on `CycleEvaluationResult.completed`. When the strategy FSM detects that all new routes are healthy and no old routes remain, it returns `CycleEvaluationResult(sub_step=PROGRESSING, completed=True)`. The evaluator collects these into `EvaluationResult.completed`, and the coordinator directly calls `_transition_completed_deployments()` which atomically performs the revision swap and DEPLOYING→READY transition.

### DeploymentStrategyEvaluator

`DeploymentStrategyEvaluator` evaluates DEPLOYING-state deployments and groups them by sub-step. It is owned by `DeployingHandler`, which invokes it during `prepare()`. The coordinator does not interact with the evaluator directly.

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
    │  │    if cycle_result.completed:                            │
    │  │      completed.append(deployment)                       │
    │  │    else:                                                │
    │  │      groups[cycle_result.sub_step].append(deployment)   │
    │  └─────────────────────────────────────────────────────────┘
    │
    ▼
  EvaluationResult {
    groups: {
      PROVISIONING: [deploy_A],
      PROGRESSING:  [deploy_B, deploy_C],
    },
    completed: [deploy_D],  # strategy completed (revision swap pending)
    skipped: [deploy_E],    # no policy / unsupported strategy
    errors:  [error_F],     # exception during evaluation
    route_changes: RouteChanges {
      rollout_specs:    [Creator, ...],  # new routes to create
      drain_route_ids:  [UUID, ...],     # old routes to terminate
      promote_route_ids: [UUID, ...],    # green routes to activate (Blue-Green)
    },
  }
```

#### Key Design Principles

1. **Route changes are aggregated by the evaluator, applied by `DeployingHandler`**: The evaluator collects route mutations (rollout/drain/promote) from each strategy FSM into `EvaluationResult.route_changes`. `DeployingHandler._apply_route_changes()` applies them during `prepare()`. Individual sub-step handlers do not touch routes.
2. **Strategy FSMs implement a common interface via registry**: All strategy implementations extend the `BaseDeploymentStrategy` abstract base class and implement `evaluate_cycle()`. Concrete classes (`RollingUpdateStrategy`, `BlueGreenStrategy`) live in dedicated module files (`strategy/rolling_update.py`, `strategy/blue_green.py`). `DeployingHandler` creates and owns the `DeploymentStrategyRegistry`, which is injected into the evaluator to instantiate the appropriate strategy per deployment.
3. **Only grouping is returned**: The evaluator classifies deployments by sub-step; actual processing (revision swap, deploying_revision cleanup, etc.) is delegated to `DeployingHandler.finalize()` and sub-step handlers.

### Per-Sub-Step Handlers

Each sub-step handler is owned by `DeployingHandler` and registered in its `sub_step_handlers` map keyed by `DeploymentSubStep`. They are not directly visible to the coordinator.

#### State Transition Type: `DeploymentLifecycleStatus`

Handlers' `next_status()` and `failure_status()` return `DeploymentLifecycleStatus`. This type bundles `EndpointLifecycle` with an optional `DeploymentSubStatus`, conveying which sub-step triggered the transition to the coordinator's generic path:

```python
@dataclass(frozen=True)
class DeploymentLifecycleStatus:
    lifecycle: EndpointLifecycle
    sub_status: DeploymentSubStatus | None = None
```

The coordinator's `_handle_status_transitions()` extracts `.lifecycle` for DB updates and history recording.

#### DeployingInProgressHandler (base) → Provisioning / Progressing

PROVISIONING and PROGRESSING share the same logic (coordinator already applied route changes; handler returns success + reschedules), so `DeployingInProgressHandler` base class defines common behavior, and subclasses hard-code their sub-step-specific `next_status()` and `status_transitions()`:

```python
class DeployingInProgressHandler(DeploymentHandler):
    """PROVISIONING / PROGRESSING common base."""

    @classmethod
    def target_statuses(cls) -> list[EndpointLifecycle]:
        return [EndpointLifecycle.DEPLOYING]

    @classmethod
    def failure_status(cls) -> DeploymentLifecycleStatus | None:
        return None

    async def execute(self, deployments):
        # Route changes already applied by coordinator
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
    def next_status(cls) -> DeploymentLifecycleStatus | None:
        return DeploymentLifecycleStatus(
            lifecycle=EndpointLifecycle.DEPLOYING,
            sub_status=DeploymentSubStep.PROVISIONING,
        )


class DeployingProgressingHandler(DeployingInProgressHandler):
    @classmethod
    def next_status(cls) -> DeploymentLifecycleStatus | None:
        return DeploymentLifecycleStatus(
            lifecycle=EndpointLifecycle.DEPLOYING,
            sub_status=DeploymentSubStep.PROGRESSING,
        )
```

`next_status().lifecycle == DEPLOYING` so the coordinator records DEPLOYING→DEPLOYING SUCCESS history for in-progress deployments. The deployment stays in DEPLOYING state and is re-evaluated next cycle.

For completed deployments, the coordinator directly calls `_transition_completed_deployments()` after all handler post-processing. This method atomically performs the revision swap (`complete_deployment_revision_swap`) and transitions the deployment to READY with history recording.

#### DeployingRolledBackHandler (ROLLED_BACK)

```python
class DeployingRolledBackHandler(DeploymentHandler):
    @classmethod
    def name(cls) -> str:
        return "deploying-rolled-back"

    @classmethod
    def next_status(cls) -> DeploymentLifecycleStatus | None:
        return DeploymentLifecycleStatus(
            lifecycle=EndpointLifecycle.READY,
            sub_status=DeploymentSubStep.ROLLED_BACK,
        )

    async def execute(self, deployments):
        # deploying_revision = NULL (current_revision preserved)
        clear_ids = [d.id for d in deployments if d.deploying_revision_id is not None]
        if clear_ids:
            await self._deployment_executor._deployment_repo.clear_deploying_revision(clear_ids)
        return DeploymentExecutionResult(successes=list(deployments))
```

On rollback, only `deploying_revision` is cleared; `current_revision` is preserved. The coordinator transitions to READY.

### Unified Coordinator Flow

The coordinator uses a single code path for all lifecycle types, including DEPLOYING:

```
process_deployment_lifecycle(lifecycle_type)
    │
    │  1. Look up handler by lifecycle_type (simple enum key)
    │  2. Acquire distributed lock if handler.lock_id is set
    │  3. Query deployments by handler.target_statuses()
    │
    │  4. Enter DeploymentRecorderContext.scope()
    │  ┌───────────────────────────────────────────────────────────────┐
    │  │                                                               │
    │  │  handler_tasks = handler.prepare(deployments)                 │
    │  │    ↑ simple handlers: [(self, deployments)]                   │
    │  │    ↑ DeployingHandler: evaluator.evaluate()                   │
    │  │      + _apply_route_changes()                                 │
    │  │      → [(sub_handler_A, subset_A), (sub_handler_B, subset_B)] │
    │  │                                                               │
    │  │  for (h, deps) in handler_tasks:                              │
    │  │    result = h.execute(deps)                                   │
    │  │                                                               │
    │  │  all_records = pool.build_all_records()                       │
    │  │                                                               │
    │  │  for (h, result) in handler_results:                          │
    │  │    _handle_status_transitions(h, result, all_records)         │
    │  │    ↑ same generic transition logic for ALL handlers            │
    │  │                                                               │
    │  └───────────────────────────────────────────────────────────────┘
    │
    │  5. handler.finalize(all_records)
    │    ↑ simple handlers: no-op
    │    ↑ DeployingHandler: record evaluation outcomes
    │      + transition completed deployments (atomic revision swap
    │        + DEPLOYING → READY + history recording)
    │
    │  6. Post-process outside RecorderContext scope
    │  for (h, result) in handler_results:
    │    h.post_process(result)
    │
    ▼
```

Key: The coordinator has **no DEPLOYING-specific logic**. `_handle_status_transitions()` uses the same generic method for all handlers. DEPLOYING-specific concerns (evaluator invocation, route mutations, completion transitions) are fully encapsulated in `DeployingHandler.prepare()` and `DeployingHandler.finalize()`.

### Sub-Step Recording

Each cycle evaluation produces sub-step variants recorded via the existing `DeploymentRecorderContext`. Both the evaluator and handlers execute within the same RecorderContext scope, so all sub-steps are collected into a single execution record.

The coordinator's `_handle_status_transitions()` calls `extract_sub_steps_for_entity()` for each handler's result, including the deployment's sub-step information in the history.

#### Sub-Step Recording: Route Mutation Granularity

Sub-steps are recorded at the **route mutation level** by the evaluator's `_record_route_changes()`. Each route mutation type (rollout, drain, promote) is recorded as a separate sub-step entry with the count of affected routes.

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

**COMPLETED cycle (Blue-Green)** — promotion executed:

```
sub_steps:
  drain         → SUCCESS (message: "3 route(s)")
  promote       → SUCCESS (message: "3 route(s)")
```

**COMPLETED cycle (Rolling Update)** — final drain:

```
sub_steps:
  drain         → SUCCESS (message: "1 route(s)")
```

Route mutation sub-steps are recorded within the `DeploymentRecorderContext` scope. For in-progress deployments, handlers add their own sub-step (e.g., `provisioning`, `progressing`) to the same record. For completed deployments, `_transition_completed_deployments()` receives the recorder pool's `all_records` and includes the current cycle's route mutation sub-steps in the completion history.

The revision swap (`complete_deployment_revision_swap`) is an atomic DB operation that does not appear as a sub-step.

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

## Decision Log

### 2026-03-04: Unified coordinator code path via composite handler pattern

**Context**: PR #9566 review identified that the coordinator treated DEPLOYING as a special case with a separate method (`process_deploying_lifecycle`) and separate code path. This created two parallel flows, a union type for handler keys (`DeploymentLifecycleType | (DeploymentLifecycleType, DeploymentSubStep)`), and DEPLOYING-specific branching in the event handler.

**Decision**: Refactor to a single unified code path using the composite handler pattern.

Three design principles drove the change:

1. **DEPLOYING generalization**: DEPLOYING is no longer a special lifecycle type. The coordinator processes it through the same `process_deployment_lifecycle()` as all other types. No `if DEPLOYING` branches exist in the coordinator or event handler.

2. **Sub-step unification via `prepare()`/`finalize()`**: The base `DeploymentHandler` gains two concrete methods with defaults — `prepare()` returns `[(self, deployments)]` (treat self as single task) and `finalize()` is a no-op. Simple handlers use these defaults unchanged. The composite `DeployingHandler` overrides `prepare()` to run the evaluator and return sub-step handler tasks, and `finalize()` to record evaluation outcomes and transition completed deployments.

3. **Evaluator interface integration**: The evaluator is no longer called directly by the coordinator. Instead, `DeployingHandler` owns the evaluator and invokes it within `prepare()`. The coordinator has no knowledge of strategy evaluation, route mutations, or completion transitions — these are fully encapsulated in the handler.

**Changes**:
- `DeploymentHandler` base: added `prepare()`, `finalize()` with defaults
- New `DeployingHandler` composite class: owns evaluator, sub-step handlers, route mutation logic, completion transition logic
- `DeploymentCoordinator`: removed `process_deploying_lifecycle()`, `DeploymentHandlerKey` type, `_strategy_registry`/`_deploying_evaluator` fields, and four private methods moved to `DeployingHandler`
- Handler map key simplified: `Mapping[DeploymentLifecycleType, DeploymentHandler]`
- Event handler: removed DEPLOYING branch

## References

- [BEP-1006: Service Deployment Strategy](BEP-1006-service-deployment-strategy.md) — High-level design for Blue-Green and Rolling Update
- [BEP-1030: Sokovan Scheduler Status Transition Design](BEP-1030-sokovan-scheduler-status-transition.md) — State transition patterns of the Sokovan scheduler
