# Blue-Green Deployment Strategy

- Parent: [BEP-1049: Zero-Downtime Deployment Strategy Architecture](../BEP-1049-deployment-strategy-handler.md)
- Related: [Rolling Update Deployment Strategy](./rolling-update.md)

## Overview

Blue-Green is a deployment strategy that creates **all** new routes (Green) while keeping existing routes (Blue), then **atomically** switches traffic once all Green routes are healthy. Green routes are created with `INACTIVE` status and receive no traffic until promotion.

### Configuration

```
BlueGreenSpec:
  auto_promote: bool = False          # Whether to auto-switch traffic when all Green are healthy
  promote_delay_seconds: int = 0      # Wait time before auto-promotion (seconds)
```

On strategy failure (all Green routes fail), automatic rollback always occurs.

## Revision Tracking

The `endpoints` table has two columns for revision management:

- `deploying_revision` — The revision currently being deployed (NULL when no deployment is in progress)
- `current_revision` — The revision currently serving traffic

## Cycle FSM

The coordinator periodically calls `execute_blue_green_cycle`. Each invocation follows this FSM:

```
  ┌──────────────────────────────────────┐
  │  No deploying_revision?              │──Yes──→ in_progress (skip)
  └──────────────────┬───────────────────┘
                     No
                     ▼
  ┌──────────────────────────────────────┐
  │  No Green routes?                    │──Yes──→ Create all Green (INACTIVE)
  └──────────────────┬───────────────────┘        → in_progress
                     No
                     ▼
  ┌──────────────────────────────────────┐
  │  Any Green PROVISIONING?             │──Yes──→ in_progress (wait)
  └──────────────────┬───────────────────┘
                     No
                     ▼
  ┌──────────────────────────────────────┐
  │  All Green failed?                   │──Yes──→ Terminate Green → completed (rollback)
  └──────────────────┬───────────────────┘
                     No
                     ▼
  ┌──────────────────────────────────────┐
  │  All Green healthy?                  │──No───→ in_progress (mixed state)
  └──────────────────┬───────────────────┘
                    Yes
                     ▼
  ┌──────────────────────────────────────┐
  │  auto_promote?                       │──No───→ in_progress (manual wait)
  └──────────────────┬───────────────────┘
                    Yes
                     ▼
  ┌──────────────────────────────────────┐
  │  promote_delay elapsed?              │──No───→ in_progress (delay wait)
  └──────────────────┬───────────────────┘
                    Yes
                     ▼
  ┌──────────────────────────────────────┐
  │  Execute promotion                   │
  │  → Green INACTIVE → ACTIVE           │
  │  → Blue  ACTIVE   → TERMINATING      │
  └──────────────────────────────────────┘
                     │
                     ▼
                 completed
```

## promote_delay_seconds Handling

Auto-promotion can wait a specified duration before switching. The timestamp is stored in Valkey:

```
  All Green confirmed healthy
       │
       ▼
  ┌──────────────────────────────────────────────────┐
  │  Store promote_ready_at in Valkey                │
  │                                                  │
  │  Key: deployment:{endpoint_id}:promote_ready_at  │
  │  Value: now() + promote_delay_seconds            │
  │  TTL: promote_delay_seconds + buffer             │
  └──────────────────────────────────────────────────┘
       │
       ▼ (next cycle)
  ┌──────────────────────────────────────────────────┐
  │  Query promote_ready_at                          │
  │                                                  │
  │  now() >= promote_ready_at? ──Yes──→ Execute promotion │
  │                              No───→ in_progress  │
  └──────────────────────────────────────────────────┘

  On loss: if promote_ready_at missing, re-store → delay restarts (safe side)
```

## Cycle-by-Cycle Execution Example

`target=3`, `auto_promote=True`, `promote_delay_seconds=0`:

```
  Cycle 0 (initial state)
  ┌─────────────────────────────────────────────────────┐
  │  Blue:  [■ ■ ■]  (3 healthy, ACTIVE)                │
  │  Green: []                                          │
  │                                                     │
  │  No Green routes                                    │
  │  → Create all 3 Green (INACTIVE)                    │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
  Cycle 1 (Green provisioning)
  ┌─────────────────────────────────────────────────────┐
  │  Blue:  [■ ■ ■]  (3 healthy, ACTIVE)                │
  │  Green: [◇ ◇ ◇]  (3 provisioning, INACTIVE)         │
  │                                                     │
  │  → PROVISIONING exists → wait                       │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
  Cycle 2 (some Green healthy)
  ┌─────────────────────────────────────────────────────┐
  │  Blue:  [■ ■ ■]  (3 healthy, ACTIVE)                │
  │  Green: [■ ◇ ◇]  (1 healthy, 2 provisioning)        │
  │                                                     │
  │  → PROVISIONING exists → wait                       │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
  Cycle 3 (all Green healthy — promotion)
  ┌─────────────────────────────────────────────────────┐
  │  Blue:  [■ ■ ■]  (3 healthy, ACTIVE)                │
  │  Green: [■ ■ ■]  (3 healthy, INACTIVE)              │
  │                                                     │
  │  All Green healthy + auto_promote + delay=0         │
  │  → Green: INACTIVE → ACTIVE                         │
  │  → Blue:  ACTIVE → TERMINATING                      │
  │  → completed                                        │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
  Final state
  ┌─────────────────────────────────────────────────────┐
  │  Blue:  []                                          │
  │  Green: [■ ■ ■]  (3 healthy, ACTIVE)                │
  │                                                     │
  │  → deploying_revision → current_revision swap       │
  │  → DEPLOYING → READY state transition               │
  └─────────────────────────────────────────────────────┘

  Legend: ■ = healthy, ◇ = provisioning
```

### Manual Promotion Scenario

