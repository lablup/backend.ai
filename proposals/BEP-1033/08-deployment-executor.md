# DeploymentExecutor Test Scenarios

## Overview

Test scenarios for `DeploymentExecutor` based on actual code behavior.

The DeploymentExecutor handles:
1. **Check Pending Deployments**: Register endpoints with proxy
2. **Check Scaling Needs**: Verify replica counts
3. **Scale Deployment**: Scale routes out/in
4. **Calculate Desired Replicas**: Calculate autoscaling replicas
5. **Destroy Deployment**: Terminate routes and unregister endpoints

**Source Files:** `sokovan/deployment/executor.py`

---

## Dependencies (Mock Targets)

- `deployment_repo: DeploymentRepository`
  - `fetch_scaling_group_proxy_targets()` -> `Mapping[str, ScalingGroupProxyTarget]`
  - `update_endpoint_urls_bulk()` -> `None`
  - `fetch_active_routes_by_endpoint_ids()` -> `Mapping[UUID, Sequence[RouteData]]`
  - `scale_routes()` -> `None`
  - `fetch_auto_scaling_rules_by_endpoint_ids()` -> `Mapping[UUID, Sequence[AutoScalingRule]]`
  - `fetch_metrics_for_autoscaling()` -> `AutoScalingMetricsData`
  - `update_desired_replicas_bulk()` -> `None`
  - `calculate_desired_replicas_for_deployment()` -> `Optional[int]`
  - `mark_terminating_route_status_bulk()` -> `None`
- `client_pool: ClientPool`
  - `load_client_session()` -> `ClientSession`
- `AppProxyClient` (internally created)
  - `create_endpoint()` -> `dict` with "endpoint" key
  - `delete_endpoint()` -> `None`

---

## Result Types

```python
@dataclass
class DeploymentExecutionResult:
    successes: list[DeploymentInfo]
    errors: list[DeploymentExecutionError]
    skipped: list[DeploymentInfo]

@dataclass
class DeploymentExecutionError:
    deployment_info: DeploymentInfo
    reason: str
    error_detail: str
```

---

## check_pending_deployments Scenarios

### SC-DE-001: Endpoint Registration Success for All Deployments

- **Purpose**: Verify endpoints are registered with proxy for all deployments
- **Dependencies (Mock):**
  - `deployment_repo.fetch_scaling_group_proxy_targets({"sg1"})`:
    - Returns: `{"sg1": ScalingGroupProxyTarget(addr="proxy:8080", api_token="token")}`
  - `AppProxyClient.create_endpoint(d1.id, request_body)`:
    - Returns: `{"endpoint": "https://endpoint1.example.com"}`
  - `deployment_repo.update_endpoint_urls_bulk({d1.id: "https://endpoint1.example.com"})`:
    - Returns: `None`
- **Input:**
  - Deployment `d1` with target_revision (resource_group="sg1")
- **Execution:** `await executor.check_pending_deployments([deployment])`
- **Verification:**
  - `DeploymentExecutionResult`:
    - `successes = [d1]`
    - `errors = []`
  - `create_endpoint` called
  - `update_endpoint_urls_bulk` called
- **Classification**: `happy-path`

---

### SC-DE-002: Deployment Without Target Revision Skipped

- **Purpose**: Verify deployments without target_revision are ignored
- **Dependencies (Mock):**
  - `deployment_repo.fetch_scaling_group_proxy_targets()`:
    - Returns: `{"sg1": ScalingGroupProxyTarget(...)}`
- **Input:**
  - Deployment `d1` with `target_revision = None`
- **Execution:** `await executor.check_pending_deployments([deployment])`
- **Verification:**
  - `DeploymentExecutionResult`:
    - `successes = []`
    - `errors = []`
  - Warning logged
  - `create_endpoint.assert_not_called()`
- **Classification**: `edge-case`

---

### SC-DE-003: Scaling Group Without Proxy Target Skipped

- **Purpose**: Verify deployments in scaling groups without proxy targets are ignored
- **Dependencies (Mock):**
  - `deployment_repo.fetch_scaling_group_proxy_targets({"sg1"})`:
    - Returns: `{"sg1": None}` or `{}`
- **Input:**
  - Deployment with `resource_group = "sg1"`
