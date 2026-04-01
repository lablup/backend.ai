# RouteExecutor Test Scenarios

## Overview

Test scenarios for `RouteExecutor` based on actual code behavior.

The RouteExecutor handles:
1. **Route Provisioning**: Provision routes by creating sessions
2. **Route Termination**: Terminate routes by ending sessions
3. **Check Running Routes**: Verify session status
4. **Route Health Check**: Classify status based on Redis health data
5. **Service Discovery Sync**: Register routes for Prometheus scraping
6. **Cleanup Target Filtering**: Select cleanup targets based on scaling group config

**Source Files:** `sokovan/deployment/route/executor.py`

---

## Dependencies (Mock Targets)

- `deployment_repo: DeploymentRepository`
  - `get_endpoints_by_ids()` -> `list[DeploymentInfo]`
  - `update_route_sessions()` -> `None`
  - `fetch_session_statuses_by_route_ids()` -> `Mapping[UUID, SessionStatus]`
  - `fetch_deployment_context()` -> `DeploymentContext`
  - `fetch_route_service_discovery_info()` -> `list[RouteDiscoveryData]`
  - `get_scaling_group_cleanup_configs()` -> `Mapping[str, CleanupConfig]`
- `scheduling_controller: SchedulingController`
  - `enqueue_session()` -> `SessionId`
  - `mark_sessions_for_termination()` -> `None`
- `valkey_schedule: ValkeyScheduleClient`
  - `check_route_health_status()` -> `Mapping[str, HealthStatus]`
- `service_discovery: ServiceDiscovery`
  - `sync_model_service_routes()` -> `None`

---

## Result Types

```python
@dataclass
class RouteExecutionResult:
    successes: list[RouteData]
    errors: list[RouteExecutionError]
    stale: list[RouteData]  # Degraded status from health check

@dataclass
class RouteExecutionError:
    route_info: RouteData
    reason: str
    error_detail: str
```

---

## provision_routes Scenarios

### SC-RE-001: Route Provisioning Success

- **Purpose**: Verify route provisioning via session creation
- **Dependencies (Mock):**
  - `deployment_repo.get_endpoints_by_ids({endpoint_id})`:
    - Returns: `[DeploymentInfo(id=endpoint_id, ...)]`
  - `deployment_repo.fetch_deployment_context(deployment)`:
    - Returns: `DeploymentContext(...)`
  - `scheduling_controller.enqueue_session(spec)`:
    - Returns: `SessionId("session-1")`
  - `deployment_repo.update_route_sessions({route_id: session_id})`:
    - Returns: `None`
- **Input:**
  - Route `r1` with `session_id = None`
- **Execution:** `await executor.provision_routes([route])`
- **Verification:**
  - `RouteExecutionResult`:
    - `successes = [r1]`
    - `errors = []`
  - `enqueue_session` called
  - `update_route_sessions` called with `{r1.id: session-1}`
- **Classification**: `happy-path`

---

### SC-RE-002: Route with Existing Session Skipped

- **Purpose**: Verify routes with existing sessions are ignored
- **Dependencies (Mock):**
  - `deployment_repo.get_endpoints_by_ids({endpoint_id})`:
    - Returns: `[DeploymentInfo(...)]`
- **Input:**
  - Route `r1` with `session_id = SessionId("existing-session")`
- **Execution:** `await executor.provision_routes([route])`
- **Verification:**
  - `successes = [r1]` (counted as success)
  - `enqueue_session.assert_not_called()`
  - `update_route_sessions.assert_not_called()`
- **Classification**: `edge-case`

---

### SC-RE-003: Endpoint Not Found - Error

- **Purpose**: Verify EndpointNotFound error when deployment info missing
- **Dependencies (Mock):**
  - `deployment_repo.get_endpoints_by_ids({endpoint_id})`:
    - Returns: `[]` (empty list)
- **Input:**
  - Route `r1` with missing `endpoint_id`
- **Execution:** `await executor.provision_routes([route])`
- **Verification:**
  - `successes = []`
  - `errors = [RouteExecutionError(r1, "Failed to provision", "Deployment not found...")]`
- **Classification**: `error-case`

---

### SC-RE-004: Session Creation Failure - Error Captured

- **Purpose**: Verify error captured when session creation throws exception
- **Dependencies (Mock):**
  - `deployment_repo.get_endpoints_by_ids(...)`:
    - Returns: Valid deployment
  - `scheduling_controller.enqueue_session(...)`:
    - Raises: `Exception("Resource limit exceeded")`
