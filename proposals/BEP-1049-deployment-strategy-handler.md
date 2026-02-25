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

How `DeploymentHandler` expresses this pattern:

| Aspect | How DeploymentHandler expresses it |
|--------|-----------------------------------|
| **State transition** | Handler owns all transitions directly (`next_status()=None`). Completed/rolled_back → handler transitions DEPLOYING→READY. In-progress → `successes` (SUCCESS history, no state change). Errors → `errors`. |
| **Routing** | `target_statuses()` returns `[DEPLOYING]`, `execute()` dispatches by `policy.strategy` |
| **Cycles** | In-progress results placed in `successes` → handler records SUCCESS history (DEPLOYING→DEPLOYING) → rescheduled on next cycle |

Because `next_status()` is `None`, the coordinator's generic success/failure handling is entirely skipped. The handler records all history entries and lifecycle transitions directly. This is necessary because the handler needs to record different history for completed items (DEPLOYING→READY) and in-progress items (DEPLOYING→DEPLOYING) in a single execution cycle.

## Sub-documents

| Document | Description |
|----------|-------------|
| [Rolling Update](BEP-1049/rolling-update.md) | Gradual route replacement strategy — max_surge/max_unavailable control |
| [Blue-Green](BEP-1049/blue-green.md) | Atomic traffic switch strategy — INACTIVE staging + promotion |

## Proposed Design

### Overall Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          Periodic Task Scheduler                             │
│                                                                              │
│  DeploymentTaskSpec                                                          │
│  ┌────────────────────────────┐                                              │
│  │ check_pending: 2s / 30s    │                                              │
│  │ check_replica: 5s / 30s    │                                              │
│  │ scaling:       5s / 30s    │                                              │
│  │ deploying:     5s / 30s    │  ← NEW: drives deployment strategy cycles    │
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
│                          ScheduleEventHandler                                │
│                                                                              │
│  handle_do_deployment_lifecycle*()                                           │
│  → DeploymentLifecycleType conversion                                        │
└────────────────┬─────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         DeploymentCoordinator                                │
│                                                                              │
│  process_deployment_lifecycle(type)                                          │
│    1. handler = handlers[type]                                               │
│    2. deployments = by_statuses(handler.target_statuses())                   │
│    3. result = handler.execute(deployments)                                  │
│    4. transitions()                                                          │
│    5. post_process()                                                         │
│                                                                              │
│  Result (generic path, next_status != None):                                 │
│    successes → next_status                                                   │
│    errors → failure_status                                                   │
│    skipped → keep                                                            │
│                                                                              │
│  Result (deploying handler, next_status == None):                            │
│    Handler records all history + transitions directly                        │
└────────────────┬─────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  DeploymentHandler                                                           │
│                                                                              │
│  name() → str                                                                │
│  target_statuses() → [...]                                                   │
│  next_status() → Lifecycle                                                   │
│  failure_status() → ...                                                      │
│  execute(deployments) → DeploymentExecutionResult                            │
│                                                                              │
│  Implementations:                                                            │
│  ├─ CheckPendingDeployment     target: [PENDING]    → SCALING                │
│  ├─ ScalingDeployment          target: [SCALING]    → READY                  │
│  ├─ CheckReplicaDeployment     target: [READY]      → READY                  │
│  ├─ DeployingDeployment        target: [DEPLOYING]  → (self)     ← NEW      │
│  ├─ ReconcileDeployment        target: [*]          → (same)                 │
│  └─ DestroyingDeployment       target: [DESTROYING] → DESTROYED              │
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

Endpoints in `DEPLOYING` state are excluded from auto-scaling rule evaluation. During a strategy-based deployment, the handler is actively managing route creation and termination (surge/unavailable for Rolling Update, Green staging for Blue-Green). If auto-scaling were to concurrently add or remove routes, it would conflict with the handler's route management — potentially violating surge limits, terminating routes the handler expects to exist, or creating routes with the wrong revision.

