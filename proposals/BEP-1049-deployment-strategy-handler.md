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

### Evaluator + Sub-Step Handler Pattern

A single `evaluate()` call may produce different sub-steps for different deployments — some completed, others still PROGRESSING. To handle this, a **strategy evaluator** groups deployments by sub-step, and **per-sub-step handlers** process each group. Completed deployments are returned separately in `EvaluationResult.completed` and processed via the PROGRESSING handler's `post_process`.

| Aspect | How it works |
|--------|-------------|
| **State transition** | Each sub-step handler returns explicit `next_status()` → coordinator's generic path handles all transitions |
| **Routing** | Coordinator branches to evaluator path for `DeploymentLifecycleType.DEPLOYING` |
| **Cycles** | Evaluator runs strategy FSM + applies route changes → handlers process results → coordinator records history |


## Sub-documents

| Document | Description |
|----------|-------------|
| [Rolling Update](BEP-1049/rolling-update.md) | Gradual route replacement strategy — max_surge/max_unavailable control |
| [Blue-Green](BEP-1049/blue-green.md) | Atomic traffic switch strategy — INACTIVE staging + promotion |

## Proposed Design

### Overall Architecture

Core idea: A **strategy evaluator** evaluates DEPLOYING-state deployments and groups them by sub-step, then **per-sub-step handlers** process each group. The coordinator's generic `_handle_status_transitions()` path handles all history recording and lifecycle transitions.

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
│    evaluator = evaluators.get(type)                                          │
│    ├─ evaluator exists → _process_with_evaluator() (evaluator path)          │
│    └─ no evaluator → existing single-handler path                            │
│                                                                              │
│  Handler map key: HandlerKey                                                 │
│    DeploymentLifecycleType                        ← single handlers          │
│    | (DeploymentLifecycleType, DeploymentSubStep) ← sub-step handlers        │
│                                                                              │
│  Result handling (same generic path for all handlers):                       │
│    successes → next_status (transition + history)                            │
│    errors → failure_status (transition + history)                            │
│    skipped → keep (no transition)                                            │
└────────────────┬─────────────────────────────────────────────────────────────┘
                 │
      ┌──────────┴──────────────────────────┐
      ▼                                     ▼
┌─────────────────────┐   ┌──────────────────────────────────────────────────┐
│  DeploymentHandler   │   │  DeploymentStrategyEvaluator                     │
│  (single-handler)    │   │  (evaluator path — DEPLOYING only)               │
│                      │   │                                                  │
│  Implementations:    │   │  evaluate(deployments) → EvaluationResult        │
│  ├─ CheckPending     │   │    1. Load policies/routes                       │
│  ├─ Scaling          │   │    2. Run strategy FSM → CycleEvaluationResult  │
│  ├─ CheckReplica     │   │    3. Apply route changes (scale_out/scale_in)   │
│  ├─ Reconcile        │   │    4. Group by sub-step                          │
│  └─ Destroying       │   └───────────────┬──────────────────────────────────┘
└─────────────────────┘                    │
                                           ▼
                            ┌──────────────────────────────────────┐
                            │  Per-Sub-Step Handlers (composite)   │
                            │                                      │
                            │  (DEPLOYING, PROVISIONING)           │
                            │  (DEPLOYING, PROGRESSING)            │
                            │    → DeployingInProgressHandler      │
                            │      next_status: DEPLOYING          │
                            │      post_process: revision swap     │
                            │        for completed deployments     │
                            │                                      │
                            │  (DEPLOYING, ROLLED_BACK)            │
                            │    → DeployingRolledBackHandler      │
                            │      next_status: READY              │
                            └──────────────────────────────────────┘
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
| **provisioning** | New routes being created or still in PROVISIONING state | DeployingInProgressHandler | DEPLOYING → DEPLOYING |
| **progressing** | Strategy making active progress — health checks pending, promotion waiting, or routes being replaced | DeployingInProgressHandler | DEPLOYING → DEPLOYING |
| **rolled_back** | Strategy failed — rolled back to previous revision | DeployingRolledBackHandler | DEPLOYING → READY |

Completion is not a sub-step but a signal on `CycleEvaluationResult.completed`. When the strategy FSM detects that all new routes are healthy and no old routes remain, it returns `CycleEvaluationResult(sub_step=PROGRESSING, completed=True)`. The evaluator collects these into `EvaluationResult.completed`, and the coordinator passes them to the PROGRESSING handler's `post_process` for revision swap, then transitions to READY.

### DeploymentStrategyEvaluator