- **Input:**
  - Route `r1`
- **Execution:** `await executor.provision_routes([route])`
- **Verification:**
  - `successes = []`
  - `errors = [RouteExecutionError(r1, "Failed to provision", "Resource limit exceeded")]`
- **Classification**: `error-case`

---

### SC-RE-005: Partial Success Among Multiple Routes

- **Purpose**: Verify some routes succeed when others fail
- **Dependencies (Mock):**
  - `deployment_repo.get_endpoints_by_ids(...)`:
    - Returns: Valid deployment
  - `scheduling_controller.enqueue_session(spec for r1)`:
    - Returns: `SessionId("s1")`
  - `scheduling_controller.enqueue_session(spec for r2)`:
    - Raises: `Exception("Failed")`
- **Input:**
  - 2 routes: `r1`, `r2`
- **Execution:** `await executor.provision_routes([r1, r2])`
- **Verification:**
  - `successes = [r1]`
  - `errors = [RouteExecutionError(r2, ...)]`
  - `update_route_sessions` called with `{r1.id: s1}`
- **Classification**: `error-case`

---

## terminate_routes Scenarios

### SC-RE-006: Route Termination Success

- **Purpose**: Verify route termination via session termination
- **Dependencies (Mock):**
  - `scheduling_controller.mark_sessions_for_termination([session_id])`:
    - Returns: `None`
- **Input:**
  - Route `r1` with `session_id = SessionId("s1")`
- **Execution:** `await executor.terminate_routes([route])`
- **Verification:**
  - `RouteExecutionResult`:
    - `successes = [r1]`
    - `errors = []`
  - `mark_sessions_for_termination` called with `[s1]`
- **Classification**: `happy-path`

---

### SC-RE-007: Route Without Session Skipped

- **Purpose**: Verify routes without sessions are ignored
- **Input:**
  - Route `r1` with `session_id = None`
- **Execution:** `await executor.terminate_routes([route])`
- **Verification:**
  - `successes = [r1]` (all inputs returned as success)
  - `mark_sessions_for_termination` called with empty list or not called
- **Classification**: `edge-case`

---

### SC-RE-008: Multiple Routes Batch Terminated

- **Purpose**: Verify multiple sessions terminated at once
- **Dependencies (Mock):**
  - `scheduling_controller.mark_sessions_for_termination([s1, s2, s3])`:
    - Returns: `None`
- **Input:**
  - 3 routes each with sessions
- **Execution:** `await executor.terminate_routes([r1, r2, r3])`
- **Verification:**
  - `successes = [r1, r2, r3]`
  - `mark_sessions_for_termination` called with 3 session IDs
- **Classification**: `happy-path`

---

## check_running_routes Scenarios

### SC-RE-009: Running Session Check Success

- **Purpose**: Verify success when session is in valid status
- **Dependencies (Mock):**
  - `deployment_repo.fetch_session_statuses_by_route_ids({r1.id})`:
    - Returns: `{r1.id: SessionStatus.RUNNING}`
- **Input:**
  - Route `r1`
- **Execution:** `await executor.check_running_routes([route])`
- **Verification:**
  - `successes = [r1]`
  - `errors = []`
- **Classification**: `happy-path`

---

### SC-RE-010: Session Not Found - RouteSessionNotFound Error

- **Purpose**: Verify error when session not found
- **Dependencies (Mock):**
  - `deployment_repo.fetch_session_statuses_by_route_ids({r1.id})`:
    - Returns: `{}` (empty map)
- **Input:**
  - Route `r1`
- **Execution:** `await executor.check_running_routes([route])`
- **Verification:**
  - `successes = []`
  - `errors = [RouteExecutionError(r1, "RouteSessionNotFound", ...)]`
- **Classification**: `error-case`

---

### SC-RE-011: Session Terminated - RouteSessionTerminated Error

- **Purpose**: Verify error when session is terminated
- **Dependencies (Mock):**
  - `deployment_repo.fetch_session_statuses_by_route_ids({r1.id})`:
    - Returns: `{r1.id: SessionStatus.TERMINATED}`
- **Input:**
  - Route `r1`
- **Execution:** `await executor.check_running_routes([route])`
- **Verification:**
  - `successes = []`
  - `errors = [RouteExecutionError(r1, "RouteSessionTerminated", ...)]`
