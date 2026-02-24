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

## Green Route Traffic Isolation

Green routes are created with `traffic_status=INACTIVE` and `traffic_ratio=0.0`. The coordinator's periodic sync only propagates ACTIVE routes to AppProxy, so Green routes are invisible to the proxy until promotion. Even if a route leaks through, both Traefik and legacy (HTTP/TCP) backends reject routes with `traffic_ratio=0`.

On promotion, the Manager updates the DB (`Green→ACTIVE`, `Blue→INACTIVE`); the coordinator sync automatically propagates the change to AppProxy. Only the DB write is required — no separate proxy configuration is needed.

## Cycle FSM

The coordinator periodically calls `execute_blue_green_cycle`. Each invocation follows this FSM:

```
  ┌──────────────────────────────────────┐
  │  No Green routes?                    │──Yes──→ Create all Green (INACTIVE)
  └──────────────────┬───────────────────┘        → creating
                     No
                     ▼
  ┌──────────────────────────────────────┐
  │  Any Green PROVISIONING?             │──Yes──→ provisioning
  └──────────────────┬───────────────────┘
                     No
                     ▼
  ┌──────────────────────────────────────┐
  │  All Green failed?                   │──Yes──→ Terminate Green → rolled_back
  └──────────────────┬───────────────────┘
                     No
                     ▼
  ┌──────────────────────────────────────┐
  │  All Green healthy?                  │──No───→ waiting
  └──────────────────┬───────────────────┘
                    Yes
                     ▼
  ┌──────────────────────────────────────┐
  │  auto_promote?                       │──No───→ waiting_promotion (manual)
  └──────────────────┬───────────────────┘
                    Yes
                     ▼
  ┌──────────────────────────────────────┐
  │  promote_delay elapsed?              │──No───→ waiting_promotion (delay)
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

### CycleStatus Variants

Each cycle evaluation returns one of the following statuses:

| Status | Condition | Coordinator Action |
|--------|-----------|-------------------|
| **creating** | No Green routes → created all as INACTIVE | `mark_deployment_needed` reschedule |
| **provisioning** | Green routes are PROVISIONING | `mark_deployment_needed` reschedule |
| **waiting** | Not all Green healthy (mixed state, no PROVISIONING) | `mark_deployment_needed` reschedule |
| **waiting_promotion** | All Green healthy, waiting for promotion trigger | Manual: no reschedule (promotion API triggers mark). Delay: reschedule aligned to `promote_ready_at` |
| **completed** | Promotion executed (Green→ACTIVE, Blue→TERMINATING) | Revision swap, DEPLOYING → READY |
| **rolled_back** | All Green failed → terminate Green | `deploying_revision` = NULL, DEPLOYING → READY |

## promote_delay_seconds Handling

Auto-promotion timing is derived from the route's `status_updated_at` column — no separate state storage needed.

`RoutingRow.status_updated_at` records the last time the route's status changed. When all Green routes are healthy, the latest `status_updated_at` among them indicates when the last route became healthy.

```
  Each cycle (all Green healthy):
  ┌──────────────────────────────────────────────────────────────┐
  │  last_healthy_at = max(green_routes.status_updated_at        │
  │                        where status == HEALTHY)              │
  │                                                              │
  │  now() - last_healthy_at >= promote_delay_seconds?           │
  │    Yes → Execute promotion                                   │
  │    No  → waiting_promotion                                   │
  └──────────────────────────────────────────────────────────────┘
```

If a route becomes unhealthy and recovers, `status_updated_at` is updated on recovery, so the delay timer automatically resets — ensuring promotion only occurs after stable health.

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
  │  → waiting_promotion (manual)                      │
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
  │  → rolled_back                                      │
  └─────────────────────────────────────────────────────┘

  Legend: ■ = healthy, ✗ = failed
```

## Component Structure

```
  ┌──────────────────────────────────────────────────────────────┐
  │  DeploymentCoordinator                                       │
  │                                                              │
  │  strategy_registry: {                                        │
  │    BLUE_GREEN: BlueGreenCycleEvaluator,                      │
  │    ROLLING:    RollingUpdateCycleEvaluator,                   │
  │  }                                                           │
  │                                                              │
  │  process_deployment_strategy(strategy)                       │
  │    1. Query DEPLOYING deployments                            │
  │    2. Load policy_map                                        │
  │    3. Filter deployments by policy strategy                  │
  │    4. evaluator = strategy_registry[strategy]                │
  │    5. result = evaluator.execute(deployments, policy_map)    │
  │    6. completed   → transition to READY                      │
  │       rolled_back → deploying_revision=NULL, READY           │
  │       creating     → mark_deployment_needed reschedule       │
  │       provisioning → mark_deployment_needed reschedule       │
  │       waiting      → mark_deployment_needed reschedule       │
  │       waiting_promotion → manual: no reschedule              │
  │                           delay: reschedule on timer         │
  │       errors → log history                                   │
  └──────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  BlueGreenCycleEvaluator                                     │
  │                                                              │
  │  lock_id → LOCKID_DEPLOYMENT_BLUE_GREEN                      │
  │                                                              │
  │  evaluate(deployment, routes, policy)                        │
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
