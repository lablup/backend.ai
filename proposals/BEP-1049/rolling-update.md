<!-- context-for-ai
type: sub-document
parent: BEP-1049
scope: Rolling update deployment strategy - gradual route replacement with max_surge/max_unavailable constraints
key-constraints:
  - Uses DeploymentStrategyHandler interface from BEP-1049
  - All routes use ACTIVE traffic status (unlike Blue-Green which uses INACTIVE)
  - max_surge and max_unavailable control the pace of replacement
  - Each cycle waits for provisioning routes before taking further action
-->

# Rolling Update Deployment Strategy

- Parent: [BEP-1049: Zero-Downtime Deployment Strategy Architecture](../BEP-1049-deployment-strategy-handler.md)
- Related: [Blue-Green Deployment Strategy](./blue-green.md)

## Overview

Rolling Update is a deployment strategy that **gradually** replaces existing routes (Old Revision) with new routes (New Revision). Two parameters — `max_surge` and `max_unavailable` — control the replacement pace, and the deployment remains in `DEPLOYING` state across multiple cycles until the full replacement is complete.

### Configuration

```
RollingUpdateSpec:
  max_surge: int = 1           # Max additional routes to create simultaneously beyond target count
  max_unavailable: int = 0     # Max unavailable routes to allow relative to target count
```

## Cycle FSM

The coordinator periodically calls `execute_rolling_update_cycle`. Each invocation follows this FSM:

```
  ┌──────────────────────────────────────┐
  │  No deploying_revision_id?           │──Yes──→ in_progress (skip)
  └──────────────────┬───────────────────┘
                     No
                     ▼
  ┌──────────────────────────────────────┐
  │  Any New routes PROVISIONING?        │──Yes──→ in_progress (wait)
  └──────────────────┬───────────────────┘
                     No
                     ▼
  ┌──────────────────────────────────────┐
  │  No Old and New healthy >= target?   │──Yes──→ completed (replacement done)
  └──────────────────┬───────────────────┘
                     No
                     ▼
  ┌──────────────────────────────────────┐
  │  Calculate max_surge/max_unavailable │
  │                                      │
  │  to_create = min(can_create,         │
  │                  need_create)         │
  │  to_terminate = min(can_terminate,   │
  │                     old_active)       │
  │                                      │
  │  → Create New routes (ACTIVE)        │
  │  → Terminate Old routes (TERMINATING)│
  └──────────────────────────────────────┘
                     │
                     ▼
                in_progress
```

## max_surge / max_unavailable Calculation

Example with `target_count = 3`, `max_surge = 1`, `max_unavailable = 1`:

```
  Constraints:
  ┌──────────────────────────────────────────────────────────┐
  │  max_total = target_count + max_surge = 4               │
  │  → Total active routes cannot exceed 4                   │
  │                                                          │
  │  min_available = target_count - max_unavailable = 2      │
  │  → Healthy routes must not drop below 2                  │
  └──────────────────────────────────────────────────────────┘

  Creation calculation:
  ┌──────────────────────────────────────────────────────────┐
  │  can_create = max(0, max_total - total_active)           │
  │  need_create = max(0, target - new_healthy - new_prov)   │
  │  to_create = min(can_create, need_create)                │
  └──────────────────────────────────────────────────────────┘

  Termination calculation:
  ┌──────────────────────────────────────────────────────────┐
  │  healthy_count = new_healthy + old_active                 │
  │  can_terminate = max(0, healthy_count - min_available)    │
  │  to_terminate = min(can_terminate, old_active)            │
  └──────────────────────────────────────────────────────────┘
```

## Cycle-by-Cycle Execution Example

`target=3`, `max_surge=1`, `max_unavailable=1`:

