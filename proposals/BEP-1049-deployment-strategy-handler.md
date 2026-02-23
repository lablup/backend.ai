---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2026-02-20
Created-Version: 26.3.0
Target-Version:
Implemented-Version:
---

<!-- context-for-ai
type: master-bep
scope: Introduce DeploymentStrategyHandler interface for multi-cycle deployment strategies (blue-green, rolling update) separate from one-shot DeploymentHandler
key-constraints:
  - DeploymentHandler interface must NOT be modified
  - Strategy handlers process DEPLOYING state only
  - DeploymentLifecycleType is for handler operations only; strategy tasks use DeploymentStrategy enum directly
key-decisions:
  - Separate interface (DeploymentStrategyHandler) instead of extending DeploymentHandler
  - Strategy filtering happens in coordinator, not executor
  - DeploymentStrategyResult uses completed/in_progress/errors instead of successes/skipped/errors
  - Strategy periodic tasks use DeploymentStrategy enum, not DeploymentLifecycleType
  - Separate event types (DoDeploymentStrategyEvent) instead of reusing lifecycle events with string prefix dispatching
phases: 2
-->

# Zero-Downtime Deployment Strategy Architecture

## Related Issues

- Parent BEP: [BEP-1006: Service Deployment Strategy](BEP-1006-service-deployment-strategy.md)
- Related BEP: [BEP-1030: Sokovan Scheduler Status Transition Design](BEP-1030-sokovan-scheduler-status-transition.md)

## Motivation

BEP-1006 defined the high-level design for Blue-Green and Rolling Update deployment strategies. This BEP covers the **implementation architecture** — how these strategies integrate into the existing Sokovan deployment lifecycle system.

Core problem: **`DeploymentHandler` assumes one-shot state transitions, but deployment strategies are inherently multi-cycle.**

Blue-Green deployment spans multiple coordinator cycles through several phases:

1. **Cycle 1**: Create Green routes with `INACTIVE` traffic → still `DEPLOYING`
2. **Cycle 2-N**: Green routes still provisioning → still `DEPLOYING`
3. **Cycle N+1**: All Green routes healthy → switch traffic, transition to `READY`

Rolling Update similarly progresses gradually across cycles. Both strategies **keep the deployment in `DEPLOYING` state across multiple processing cycles until strategy completion or rollback.**

Why `DeploymentHandler` cannot express this pattern:

| Aspect | `DeploymentHandler` (existing) | What deployment strategies need |
|--------|-------------------------------|--------------------------------|
| **State transition** | Static: `successes` → `next_status` | `completed` → `READY`, `in_progress` → keep |
| **Routing** | Based on `target_statuses()` | Shared `DEPLOYING` → needs policy(`strategy`)-based branching |
| **Cycles** | One-shot execution | Multi-cycle (reschedule) |

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
│  DeploymentTaskSpec (for handlers)        StrategyTaskSpec (for strategies)  │
│  ┌────────────────────────────┐           ┌──────────────────────────────┐   │
│  │ check_pending: 2s / 30s   │           │ ROLLING:    5s / 30s         │   │
│  │ check_replica: 5s / 30s   │           │ BLUE_GREEN: 5s / 30s         │   │
│  │ scaling:       5s / 30s   │           │                              │   │
│  │ reconcile:     — / 30s    │           │                              │   │
│  │ destroying:    5s / 60s   │           │                              │   │
│  └─────────────┬──────────────┘           └──────────────┬───────────────┘   │
│                │                                         │                   │
│                ▼                                         ▼                   │
│  DoDeploymentLifecycleEvent              DoDeploymentStrategyEvent           │
│  DoDeploymentLifecycleIfNeededEvent      DoDeploymentStrategyIfNeededEvent   │
│  (lifecycle_type: str)                   (strategy_type: str)                │
└────────────────┬─────────────────────────────────────────┬───────────────────┘
                 │                                         │
                 ▼                                         ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          ScheduleEventHandler                                │
│                                                                              │
│  handle_do_deployment_lifecycle*()       handle_do_deployment_strategy*()    │
│  → DeploymentLifecycleType conversion    → DeploymentStrategy conversion     │
└────────────────┬─────────────────────────────────────────┬───────────────────┘
                 │                                         │
                 ▼                                         ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         DeploymentCoordinator                                │
│                                                                              │
│  ┌─── Handler Path ────────────────┐    ┌─── Strategy Path ──────────────┐  │
│  │                              │    │                                    │  │
│  │  process_deployment_         │    │  process_deployment_               │  │
│  │    lifecycle(type)           │    │    strategy(strategy)              │  │
│  │                              │    │                                    │  │
│  │  1. handler = handlers[type] │    │  1. handler = strategy_handlers    │  │
│  │  2. deployments =            │    │       [strategy]                   │  │
│  │       by_statuses(target)    │    │  2. deployments = DEPLOYING        │  │
│  │  3. result = execute(deps)   │    │  3. Load policy_map                │  │
│  │  4. transitions()            │    │  4. Filter by policy strategy      │  │
│  │  5. post_process()           │    │  5. result = execute(deps,         │  │
│  │                              │    │       policy_map)                  │  │
│  │  Result:                     │    │  6. strategy_transitions()         │  │
│  │    successes → next_status   │    │  7. in_progress → reschedule       │  │
│  │    errors → failure_status   │    │                                    │  │
│  │    skipped → keep            │    │  Result:                           │  │
│  │                              │    │    completed → READY               │  │
│  └──────────────────────────────┘    │    in_progress → keep DEPLOYING    │  │
│                                      │    errors → keep DEPLOYING + log   │  │
│                                      └────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
                 │                                         │
                 ▼                                         ▼