With `auto_promote=False`:

```
  Cycle N (all Green healthy)
  ┌─────────────────────────────────────────────────────┐
  │  Blue:  [■ ■ ■]  (3 healthy, ACTIVE)                │
  │  Green: [■ ■ ■]  (3 healthy, INACTIVE)              │
  │                                                     │
  │  All Green healthy but auto_promote=False           │
  │  → in_progress (waiting for manual promotion)       │
  └─────────────────────────────────────────────────────┘
                          │
                  Operator calls manual promotion API
                          │
                          ▼
  ┌─────────────────────────────────────────────────────┐
  │  Green: INACTIVE → ACTIVE                           │
  │  Blue:  ACTIVE → TERMINATING                        │
  │  → completed                                        │
  └─────────────────────────────────────────────────────┘
```

### Rollback Scenario

```
  Cycle N (all Green failed)
  ┌─────────────────────────────────────────────────────┐
  │  Blue:  [■ ■ ■]  (3 healthy, ACTIVE)                │
  │  Green: [✗ ✗ ✗]  (3 failed)                         │
  │                                                     │
  │  All Green failed                                   │
  │  → Terminate all Green (TERMINATING)                │
  │  → deploying_revision = NULL (rollback)             │
  │  → completed                                        │
  └─────────────────────────────────────────────────────┘

  Legend: ■ = healthy, ✗ = failed
```

## Component Structure

```
  ┌──────────────────────────────────────────────────────────────┐
  │  DeploymentCoordinator                                       │
  │                                                              │
  │  process_deployment_strategy(BLUE_GREEN)                     │
  │    1. Query DEPLOYING deployments                            │
  │    2. Load policy_map                                        │
  │    3. Filter deployments with strategy == BLUE_GREEN         │
  │    4. handler.execute(matching, policy_map)                  │
  │    5. completed → transition to READY                        │
  │       in_progress → mark_deployment_needed reschedule        │
  │       errors → log history                                   │
  └──────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  BlueGreenStrategyHandler                                    │
  │                                                              │
  │  name() → "blue-green"                                       │
  │  strategy() → DeploymentStrategy.BLUE_GREEN                  │
  │  lock_id → LOCKID_DEPLOYMENT_BLUE_GREEN                      │
  │                                                              │
  │  execute(deployments, policy_map)                            │
  │    → executor.execute_blue_green_cycle(...)                  │
  └──────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  DeploymentExecutor.execute_blue_green_cycle()               │
  │                                                              │
  │  1. fetch_active_routes_by_endpoint_ids (bulk)               │
  │  2. Execute _evaluate_blue_green_cycle per deployment        │
  │  3. completed deployments →                                  │
  │       complete_deployment_revision_update_bulk               │
  │  4. Return DeploymentStrategyResult                          │
  └──────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  _evaluate_blue_green_cycle (single deployment)              │
  │                                                              │
  │  Route classification:                                       │
  │  ┌────────────────────────────────────────────────────┐      │
  │  │  blue_routes:  revision != deploying_revision      │      │
  │  │  green_routes: revision == deploying_revision      │      │
  │  │                                                    │      │
  │  │  green_provisioning: green + PROVISIONING          │      │
  │  │  green_healthy:      green + HEALTHY               │      │
  │  │  green_failed:       green + ERROR/TERMINATED      │      │
  │  │  blue_active:        blue + is_active()            │      │
  │  └────────────────────────────────────────────────────┘      │
  │                                                              │
  │  Actions applied:                                            │
  │  ┌────────────────────────────────────────────────────┐      │
  │  │  ● Green creation:                                 │      │
  │  │    RouteCreatorSpec(                                │     │
  │  │      revision_id = deploying_revision,             │      │
  │  │      traffic_status = INACTIVE  ← differs from RU  │      │
  │  │    ) × target_count                                │      │
  │  │                                                    │      │
  │  │  ● Promotion (traffic switch):                     │      │
  │  │    Green: RouteBatchUpdaterSpec(                    │     │
  │  │      traffic_status = ACTIVE                       │      │
  │  │    )                                               │      │
  │  │    Blue: RouteBatchUpdaterSpec(                     │     │
  │  │      status = TERMINATING,                         │      │
  │  │      traffic_status = INACTIVE                     │      │
  │  │    )                                               │      │
  │  │                                                    │      │
  │  │  ● Rollback:                                       │      │
  │  │    Green: RouteBatchUpdaterSpec(                    │     │
  │  │      status = TERMINATING                          │      │
  │  │    )                                               │      │
  │  └────────────────────────────────────────────────────┘      │
  └──────────────────────────────────────────────────────────────┘
```

## Revision Swap on Completion

When all Green routes become ACTIVE and Blue routes are terminated:

```
  completed determination
       │
       ▼
  complete_deployment_revision_update_bulk({endpoint_id: deploying_revision})
       │
       ├─ current_revision = deploying_revision
       └─ deploying_revision = NULL

             │
             ▼
  Coordinator: DEPLOYING → READY state transition
```

## Comparison with Rolling Update

| Aspect | Blue-Green | Rolling Update |
|--------|------------|---------------|
| **Route creation** | All at once | Gradual (max_surge controlled) |
| **New route traffic** | `INACTIVE` (waits until promotion) | `ACTIVE` (receives traffic immediately) |
| **Old route removal** | All at once on promotion | Gradual (max_unavailable controlled) |
| **Traffic switch** | Atomic (activate Green + terminate Blue) | Gradual (concurrent with new route creation) |
| **Configuration** | `auto_promote`, `promote_delay_seconds` | `max_surge`, `max_unavailable` |
| **Resource usage** | 2× resources during switch | Only max_surge additional resources |
| **Rollback** | Just terminate Green (Blue still running) | Recovery needed from partial replacement state |