```
  Cycle 0 (initial state)
  ┌─────────────────────────────────────────────────────┐
  │  Old: [■ ■ ■]  (3 healthy)                          │
  │  New: []                                             │
  │                                                      │
  │  total_active=3, max_total=4 → can_create=1          │
  │  need_create=3 → to_create=1                         │
  │  healthy=3, min_available=2 → can_terminate=1        │
  │                                                      │
  │  → Create 1 New, Terminate 1 Old                     │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
  Cycle 1 (New provisioning)
  ┌─────────────────────────────────────────────────────┐
  │  Old: [■ ■]    (2 healthy)                           │
  │  New: [◇]      (1 provisioning)                      │
  │                                                      │
  │  → PROVISIONING exists → wait                        │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
  Cycle 2 (1 New healthy)
  ┌─────────────────────────────────────────────────────┐
  │  Old: [■ ■]    (2 healthy)                           │
  │  New: [■]      (1 healthy)                           │
  │                                                      │
  │  total_active=3, max_total=4 → can_create=1          │
  │  need_create=2 → to_create=1                         │
  │  healthy=3, min_available=2 → can_terminate=1        │
  │                                                      │
  │  → Create 1 New, Terminate 1 Old                     │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
  Cycle 3 (New provisioning)
  ┌─────────────────────────────────────────────────────┐
  │  Old: [■]      (1 healthy)                           │
  │  New: [■ ◇]    (1 healthy, 1 provisioning)           │
  │                                                      │
  │  → PROVISIONING exists → wait                        │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
  Cycle 4 (2 New healthy)
  ┌─────────────────────────────────────────────────────┐
  │  Old: [■]      (1 healthy)                           │
  │  New: [■ ■]    (2 healthy)                           │
  │                                                      │
  │  total_active=3, max_total=4 → can_create=1          │
  │  need_create=1 → to_create=1                         │
  │  healthy=3, min_available=2 → can_terminate=1        │
  │                                                      │
  │  → Create 1 New, Terminate 1 Old                     │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
  Cycle 5 (waiting for provisioning)
  ┌─────────────────────────────────────────────────────┐
  │  Old: []                                             │
  │  New: [■ ■ ◇]  (2 healthy, 1 provisioning)          │
  │                                                      │
  │  → PROVISIONING exists → wait                        │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
  Cycle 6 (completed)
  ┌─────────────────────────────────────────────────────┐
  │  Old: []                                             │
  │  New: [■ ■ ■]  (3 healthy)                           │
  │                                                      │
  │  No Old and New >= target → completed                │
  │  → deploying_revision → current_revision swap        │
  │  → DEPLOYING → READY state transition                │
  └─────────────────────────────────────────────────────┘

  Legend: ■ = healthy, ◇ = provisioning
```

## Component Structure

```
  ┌──────────────────────────────────────────────────────────────┐
  │  DeploymentCoordinator                                       │
  │                                                              │
  │  process_deployment_strategy(ROLLING)                        │
  │    1. Query DEPLOYING deployments                            │
  │    2. Load policy_map                                        │
  │    3. Filter deployments with strategy == ROLLING            │
  │    4. handler.execute(matching, policy_map)                   │
  │    5. completed → transition to READY                        │
  │       in_progress → mark_deployment_needed reschedule        │
  │       errors → log history                                   │
  └──────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  RollingUpdateStrategyHandler                                │
  │                                                              │
  │  name() → "rolling-update"                                   │
  │  strategy() → DeploymentStrategy.ROLLING                     │
  │  lock_id → LOCKID_DEPLOYMENT_ROLLING_UPDATE                  │
  │                                                              │
  │  execute(deployments, policy_map)                             │
  │    → executor.execute_rolling_update_cycle(...)               │
  └──────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  DeploymentExecutor.execute_rolling_update_cycle()           │
  │                                                              │
  │  1. fetch_active_routes_by_endpoint_ids (bulk)               │
  │  2. Execute _evaluate_rolling_update_cycle per deployment    │
  │  3. completed deployments →                                  │
  │       complete_deployment_revision_update_bulk                │
  │  4. Return DeploymentStrategyResult                          │
  └──────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  _evaluate_rolling_update_cycle (single deployment)          │
  │                                                              │
  │  Route classification:                                       │
  │  ┌────────────────────────────────────────────────────┐      │
  │  │  old_routes:  revision != deploying_revision_id    │      │
  │  │  new_routes:  revision == deploying_revision_id    │      │
  │  │                                                    │      │
  │  │  new_provisioning: new + PROVISIONING              │      │
  │  │  new_healthy:      new + HEALTHY                   │      │
  │  │  old_active:       old + is_active()               │      │
  │  └────────────────────────────────────────────────────┘      │
  │                                                              │
  │  Actions applied:                                            │
  │  ┌────────────────────────────────────────────────────┐      │
  │  │  scale_out: RouteCreatorSpec(                      │      │
  │  │    revision_id = deploying_revision_id,            │      │
  │  │    traffic_status = ACTIVE  ← differs from BG      │      │
  │  │  )                                                 │      │
  │  │                                                    │      │
  │  │  scale_in: RouteBatchUpdaterSpec(                  │      │
  │  │    status = TERMINATING,                           │      │
  │  │    traffic_status = INACTIVE                       │      │
  │  │  )                                                 │      │
  │  └────────────────────────────────────────────────────┘      │
  └──────────────────────────────────────────────────────────────┘
```

## Revision Swap on Completion

When all Old routes are removed and New routes reach target count or above as healthy:

```
  completed determination
       │
       ▼
  complete_deployment_revision_update_bulk({endpoint_id: deploying_revision_id})
       │
       ├─ current_revision_id = deploying_revision_id
       └─ deploying_revision_id = NULL
       │
       ▼
  Coordinator: DEPLOYING → READY state transition
```