`DeploymentStrategyEvaluator` evaluates DEPLOYING-state deployments and groups them by sub-step. It is a separate component (not a handler) that the coordinator invokes before handler execution.

#### Execution Flow

```
DeploymentStrategyEvaluator.evaluate(deployments)
    │
    │  Phase 1: Load policies and routes
    │  ┌─────────────────────────────────────────────────────────┐
    │  │  policy_map = load_policies(deployments)                │
    │  │  route_map = fetch_active_routes_by_endpoint_ids(...)   │
    │  └─────────────────────────────────────────────────────────┘
    │
    │  Phase 2: Run per-deployment strategy FSM
    │  ┌─────────────────────────────────────────────────────────┐
    │  │  for deployment in deployments:                         │
    │  │    policy = policy_map[deployment.id]                   │
    │  │    routes = route_map[deployment.id]                    │
    │  │                                                         │
    │  │    if policy.strategy == ROLLING:                       │
    │  │      cycle_result = rolling_update_evaluate(...)        │
    │  │    elif policy.strategy == BLUE_GREEN:                  │
    │  │      cycle_result = blue_green_evaluate(...)            │
    │  │                                                         │
    │  │    if cycle_result.completed:                            │
    │  │      completed.append(deployment)                       │
    │  │    else:                                                │
    │  │      groups[cycle_result.sub_step].append(deployment)   │
    │  └─────────────────────────────────────────────────────────┘
    │
    │  Phase 3: Apply route changes (in-progress only)
    │  ┌─────────────────────────────────────────────────────────┐
    │  │  Collect route changes from PROVISIONING/PROGRESSING:   │
    │  │    scale_out_creators → create new routes               │
    │  │    scale_in_updater → terminate old routes              │
    │  │  repo.scale_routes(scale_out, scale_in)                │
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
  }
```

#### Key Design Principles

1. **Route changes are applied by the evaluator**: scale_out/scale_in are applied once in the evaluator. Individual handlers do not touch routes.
2. **Strategy FSMs live in the evaluator**: `_rolling_update_evaluate()`, `_blue_green_evaluate()` and other strategy FSM logic are internal helper methods of the evaluator.
3. **Only grouping is returned**: The evaluator classifies deployments by sub-step; actual processing (revision swap, deploying_revision cleanup, etc.) is delegated to handlers.

### Per-Sub-Step Handlers

Each handler is registered with a `(DeploymentLifecycleType, DeploymentSubStep)` composite key in the coordinator.

#### DeployingInProgressHandler (PROVISIONING / PROGRESSING)

```python
class DeployingInProgressHandler(DeploymentHandler):
    @classmethod
    def name(cls) -> str:
        return "deploying_in_progress"

    @classmethod
    def target_statuses(cls) -> list[EndpointLifecycle]:
        return [EndpointLifecycle.DEPLOYING]

    @classmethod
    def next_status(cls) -> EndpointLifecycle | None:
        return EndpointLifecycle.DEPLOYING  # DEPLOYING -> DEPLOYING

    @classmethod
    def failure_status(cls) -> EndpointLifecycle | None:
        return None

    async def execute(self, deployments):
        # Route changes already applied by evaluator
        return DeploymentExecutionResult(successes=list(deployments))

    async def post_process(self, result):
        if result.successes:
            await self._deployment_controller.mark_lifecycle_needed(
                DeploymentLifecycleType.DEPLOYING       # reschedule next cycle
            )
        await self._route_controller.mark_lifecycle_needed(
            RouteLifecycleType.PROVISIONING              # trigger new route provisioning
        )

        # Revision swap for completed deployments
        # (coordinator attaches eval_result.completed to result.completed)
        if result.completed:
            swap_ids = [d.id for d in result.completed
                        if d.deploying_revision_id is not None]
            if swap_ids:
                await repo.complete_deployment_revision_swap(swap_ids)
```

`next_status()=DEPLOYING` so the coordinator records DEPLOYING→DEPLOYING SUCCESS history for in-progress deployments. The deployment stays in DEPLOYING state and is re-evaluated next cycle.

For completed deployments, the coordinator passes `EvaluationResult.completed` to this handler's `post_process` via `result.completed`. The handler performs the revision swap, then the coordinator transitions the deployment to READY with history recording.

#### DeployingRolledBackHandler (ROLLED_BACK)

```python
class DeployingRolledBackHandler(DeploymentHandler):
    @classmethod
    def name(cls) -> str:
        return "deploying_rolled_back"

    @classmethod
    def next_status(cls) -> EndpointLifecycle | None:
        return EndpointLifecycle.READY  # DEPLOYING -> READY

    async def execute(self, deployments):
        # deploying_revision = NULL (current_revision preserved)
        clear_ids = [d.id for d in deployments if d.deploying_revision_id is not None]
        if clear_ids:
            await self._deployment_executor._deployment_repo.clear_deploying_revision(clear_ids)
        return DeploymentExecutionResult(successes=list(deployments))
```