- **Execution:** `await executor.check_pending_deployments([deployment])`
- **Verification:**
  - `successes = []`
  - `errors = []`
  - Warning logged
- **Classification**: `edge-case`

---

### SC-DE-004: Endpoint Registration Failure Captured as Error

- **Purpose**: Verify proxy registration failure is captured as error
- **Dependencies (Mock):**
  - `deployment_repo.fetch_scaling_group_proxy_targets()`:
    - Returns: Valid proxy target
  - `AppProxyClient.create_endpoint()`:
    - Raises: `Exception("Connection refused")`
- **Input:**
  - Valid deployment `d1`
- **Execution:** `await executor.check_pending_deployments([deployment])`
- **Verification:**
  - `DeploymentExecutionResult`:
    - `successes = []`
    - `errors = [DeploymentExecutionError(d1, "Connection refused", "Failed to register endpoint")]`
- **Classification**: `error-case`

---

### SC-DE-005: Partial Success - Some Deployments Fail

- **Purpose**: Verify successful deployments proceed when some fail
- **Dependencies (Mock):**
  - `deployment_repo.fetch_scaling_group_proxy_targets()`:
    - Returns: Valid proxy target
  - `AppProxyClient.create_endpoint(d1.id, ...)`:
    - Returns: `{"endpoint": "https://endpoint1.example.com"}`
  - `AppProxyClient.create_endpoint(d2.id, ...)`:
    - Raises: `Exception("Timeout")`
- **Input:**
  - 2 deployments: `d1`, `d2`
- **Execution:** `await executor.check_pending_deployments([d1, d2])`
- **Verification:**
  - `successes = [d1]`
  - `errors = [DeploymentExecutionError(d2, ...)]`
  - `update_endpoint_urls_bulk` called only for d1
- **Classification**: `error-case`

---

## check_ready_deployments_that_need_scaling Scenarios

### SC-DE-006: Replica Count Matches - Success

- **Purpose**: Verify success when actual route count matches target replica count
- **Dependencies (Mock):**
  - `deployment_repo.fetch_active_routes_by_endpoint_ids({d1.id})`:
    - Returns: `{d1.id: [route1, route2, route3]}`
- **Input:**
  - Deployment `d1` with `target_replica_count = 3`
- **Execution:** `await executor.check_ready_deployments_that_need_scaling([d1])`
- **Verification:**
  - `successes = [d1]`
  - `errors = []`
- **Classification**: `happy-path`

---

### SC-DE-007: Replica Count Mismatch - Error

- **Purpose**: Verify ReplicaCountMismatch error when route count differs from target
- **Dependencies (Mock):**
  - `deployment_repo.fetch_active_routes_by_endpoint_ids({d1.id})`:
    - Returns: `{d1.id: [route1, route2]}` (only 2)
- **Input:**
  - Deployment `d1` with `target_replica_count = 3`
- **Execution:** `await executor.check_ready_deployments_that_need_scaling([d1])`
- **Verification:**
  - `successes = []`
  - `errors = [DeploymentExecutionError(d1, "Mismatched active routes", ...)]`
- **Classification**: `error-case`

---

## scale_deployment Scenarios

### SC-DE-008: Scale Out - Create Routes

- **Purpose**: Verify new routes created when target replicas > current
- **Dependencies (Mock):**
  - `deployment_repo.fetch_active_routes_by_endpoint_ids({d1.id})`:
    - Returns: `{d1.id: [route1]}` (1)
  - `deployment_repo.scale_routes(creators, None)`:
    - Returns: `None`
- **Input:**
  - Deployment `d1` with `target_replica_count = 3`
- **Execution:** `await executor.scale_deployment([d1])`
- **Verification:**
  - `successes = [d1]`
  - `scale_routes` called with 2 Creators
- **Classification**: `happy-path`

---

### SC-DE-009: Scale In - Terminate Routes

- **Purpose**: Verify routes terminated when target replicas < current
- **Dependencies (Mock):**
  - `deployment_repo.fetch_active_routes_by_endpoint_ids({d1.id})`:
    - Returns: `{d1.id: [route1, route2, route3, route4]}` (4)
  - `deployment_repo.scale_routes([], updater)`:
    - Returns: `None`