Auto-scaling resumes automatically once the deployment completes and the endpoint returns to `READY`.

### Sub-Step Variants

Both Blue-Green and Rolling Update cycle FSMs share a common set of **sub-step variants**. Each cycle evaluation directly returns one of these variants — no strategy-specific statuses or mapping layer exists:

| Sub-Step | Description | Handler Action |
|----------|-------------|----------------|
| **provisioning** | New routes being created or still in PROVISIONING state | `successes` — SUCCESS history (DEPLOYING→DEPLOYING), reschedule |
| **progressing** | Strategy making active progress — health checks pending, promotion waiting, or routes being replaced | `successes` — SUCCESS history (DEPLOYING→DEPLOYING), reschedule |
| **completed** | Strategy finished successfully — all new routes serving traffic | Handler transitions DEPLOYING→READY directly, revision swap |
| **rolled_back** | Strategy failed — rolled back to previous revision | Handler transitions DEPLOYING→READY directly, deploying_revision=NULL |

### DeployingDeploymentHandler

`DeployingDeploymentHandler` implements the standard `DeploymentHandler` interface. Its `execute()` method dispatches to the appropriate strategy evaluator based on each deployment's policy:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  DeployingDeploymentHandler                                                  │
│                                                                              │
│  name()             → "deploying"                                            │
│  target_statuses()  → [DEPLOYING]                                            │
│  next_status()      → None  (handler owns all transitions)                   │
│  failure_status()   → None                                                   │
│                                                                              │
│  execute(deployments) → DeploymentExecutionResult                            │
│    1. Load policy_map and route_map for all deployments                      │
│    2. For each deployment:                                                   │
│         policy = policy_map[deployment.id]                                   │
│         strategy = policy.strategy  (BLUE_GREEN | ROLLING)                   │
│         sub_step = evaluate_cycle(strategy, deployment, routes, spec)        │
│    3. Classify by sub_step:                                                  │
│         completed/rolled_back → completed (handler transitions directly)     │
│         provisioning/progressing → in_progress (→ result.successes)          │
│         no policy/unsupported → skipped                                      │
│         exception → errors                                                   │
│    4. Apply route changes (scale_out + scale_in)                             │
│    5. Complete revision swap for completed deployments                       │
│    6. Record history for all: completed (→READY) + in_progress (→DEPLOYING) │
│                                                                              │
│  evaluate_cycle(strategy, deployment, routes, spec)                          │
│    ├─ BLUE_GREEN → blue_green_evaluate(deployment, routes, spec)             │
│    └─ ROLLING    → rolling_update_evaluate(deployment, routes, spec)         │
└──────────────────────────────────────────────────────────────────────────────┘
```

The strategy evaluation functions (`blue_green_evaluate`, `rolling_update_evaluate`) contain the same cycle FSM logic described in the sub-documents, but are invoked as internal helpers rather than standalone evaluator objects.

### Sub-Step Recording and Handler-Owned History

Each cycle evaluation produces a sub-step variant that is recorded via the existing `DeploymentRecorderContext`. The handler records **all** history entries directly (not through the coordinator) because it needs to write different `to_status` values in a single execution:

- **Completed items**: SUCCESS history with `from_status=DEPLOYING, to_status=READY` + lifecycle batch update
- **In-progress items**: SUCCESS history with `from_status=DEPLOYING, to_status=DEPLOYING` (history only, no state change)

Both are written atomically via `update_endpoint_lifecycle_bulk_with_history()`. Because `next_status()` returns `None`, the coordinator's generic `_handle_status_transitions()` is entirely skipped for this handler.

This enables:

- **Observability**: Each deployment's progress is tracked per-entity with sub-step granularity (e.g., "provisioning", "waiting", "progressing")
- **Debugging**: The sub-step history shows exactly which phase each deployment was in at each cycle
- **Consistency**: The same recording mechanism used by all other handlers applies to deploying

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