- **Classification**: `error-case`

---

## check_route_health Scenarios

### SC-RE-012: Healthy Route - Success

- **Purpose**: Verify success when Redis returns HEALTHY status
- **Dependencies (Mock):**
  - `valkey_schedule.check_route_health_status([str(r1.id)])`:
    - Returns: `{str(r1.id): HealthStatus(status=HEALTHY)}`
- **Input:**
  - Route `r1`
- **Execution:** `await executor.check_route_health([route])`
- **Verification:**
  - `successes = [r1]`
  - `errors = []`
  - `stale = []`
- **Classification**: `happy-path`

---

### SC-RE-013: Unhealthy Route - Error

- **Purpose**: Verify error when Redis returns UNHEALTHY status
- **Dependencies (Mock):**
  - `valkey_schedule.check_route_health_status([str(r1.id)])`:
    - Returns: `{str(r1.id): HealthStatus(status=UNHEALTHY)}`
- **Input:**
  - Route `r1`
- **Execution:** `await executor.check_route_health([route])`
- **Verification:**
  - `successes = []`
  - `errors = [RouteExecutionError(r1, "RouteUnhealthy", ...)]`
  - `stale = []`
- **Classification**: `error-case`

---

### SC-RE-014: Stale Route - Added to Stale List

- **Purpose**: Verify route added to stale list when Redis returns STALE status
- **Dependencies (Mock):**
  - `valkey_schedule.check_route_health_status([str(r1.id)])`:
    - Returns: `{str(r1.id): HealthStatus(status=STALE)}`
- **Input:**
  - Route `r1`
- **Execution:** `await executor.check_route_health([route])`
- **Verification:**
  - `successes = []`
  - `errors = []`
  - `stale = [r1]`
- **Classification**: `edge-case`

---

### SC-RE-015: No Health Data - Treated as Stale

- **Purpose**: Verify route treated as stale when no Redis data exists
- **Dependencies (Mock):**
  - `valkey_schedule.check_route_health_status([str(r1.id)])`:
    - Returns: `{}` (empty map)
- **Input:**
  - Route `r1`
- **Execution:** `await executor.check_route_health([route])`
- **Verification:**
  - `successes = []`
  - `errors = []`
  - `stale = [r1]`
- **Classification**: `edge-case`

---

### SC-RE-016: Mixed Results - Classified to Each Category

- **Purpose**: Verify multiple routes correctly classified to each status
- **Dependencies (Mock):**
  - `valkey_schedule.check_route_health_status(...)`:
    - Returns: `{r1: HEALTHY, r2: UNHEALTHY, r3: STALE}`
- **Input:**
  - 3 routes: `r1`, `r2`, `r3`
- **Execution:** `await executor.check_route_health([r1, r2, r3])`
- **Verification:**
  - `successes = [r1]`
  - `errors = [RouteExecutionError(r2, ...)]`
  - `stale = [r3]`
- **Classification**: `happy-path`

---

## sync_service_discovery Scenarios

### SC-RE-017: Service Discovery Sync Success

- **Purpose**: Verify healthy routes are registered with service discovery
- **Dependencies (Mock):**
  - `deployment_repo.fetch_route_service_discovery_info({r1.id})`:
    - Returns: `[RouteDiscoveryData(route_id=r1.id, host="192.168.1.1", port=8080, ...)]`
  - `service_discovery.sync_model_service_routes(metadata_list)`:
    - Returns: `None`
- **Input:**
  - Route `r1` with `session_id`
- **Execution:** `await executor.sync_service_discovery([route])`
- **Verification:**
  - `RouteExecutionResult`:
    - `successes = []` (empty result returned)
    - `errors = []`
  - `sync_model_service_routes` called with `ModelServiceMetadata`
- **Classification**: `happy-path`

---

### SC-RE-018: Route Without Session Skipped

- **Purpose**: Verify routes without sessions excluded from service discovery
- **Input:**
  - Route `r1` with `session_id = None`
- **Execution:** `await executor.sync_service_discovery([route])`
- **Verification:**
  - `successes = []`
  - `errors = []`
  - `fetch_route_service_discovery_info.assert_not_called()`
  - `sync_model_service_routes.assert_not_called()`
- **Classification**: `edge-case`

---

## cleanup_routes_by_config Scenarios

