# Rolling Update Deployment Strategy

- Parent: [BEP-1049: Zero-Downtime Deployment Strategy Architecture](../BEP-1049-deployment-strategy-handler.md)
- Related: [Blue-Green Deployment Strategy](./blue-green.md)

## Overview

Rolling Update is a deployment strategy that **gradually** replaces existing routes (Old Revision) with new routes (New Revision). Two parameters — `max_surge` and `max_unavailable` — control the replacement pace, and the deployment remains in `DEPLOYING` state across multiple cycles until the full replacement is complete.

### Configuration

```
RollingUpdateSpec:
  max_surge: int = 1           # Max additional routes to create simultaneously beyond desired_replicas
  max_unavailable: int = 0     # Max unavailable routes to allow relative to desired_replicas
```

## Revision Tracking

The `endpoints` table has two columns for revision management:

- `deploying_revision` — The revision currently being deployed (NULL when no deployment is in progress)
- `current_revision` — The revision currently serving traffic

## Cycle FSM

The `DeployingDeploymentHandler` periodically evaluates each Rolling Update deployment. Each invocation follows this FSM:

```
  ┌──────────────────────────────────────┐
  │  Any New routes PROVISIONING?        │──Yes──→ provisioning
  └──────────────────┬───────────────────┘
                     No
                     ▼
  ┌──────────────────────────────────────────────────┐
  │  No Old and New healthy >= desired_replicas?     │──Yes──→ completed (replacement done)
  └──────────────────┬───────────────────────────────┘
                     No
                     ▼
  ┌──────────────────────────────────────┐
  │  Calculate max_surge/max_unavailable │
  │                                      │
  │  to_create = min(can_create,         │
  │                  need_create)        │
  │  to_terminate = min(can_terminate,   │
  │                     old_active)      │
  │                                      │
  │  → Create New routes (ACTIVE)        │
  │  → Terminate Old routes (TERMINATING)│
  └──────────────────────────────────────┘
                     │
                     ▼
                progressing
```

### Sub-Step Variants

Each cycle evaluation directly returns one of the shared sub-step variants:

| Sub-Step | Condition | Handler Action |
|----------|-----------|----------------|
| **provisioning** | New routes are PROVISIONING | `successes` → SUCCESS history (DEPLOYING→DEPLOYING), reschedule |
| **progressing** | Calculated surge/unavailable, created/terminated routes | `successes` → SUCCESS history (DEPLOYING→DEPLOYING), reschedule |
| **completed** | No Old routes and New healthy >= desired_replicas | Handler transitions DEPLOYING→READY directly, revision swap |

## max_surge / max_unavailable Calculation

Example with `desired_replicas = 3`, `max_surge = 1`, `max_unavailable = 1`:

```
  Constraints:
  ┌──────────────────────────────────────────────────────────┐
  │  max_total = desired_replicas + max_surge = 4            │
  │  → Total active routes cannot exceed 4                   │
  │                                                          │
  │  min_available = desired_replicas - max_unavailable = 2  │
  │  → Healthy routes must not drop below 2                  │
  └──────────────────────────────────────────────────────────┘

  Creation calculation:
  ┌────────────────────────────────────────────────────────────────────┐
  │  can_create = max(0, max_total - total_active)                     │
  │  need_create = max(0, desired_replicas - new_healthy - new_prov)   │
  │  to_create = min(can_create, need_create)                          │
  └────────────────────────────────────────────────────────────────────┘

  Termination calculation:
  ┌──────────────────────────────────────────────────────────┐
  │  healthy_count = new_healthy + old_active                │
  │  can_terminate = max(0, healthy_count - min_available)   │
  │  to_terminate = min(can_terminate, old_active)           │
  └──────────────────────────────────────────────────────────┘
```

## Cycle-by-Cycle Execution Example

`desired_replicas=3`, `max_surge=1`, `max_unavailable=1`:

```
  Cycle 0 (initial state)
  ┌─────────────────────────────────────────────────────┐
  │  Old: [■ ■ ■]  (3 healthy)                          │
  │  New: []                                            │
  │                                                     │
  │  total_active=3, max_total=4 → can_create=1         │
  │  need_create=3 → to_create=1                        │
  │  healthy=3, min_available=2 → can_terminate=1       │
  │                                                     │
  │  → Create 1 New, Terminate 1 Old                    │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
  Cycle 1 (New provisioning)
  ┌─────────────────────────────────────────────────────┐
  │  Old: [■ ■]    (2 healthy)                          │
  │  New: [◇]      (1 provisioning)                     │
  │                                                     │
  │  → PROVISIONING exists → wait                       │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
  Cycle 2 (1 New healthy)
  ┌─────────────────────────────────────────────────────┐
  │  Old: [■ ■]    (2 healthy)                          │
  │  New: [■]      (1 healthy)                          │
  │                                                     │
  │  total_active=3, max_total=4 → can_create=1         │
  │  need_create=2 → to_create=1                        │
  │  healthy=3, min_available=2 → can_terminate=1       │
  │                                                     │
  │  → Create 1 New, Terminate 1 Old                    │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
  Cycle 3 (New provisioning)
  ┌─────────────────────────────────────────────────────┐
  │  Old: [■]      (1 healthy)                          │
  │  New: [■ ◇]    (1 healthy, 1 provisioning)          │
  │                                                     │
  │  → PROVISIONING exists → wait                       │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
  Cycle 4 (2 New healthy)
  ┌─────────────────────────────────────────────────────┐
  │  Old: [■]      (1 healthy)                          │
  │  New: [■ ■]    (2 healthy)                          │
  │                                                     │
  │  total_active=3, max_total=4 → can_create=1         │
  │  need_create=1 → to_create=1                        │
  │  healthy=3, min_available=2 → can_terminate=1       │
  │                                                     │
  │  → Create 1 New, Terminate 1 Old                    │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
  Cycle 5 (waiting for provisioning)
  ┌─────────────────────────────────────────────────────┐
  │  Old: []                                            │
  │  New: [■ ■ ◇]  (2 healthy, 1 provisioning)          │
  │                                                     │
  │  → PROVISIONING exists → wait                       │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
  Cycle 6 (completed)
  ┌─────────────────────────────────────────────────────┐
  │  Old: []                                            │
  │  New: [■ ■ ■]  (3 healthy)                          │
  │                                                     │
  │  No Old and New >= desired_replicas → completed     │
  │  → deploying_revision → current_revision swap       │
  │  → DEPLOYING → READY state transition               │
  └─────────────────────────────────────────────────────┘

  Legend: ■ = healthy, ◇ = provisioning
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
  │         ROLLING_UPDATE → rolling_update_evaluate(...)        │
  │    4. Classify by sub_step:                                   │
  │         completed    → handler transitions DEPLOYING→READY   │
  │         in-progress  → successes (SUCCESS history, resched.) │
  │         errors       → errors                                │
  └──────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  rolling_update_evaluate(deployment, routes, policy)         │
  │  (internal strategy evaluation function)                     │
  │                                                              │
  │  Route classification:                                       │
  │  ┌────────────────────────────────────────────────────┐      │
  │  │  old_routes:  revision != deploying_revision       │      │
  │  │  new_routes:  revision == deploying_revision       │      │
  │  │                                                    │      │
  │  │  new_provisioning: new + PROVISIONING              │      │
  │  │  new_healthy:      new + HEALTHY                   │      │
  │  │  old_active:       old + is_active()               │      │
  │  └────────────────────────────────────────────────────┘      │
  │                                                              │
  │  Actions applied:                                            │
  │  ┌────────────────────────────────────────────────────┐      │
  │  │  scale_out: RouteCreatorSpec(                      │      │
  │  │    revision_id = deploying_revision,               │      │
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

When all Old routes are removed and New routes reach desired_replicas or above as healthy:

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