On rollback, only `deploying_revision` is cleared; `current_revision` is preserved. The coordinator transitions to READY.

### Coordinator Evaluator Path (`_process_with_evaluator`)

The coordinator takes a separate path for lifecycle types that have an evaluator registered in `_deployment_evaluators`:

```
_process_with_evaluator(lifecycle_type, evaluator)
    │
    │  1. Acquire distributed lock (evaluator.lock_id)
    │  2. Query DEPLOYING-state deployments
    │
    │  3. Enter DeploymentRecorderContext.scope()
    │  ┌───────────────────────────────────────────────────────────────┐
    │  │                                                               │
    │  │  eval_result = evaluator.evaluate(deployments)                │
    │  │                                                               │
    │  │  for sub_step, group in eval_result.groups:                   │
    │  │    handler = handlers[(lifecycle_type, sub_step)]             │
    │  │    result = handler.execute(group)                            │
    │  │    handler_results[sub_step] = (handler, result)              │
    │  │                                                               │
    │  │  all_records = pool.build_all_records()                       │
    │  │                                                               │
    │  │  for sub_step, (handler, result) in handler_results:          │
    │  │    _handle_status_transitions(handler, result, all_records)   │
    │  │    ↑ same generic transition logic as single-handler path     │
    │  │                                                               │
    │  └───────────────────────────────────────────────────────────────┘
    │
    │  4. Attach completed deployments to PROGRESSING handler's result
    │  if eval_result.completed:
    │    handler_results[PROGRESSING].result.completed = eval_result.completed
    │
    │  5. Post-process outside RecorderContext scope
    │  for sub_step, (handler, result) in handler_results:
    │    handler.post_process(result)
    │    ↑ PROGRESSING handler performs revision swap for result.completed
    │
    │  6. Lifecycle transition for completed deployments
    │  if eval_result.completed:
    │    _transition_completed_deployments(completed, all_records)
    │    ↑ DEPLOYING → READY + history recording
    │
    ▼
```

Key: `_handle_status_transitions()` uses the **exact same generic method** as the single-handler path. It performs batch updates and history recording based on each handler's `next_status()`/`failure_status()`. Completed deployments bypass this path — their lifecycle transition is handled by `_transition_completed_deployments()` after the revision swap in `post_process`.

### Sub-Step Recording

Each cycle evaluation produces sub-step variants recorded via the existing `DeploymentRecorderContext`. Both the evaluator and handlers execute within the same RecorderContext scope, so all sub-steps are collected into a single execution record.

The coordinator's `_handle_status_transitions()` calls `extract_sub_steps_for_entity()` for each handler's result, including the deployment's sub-step information in the history.

#### Rolling Update Per-Cycle Recording Examples

**PROVISIONING cycle** — new routes still being provisioned:

```
sub_steps:
  [rolling_update_evaluate] classify_routes      → success
  [rolling_update_evaluate] wait_provisioning     → success
  [strategy_result]         determine_sub_step    → success (message: "provisioning")
```

**PROGRESSING cycle** — creating new routes / terminating old routes:

```
sub_steps:
  [rolling_update_evaluate] classify_routes      → success
  [rolling_update_evaluate] check_completion     → success
  [rolling_update_evaluate] calculate_surge      → success
  [rolling_update_evaluate] build_route_changes  → success
  [strategy_result]         determine_sub_step   → success (message: "progressing")
```

**COMPLETED cycle** — all new routes healthy, no old routes remaining:

```
sub_steps:
  [rolling_update_evaluate] classify_routes      → success
  [rolling_update_evaluate] check_completion     → success
  [strategy_result]         determine_sub_step   → success (message: "completed")
```

The revision swap (`complete_deployment_revision_swap`) is performed by the PROGRESSING handler's `post_process` outside the recorder scope, so it does not appear in sub_steps. The coordinator then transitions the deployment to READY with history recording.

Format is `[phase] step`. The `determine_sub_step` step's `message` field records the determined sub-step value. This information is stored as JSON in the `deployment_history` table's `sub_steps` column and is queryable via API/CLI.

This enables:

- **Observability**: Each deployment's progress is tracked per-entity with sub-step granularity (e.g., "provisioning", "progressing", "completed")
- **Debugging**: The sub-step history shows exactly which phase each deployment was in at each cycle
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