- **Input:**
  - Deployment `d1` with `target_replica_count = 2`
- **Execution:** `await executor.scale_deployment([d1])`
- **Verification:**
  - `successes = [d1]`
  - `scale_routes` called with BatchUpdater containing 2 route IDs
  - Updater status is `TERMINATING`
- **Classification**: `happy-path`

---

### SC-DE-010: No Scaling Needed - Skipped

- **Purpose**: Verify deployment skipped when target equals current replica count
- **Dependencies (Mock):**
  - `deployment_repo.fetch_active_routes_by_endpoint_ids({d1.id})`:
    - Returns: `{d1.id: [route1, route2]}` (2)
- **Input:**
  - Deployment `d1` with `target_replica_count = 2`
- **Execution:** `await executor.scale_deployment([d1])`
- **Verification:**
  - `successes = []`
  - `skipped = [d1]`
  - `scale_routes.assert_not_called()`
- **Classification**: `edge-case`

---

## calculate_desired_replicas Scenarios

### SC-DE-011: Calculate Replicas from Autoscaling Rules

- **Purpose**: Verify desired replicas calculated from autoscaling rules
- **Dependencies (Mock):**
  - `deployment_repo.fetch_auto_scaling_rules_by_endpoint_ids({d1.id})`:
    - Returns: `{d1.id: [AutoScalingRule(...)]}`
  - `deployment_repo.fetch_metrics_for_autoscaling(...)`:
    - Returns: `AutoScalingMetricsData(...)`
  - `deployment_repo.calculate_desired_replicas_for_deployment(d1, rules, metrics)`:
    - Returns: `5`
  - `deployment_repo.update_desired_replicas_bulk({d1.id: 5})`:
    - Returns: `None`
- **Input:**
  - Deployment `d1` with autoscaling configured
- **Execution:** `await executor.calculate_desired_replicas([d1])`
- **Verification:**
  - `successes = [d1]`
  - `update_desired_replicas_bulk` called with `{d1.id: 5}`
- **Classification**: `happy-path`

---

### SC-DE-012: No Autoscaling Rules - Manual Scaling

- **Purpose**: Verify manual replica_count used when no autoscaling rules
- **Dependencies (Mock):**
  - `deployment_repo.fetch_auto_scaling_rules_by_endpoint_ids({d1.id})`:
    - Returns: `{d1.id: []}` (empty rules)
  - `deployment_repo.fetch_metrics_for_autoscaling(...)`:
    - Returns: `AutoScalingMetricsData(routes_by_endpoint={d1.id: [route1]})`
- **Input:**
  - Deployment `d1` with `replica_count = 3` (current routes: 1)
- **Execution:** `await executor.calculate_desired_replicas([d1])`
- **Verification:**
  - `successes = [d1]`
  - `update_desired_replicas_bulk` called with `{d1.id: 3}`
- **Classification**: `happy-path`

---

### SC-DE-013: No Change Needed - Skipped

- **Purpose**: Verify skipped when autoscaling result is None
- **Dependencies (Mock):**
  - `deployment_repo.fetch_auto_scaling_rules_by_endpoint_ids({d1.id})`:
    - Returns: `{d1.id: [AutoScalingRule(...)]}`
  - `deployment_repo.calculate_desired_replicas_for_deployment(...)`:
    - Returns: `None` (no change)
- **Input:**
  - Deployment `d1`
- **Execution:** `await executor.calculate_desired_replicas([d1])`
- **Verification:**
  - `successes = []`
  - `skipped = [d1]`
  - `update_desired_replicas_bulk.assert_not_called()`
- **Classification**: `edge-case`

---

### SC-DE-014: Replica Calculation Failure - Error

- **Purpose**: Verify error captured when replica calculation throws exception
- **Dependencies (Mock):**
  - `deployment_repo.fetch_auto_scaling_rules_by_endpoint_ids(...)`:
    - Returns: Valid rules
  - `deployment_repo.calculate_desired_replicas_for_deployment(...)`:
    - Raises: `Exception("Metrics unavailable")`
- **Input:**
  - Deployment `d1`
- **Execution:** `await executor.calculate_desired_replicas([d1])`
- **Verification:**
  - `successes = []`
  - `errors = [DeploymentExecutionError(d1, "Metrics unavailable", "Failed to calculate desired replicas")]`