┌──────────────────────────────┐    ┌──────────────────────────────────────────┐
│     DeploymentHandler        │    │       DeploymentStrategyHandler          │
│     (existing, unchanged)    │    │       (new interface)                    │
│                              │    │                                          │
│  name() → str                │    │  name() → str                            │
│  target_statuses() → [...]   │    │  strategy() → DeploymentStrategy         │
│  next_status() → Lifecycle   │    │  lock_id → LockID | None                 │
│  failure_status() → ...      │    │  execute(deployments, policy_map)         │
│  execute(deployments)        │    │    → DeploymentStrategyResult             │
│    → DeploymentExecResult    │    │                                          │
│                              │    │                                          │
│  Implementations:            │    │  Implementations:                        │
│  ├─ CheckPendingDeployment   │    │  ├─ RollingUpdateStrategyHandler          │
│  ├─ ScalingDeployment        │    │  └─ BlueGreenStrategyHandler              │
│  ├─ CheckReplicaDeployment   │    │                                          │
│  ├─ ReconcileDeployment      │    │                                          │
│  └─ DestroyingDeployment     │    │                                          │
└──────────────────────────────┘    └──────────────────────────────────────────┘
                 │                                         │
                 └────────────────┬────────────────────────┘
                                  ▼
                    ┌──────────────────────────┐
                    │   DeploymentExecutor     │
                    │   (business logic)       │
                    └──────────────────────────┘
```

### Endpoint Lifecycle State Machine

```
PENDING → SCALING → READY ⇄ DEPLOYING
                      ↓
                  DESTROYING → DESTROYED
```

`DEPLOYING` is entered when a new revision update is triggered on a deployment in the `READY` state. Which strategy processes it is determined by `DeploymentPolicyData.strategy`.

### Event Separation: Lifecycle vs Strategy

Lifecycle and strategy use **separate event types**. This separates event handlers so each handles a single concern:

```
┌─────────────────────────────┐    ┌─────────────────────────────┐
│  Lifecycle Events            │    │  Strategy Events             │
│                             │    │                             │
│  DoDeploymentLifecycle*     │    │  DoDeploymentStrategy*      │
│  Event                      │    │  Event                      │
│  ┌───────────────────────┐  │    │  ┌───────────────────────┐  │
│  │ lifecycle_type: str   │  │    │  │ strategy_type: str    │  │
│  │ ("check_pending" etc) │  │    │  │ ("ROLLING" etc)       │  │
│  └───────────────────────┘  │    │  └───────────────────────┘  │
│           │                 │    │           │                 │
│           ▼                 │    │           ▼                 │
│  handle_do_deployment_      │    │  handle_do_deployment_      │
│    lifecycle*()             │    │    strategy*()              │
│           │                 │    │           │                 │
│           ▼                 │    │           ▼                 │
│  coordinator.process_       │    │  coordinator.process_       │
│    deployment_lifecycle()   │    │    deployment_strategy()    │
└─────────────────────────────┘    └─────────────────────────────┘
```

Valkey markings share a unified keyspace but are distinguished by key convention:

| Type | Key Format | Example |
|------|-----------|---------|
| Handler lifecycle | `{DeploymentLifecycleType.value}` | `"check_pending"`, `"scaling"` |
| Strategy | `"strategy_{DeploymentStrategy.value.lower()}"` | `"strategy_rolling"` |

### Revision Activation Trigger Branching

Revision switching (`activate_revision`) and general updates (`update_deployment`) take different paths:

```
activate_revision(deployment_id, revision_id)
    │
    ├─ Policy lookup: deployment_policy exists?
    │
    ├─ No policy (existing behavior)
    │    → current_revision = revision_id (immediate swap)
    │    → mark("check_replica")
    │
    └─ Policy exists (strategy deployment)
         → deploying_revision = revision_id
         → lifecycle = DEPLOYING
         ├─ BLUE_GREEN → mark("strategy_blue_green")
         └─ ROLLING    → mark("strategy_rolling")

update_deployment(replica_count, metadata, ...)
    │
    └─ Always mark("check_replica")  ← strategy-independent
```

Replica count changes are additions/removals of the same revision, so no strategy is needed.
Only revision switching requires safe replacement of new code/models, so it uses the strategy path.

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
- [BEP-1029: Sokovan ObserverHandler Pattern](BEP-1029-sokovan-observer-handler.md) — Precedent for creating separate handler interfaces
- [BEP-1030: Sokovan Scheduler Status Transition Design](BEP-1030-sokovan-scheduler-status-transition.md) — State transition patterns of the Sokovan scheduler