### SC-RE-019: Cleanup Target Routes Filtered

- **Purpose**: Verify cleanup targets selected based on scaling group config
- **Dependencies (Mock):**
  - `deployment_repo.get_endpoints_by_ids({endpoint_id})`:
    - Returns: `[DeploymentInfo(resource_group="sg1", ...)]`
  - `deployment_repo.get_scaling_group_cleanup_configs(["sg1"])`:
    - Returns: `{"sg1": CleanupConfig(cleanup_target_statuses=[UNHEALTHY, DEGRADED])}`
- **Input:**
  - Route `r1` with `status = RouteStatus.UNHEALTHY`
- **Execution:** `await executor.cleanup_routes_by_config([route])`
- **Verification:**
  - `successes = [r1]` (cleanup target)
- **Classification**: `happy-path`

---

### SC-RE-020: Route Not Cleanup Target

- **Purpose**: Verify routes not in cleanup target status are excluded
- **Dependencies (Mock):**
  - `deployment_repo.get_endpoints_by_ids({endpoint_id})`:
    - Returns: `[DeploymentInfo(resource_group="sg1", ...)]`
  - `deployment_repo.get_scaling_group_cleanup_configs(["sg1"])`:
    - Returns: `{"sg1": CleanupConfig(cleanup_target_statuses=[UNHEALTHY])}`
- **Input:**
  - Route `r1` with `status = RouteStatus.HEALTHY`
- **Execution:** `await executor.cleanup_routes_by_config([route])`
- **Verification:**
  - `successes = []` (not cleanup target)
- **Classification**: `edge-case`

---

### SC-RE-021: No Cleanup Config - All Excluded

- **Purpose**: Verify all routes excluded when no cleanup config exists
- **Dependencies (Mock):**
  - `deployment_repo.get_endpoints_by_ids({endpoint_id})`:
    - Returns: `[DeploymentInfo(resource_group="sg1", ...)]`
  - `deployment_repo.get_scaling_group_cleanup_configs(["sg1"])`:
    - Returns: `{}` (empty config)
- **Input:**
  - Route `r1`
- **Execution:** `await executor.cleanup_routes_by_config([route])`
- **Verification:**
  - `successes = []` (no cleanup targets)
- **Classification**: `edge-case`

---

## Empty Input Scenarios

### SC-RE-022: Empty Route List - Immediate Return

- **Purpose**: Verify early return for empty input
- **Input:**
  - `routes = []`
- **Execution (all methods):**
  - `await executor.provision_routes([])`
  - `await executor.terminate_routes([])`
  - `await executor.check_running_routes([])`
  - `await executor.check_route_health([])`
  - `await executor.sync_service_discovery([])`
  - `await executor.cleanup_routes_by_config([])`
- **Verification:**
  - All cases: `RouteExecutionResult(successes=[], errors=[], stale=[])`
  - Minimal repository/controller calls
- **Classification**: `edge-case`

---

## Integration Scenarios

### SC-RE-INT-001: Full Route Lifecycle

- **Purpose**: Verify complete flow from route creation to termination
- **Setup:**
  - Route `r1` pending provisioning
- **Execution Flow:**
  1. `provision_routes([r1])` → Create and link session
  2. `check_running_routes([r1])` → Verify session status
  3. `check_route_health([r1])` → Health check (assume HEALTHY)
  4. `sync_service_discovery([r1])` → Register with service discovery
  5. (Time passes, UNHEALTHY detected)
  6. `check_route_health([r1])` → Health check (UNHEALTHY)
  7. `cleanup_routes_by_config([r1])` → Select cleanup target
  8. `terminate_routes([r1])` → Terminate session
- **Verification:**
  - Each step returns appropriate result
  - Route ultimately terminated
- **Classification**: `happy-path`

---

### SC-RE-INT-002: Health Check Based Auto-Recovery Flow

- **Purpose**: Verify auto-recovery flow after health check failure
- **Setup:**
  - Route `r1` in UNHEALTHY state
- **Execution Flow:**
  1. `check_route_health([r1])` → r1 in errors
  2. `cleanup_routes_by_config([r1])` → Confirm cleanup target
  3. `terminate_routes([r1])` → Terminate existing session
  4. (New route creation handled by upper handler)
- **Verification:**
  - UNHEALTHY route properly terminated
  - Ready for new route creation
- **Classification**: `happy-path`