- **Classification**: `error-case`

---

## destroy_deployment Scenarios

### SC-DE-015: Deployment Destruction Success

- **Purpose**: Verify all routes terminated and endpoint unregistered
- **Dependencies (Mock):**
  - `deployment_repo.fetch_active_routes_by_endpoint_ids({d1.id})`:
    - Returns: `{d1.id: [route1, route2]}`
  - `deployment_repo.fetch_scaling_group_proxy_targets({"sg1"})`:
    - Returns: `{"sg1": ScalingGroupProxyTarget(...)}`
  - `deployment_repo.mark_terminating_route_status_bulk({route1.id, route2.id})`:
    - Returns: `None`
  - `AppProxyClient.delete_endpoint(d1.id)`:
    - Returns: `None`
- **Input:**
  - Deployment `d1` with 2 routes
- **Execution:** `await executor.destroy_deployment([d1])`
- **Verification:**
  - `successes = [d1]`
  - `mark_terminating_route_status_bulk` called with route IDs
  - `delete_endpoint` called
- **Classification**: `happy-path`

---

### SC-DE-016: Endpoint Deletion Failure - Error Captured

- **Purpose**: Verify endpoint deletion failure is captured as error
- **Dependencies (Mock):**
  - `deployment_repo.fetch_active_routes_by_endpoint_ids(...)`:
    - Returns: Valid routes
  - `deployment_repo.fetch_scaling_group_proxy_targets(...)`:
    - Returns: Valid proxy target
  - `deployment_repo.mark_terminating_route_status_bulk(...)`:
    - Returns: `None`
  - `AppProxyClient.delete_endpoint(d1.id)`:
    - Raises: `Exception("Endpoint not found")`
- **Input:**
  - Deployment `d1`
- **Execution:** `await executor.destroy_deployment([d1])`
- **Verification:**
  - `successes = []`
  - `errors = [DeploymentExecutionError(d1, "Failed to unregister endpoint", ...)]`
  - Route status already marked as TERMINATING
- **Classification**: `error-case`

---

### SC-DE-017: No Proxy Target - Log and Continue

- **Purpose**: Verify deployment destruction succeeds even without proxy target
- **Dependencies (Mock):**
  - `deployment_repo.fetch_active_routes_by_endpoint_ids(...)`:
    - Returns: Valid routes
  - `deployment_repo.fetch_scaling_group_proxy_targets({"sg1"})`:
    - Returns: `{"sg1": None}`
  - `deployment_repo.mark_terminating_route_status_bulk(...)`:
    - Returns: `None`
- **Input:**
  - Deployment `d1`
- **Execution:** `await executor.destroy_deployment([d1])`
- **Verification:**
  - `successes = [d1]`
  - Warning logged
  - `delete_endpoint.assert_not_called()`
- **Classification**: `edge-case`

---

## Empty Input Scenarios

### SC-DE-018: Empty Deployment List - Immediate Return

- **Purpose**: Verify early return for empty input
- **Input:**
  - `deployments = []`
- **Execution (all methods):**
  - `await executor.check_pending_deployments([])`
  - `await executor.check_ready_deployments_that_need_scaling([])`
  - `await executor.scale_deployment([])`
  - `await executor.calculate_desired_replicas([])`
  - `await executor.destroy_deployment([])`
- **Verification:**
  - All cases: `DeploymentExecutionResult(successes=[], errors=[], skipped=[])`
  - Minimal repository calls
- **Classification**: `edge-case`

---

## Integration Scenarios

### SC-DE-INT-001: Full Deployment Lifecycle

- **Purpose**: Verify complete flow from deployment creation to destruction
- **Setup:**
  - Deployment `d1` in pending state
- **Execution Flow:**
  1. `check_pending_deployments([d1])` → Register endpoint
  2. `calculate_desired_replicas([d1])` → Determine target replicas
  3. `scale_deployment([d1])` → Create routes
  4. `check_ready_deployments_that_need_scaling([d1])` → Verify replicas
  5. `destroy_deployment([d1])` → Cleanup
- **Verification:**
  - Each step completes successfully
  - All resources properly created and cleaned up
- **Classification**: `happy-path`
