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

The `DeploymentStrategyEvaluator` periodically evaluates each Rolling Update deployment. Each invocation follows this FSM:

```
  ┌──────────────────────────────────────┐
  │  Any New routes PROVISIONING?        │──Yes──→ provisioning (wait)
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

Rollback is **not** decided by the FSM itself. If all new routes fail, the FSM will keep attempting to create new routes via the surge/unavailable calculation. Eventually the DEPLOYING timeout (30 min) is exceeded and the coordinator transitions the deployment to ROLLING_BACK via the `expired` path.

### Route Classification

Routes are classified by revision and status:

| Category | Condition | Description |
|----------|-----------|-------------|
| `old_active` | revision != deploying_revision, is_active() | Old routes currently serving traffic |
| `new_provisioning` | revision == deploying_revision, PROVISIONING | New routes being created |
| `new_healthy` | revision == deploying_revision, HEALTHY | New routes ready to serve |
| `new_unhealthy` | revision == deploying_revision, UNHEALTHY/DEGRADED | New routes with issues |
| `new_failed` | revision == deploying_revision, FAILED/TERMINATED | New routes that failed |

### Handler Flow

All DEPLOYING deployments are handled by `DeployingProvisioningHandler`, which stays in the PROVISIONING sub-step throughout the entire deployment lifecycle. The handler runs the strategy evaluator each cycle:

| Result | Condition | Handler Action |
|--------|-----------|----------------|
| **success** | Evaluator returns COMPLETED (no Old routes, New healthy >= desired) | Coordinator transitions to READY |
| **need_retry** | Route mutations executed (create/drain) | Stays in DEPLOYING/PROVISIONING, history recorded |
| **skipped** | No changes — routes still provisioning or waiting | No transition; coordinator checks for timeout |
| **expired** | Skipped deployment exceeds DEPLOYING timeout (30 min) | Coordinator transitions to DEPLOYING/ROLLING_BACK |

When a deployment transitions to ROLLING_BACK, the `DeployingRollingBackHandler` clears `deploying_revision` and transitions directly to READY.

### Safety Guards

- **Zero-downtime protection**: When `max_unavailable < desired`, never terminates ALL old routes until at least one new route is healthy
- **Deadlock prevention**: `RollingUpdateSpec` validator ensures at least one of `max_surge` or `max_unavailable` is positive
- **Timeout-based rollback**: The FSM does not detect failure — the coordinator's timeout mechanism handles it. If the deployment cannot complete within the DEPLOYING timeout (30 min), the coordinator transitions to ROLLING_BACK via the `expired` path

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
  │  → need_retry (route mutations executed)             │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
  Cycle 1 (New provisioning)
  ┌─────────────────────────────────────────────────────┐
  │  Old: [■ ■]    (2 healthy)                          │
  │  New: [◇]      (1 provisioning)                     │
  │                                                     │
  │  → PROVISIONING exists → skipped (wait)             │
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
  │  → need_retry (route mutations executed)             │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
  Cycle 3 (New provisioning)
  ┌─────────────────────────────────────────────────────┐
  │  Old: [■]      (1 healthy)                          │
  │  New: [■ ◇]    (1 healthy, 1 provisioning)          │
  │                                                     │
  │  → PROVISIONING exists → skipped (wait)             │
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
  │  → need_retry (route mutations executed)             │
  └─────────────────────────────────────────────────────┘
                          │
                          ▼
  Cycle 5 (waiting for provisioning)
  ┌─────────────────────────────────────────────────────┐
  │  Old: []                                            │
  │  New: [■ ■ ◇]  (2 healthy, 1 provisioning)          │
  │                                                     │
  │  → PROVISIONING exists → skipped (wait)             │
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
  │  → success → coordinator transitions to READY       │
  └─────────────────────────────────────────────────────┘

  Legend: ■ = healthy, ◇ = provisioning
```

## Timeout and Rollback

Deploying timeout is handled through the coordinator's generic `expired` transition mechanism:

1. `DeployingProvisioningHandler` declares `expired → DEPLOYING/ROLLING_BACK` in `status_transitions()`
2. Each cycle, the coordinator checks `result.skipped` deployments against the DEPLOYING timeout (30 min)
3. Timeout is measured using `phase_started_at` from `DeploymentWithHistory` — the `created_at` of the first scheduling history record for this handler phase
4. `phase_started_at` is stable across retries: history records with same phase/error_code/to_status are merged (only `attempts` incremented, `created_at` unchanged)
5. Timed-out deployments transition to DEPLOYING/ROLLING_BACK
6. `DeployingRollingBackHandler` clears `deploying_revision` and transitions to READY

No separate timeout handler or periodic task is needed — timeout checking is built into the coordinator's standard transition handling.

## Component Structure

```
  ┌──────────────────────────────────────────────────────────────┐
  │  DeploymentStrategyEvaluator                                 │
  │  (evaluator — strategy FSM + route changes)                  │
  │                                                              │
  │  evaluate(deployments) → EvaluationResult                    │
  │    1. Load policy_map, route_map                             │
  │    2. For each deployment:                                   │
  │         policy = policy_map[deployment.id]                   │
  │         strategy = policy.strategy                           │
  │    3. Dispatch by strategy:                                  │
  │         ROLLING → rolling_update_evaluate(...)               │
  │    4. Aggregate route changes + group by sub_step            │
  │  Coordinator applies route changes after evaluation          │
  └──────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  rolling_update_evaluate(deployment, routes, spec)           │
  │  (evaluator internal strategy function)                      │
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
  │  Route changes returned (applied by applier):                │
  │  ┌────────────────────────────────────────────────────┐      │
  │  │  rollout_specs: RouteCreatorSpec(                  │      │
  │  │    revision_id = deploying_revision,               │      │
  │  │    traffic_status = ACTIVE  ← differs from BG      │      │
  │  │  )                                                 │      │
  │  │                                                    │      │
  │  │  drain_route_ids: old route IDs                    │      │
  │  │    → status = TERMINATING                          │      │
  │  └────────────────────────────────────────────────────┘      │
  └──────────────────────────────────────────────────────────────┘
                             │
                             ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  DeployingProvisioningHandler                                │
  │  (single handler for entire DEPLOYING lifecycle)             │
  │                                                              │
  │  completed → success → coordinator transitions to READY      │
  │  route mutations → need_retry → stays in PROVISIONING        │
  │  no changes → skipped → coordinator checks timeout           │
  │  evaluation errors → errors → classified by coordinator      │
  │                                                              │
  │  DeployingRollingBackHandler                                 │
  │  (cleanup on timeout)                                        │
  │                                                              │
  │  clear deploying_revision → success → READY                  │
  └──────────────────────────────────────────────────────────────┘
```

## Revision Swap on Completion

When all Old routes are removed and New routes reach desired_replicas or above as healthy:

```
  completed determination (evaluator)
       │
       ▼
  StrategyResultApplier.apply()
    → Atomic transaction:
      1. complete_deployment_revision_swap(ids)
         current_revision = deploying_revision
         deploying_revision = NULL
      2. Returns completed_ids in StrategyApplyResult
       │
       ▼
  DeployingProvisioningHandler
    → completed_ids → successes
    → coordinator transitions DEPLOYING → READY
    → History recording
```
