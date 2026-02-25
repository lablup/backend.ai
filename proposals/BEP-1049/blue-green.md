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

The `DeployingDeploymentHandler` periodically evaluates each Blue-Green deployment. Each invocation follows this FSM:

```
  ┌──────────────────────────────────────┐
  │  No Green routes?                    │──Yes──→ Create all Green (INACTIVE)
  └──────────────────┬───────────────────┘        → provisioning
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
  │  All Green healthy?                  │──No───→ progressing
  └──────────────────┬───────────────────┘
                    Yes
                     ▼
  ┌──────────────────────────────────────┐
  │  auto_promote?                       │──No───→ progressing (manual)
  └──────────────────┬───────────────────┘
                    Yes
                     ▼
  ┌──────────────────────────────────────┐
  │  promote_delay elapsed?              │──No───→ progressing (delay)
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

### Sub-Step Variants

Each cycle evaluation directly returns one of the shared sub-step variants:

| Sub-Step | Condition | Handler Action |
|----------|-----------|----------------|
| **provisioning** | No Green routes → created all as INACTIVE | `successes` → SUCCESS history (DEPLOYING→DEPLOYING), reschedule |
| **provisioning** | Green routes are PROVISIONING | `successes` → SUCCESS history (DEPLOYING→DEPLOYING), reschedule |
| **progressing** | Not all Green healthy (mixed state, no PROVISIONING) | `successes` → SUCCESS history (DEPLOYING→DEPLOYING), reschedule |
| **progressing** | All Green healthy, waiting for promotion trigger (manual or delay) | `successes` → SUCCESS history (DEPLOYING→DEPLOYING), reschedule |
| **completed** | Promotion executed (Green→ACTIVE, Blue→TERMINATING) | Handler transitions DEPLOYING→READY directly, revision swap |
| **rolled_back** | All Green failed → terminate Green | Handler transitions DEPLOYING→READY directly, deploying_revision=NULL |

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
  │  DeployingDeploymentHandler                                  │
  │                                                              │
  │  name()             → "deploying"                            │
  │  target_statuses()  → [DEPLOYING]                            │
  │  next_status()      → None  (handler owns transitions)        │
  │                                                              │
  │  execute(deployments) → DeploymentExecutionResult            │
  │    1. Load policy_map                                        │
  │    2. For each deployment:                                   │
  │         policy = policy_map[deployment.id]                   │
  │         strategy = policy.strategy                           │
  │    3. Dispatch by strategy:                                  │
  │         BLUE_GREEN → blue_green_evaluate(...)                │
  │    4. Classify by sub_step:                                   │
  │         completed    → handler transitions DEPLOYING→READY   │
  │         rolled_back  → handler transitions, dep_rev=NULL     │
  │         in-progress  → successes (SUCCESS history, resched.) │
  │         errors       → errors                                │
  └──────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  blue_green_evaluate(deployment, routes, policy)             │
  │  (internal strategy evaluation function)                     │
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
  │  │    RouteCreatorSpec(                               │      │
  │  │      revision_id = deploying_revision,             │      │
  │  │      traffic_status = INACTIVE  ← differs from RU  │      │
  │  │    ) × target_count                                │      │
  │  │                                                    │      │
  │  │  ● Promotion (traffic switch):                     │      │
  │  │    Green: RouteBatchUpdaterSpec(                   │      │
  │  │      traffic_status = ACTIVE                       │      │
  │  │    )                                               │      │
  │  │    Blue: RouteBatchUpdaterSpec(                    │      │
  │  │      status = TERMINATING,                         │      │
  │  │      traffic_status = INACTIVE                     │      │
  │  │    )                                               │      │
  │  │                                                    │      │
  │  │  ● Rollback:                                       │      │
  │  │    Green: RouteBatchUpdaterSpec(                   │      │
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
  RevisionStateUpdaterSpec(
    current_revision = deploying_revision,
    deploying_revision = NULL
  )
       │
       ▼
  Handler records history + transitions DEPLOYING → READY directly
  (via update_endpoint_lifecycle_bulk_with_history)
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
