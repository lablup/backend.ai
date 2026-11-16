# RouteExecutor 테스트 시나리오

## 개요

실제 코드 동작을 바탕으로 `RouteExecutor` 의 테스트 시나리오를 정의한다.

RouteExecutor 는 다음을 처리한다.
1. **route 프로비저닝**: session 을 생성해 route 를 프로비저닝한다
2. **route 종료**: session 을 끝내 route 를 종료한다
3. **실행 중 route 확인**: session 상태를 확인한다
4. **route 헬스 체크**: Valkey health data 로 상태를 분류한다
5. **서비스 디스커버리 동기화**: Prometheus 수집 대상으로 route 를 등록한다
6. **정리 대상 필터링**: 자원 그룹 config 로 정리 대상을 고른다

**소스 파일:** `sokovan/deployment/route/executor.py`

---

## 의존성(mock 대상)

- `deployment_repo: DeploymentRepository`
  - `get_endpoints_by_ids()` → `list[DeploymentInfo]`
  - `update_route_sessions()` → `None`
  - `fetch_session_statuses_by_route_ids()` → `Mapping[UUID, SessionStatus]`
  - `fetch_deployment_context()` → `DeploymentContext`
  - `fetch_route_service_discovery_info()` → `list[RouteDiscoveryData]`
  - `get_scaling_group_cleanup_configs()` → `Mapping[str, CleanupConfig]`
- `scheduling_controller: SchedulingController`
  - `enqueue_session()` → `SessionId`
  - `mark_sessions_for_termination()` → `None`
- `valkey_schedule: ValkeyScheduleClient`
  - `check_route_health_status()` → `Mapping[str, HealthStatus]`
- `service_discovery: ServiceDiscovery`
  - `sync_model_service_routes()` → `None`

---

## 결과 타입

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

## provision_routes 시나리오

### SC-RE-001: route 프로비저닝이 성공한다

- **목적**: session 생성으로 route 를 프로비저닝하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.get_endpoints_by_ids({endpoint_id})`:
    - 반환: `[DeploymentInfo(id=endpoint_id, ...)]`
  - `deployment_repo.fetch_deployment_context(deployment)`:
    - 반환: `DeploymentContext(...)`
  - `scheduling_controller.enqueue_session(spec)`:
    - 반환: `SessionId("session-1")`
  - `deployment_repo.update_route_sessions({route_id: session_id})`:
    - 반환: `None`
- **입력:**
  - `session_id = None` 인 route `r1`
- **실행:** `await executor.provision_routes([route])`
- **검증:**
  - `RouteExecutionResult`:
    - `successes = [r1]`
    - `errors = []`
  - `enqueue_session` 을 호출한다
  - `update_route_sessions` 를 `{r1.id: session-1}` 로 호출한다
- **분류**: `happy-path`

---

### SC-RE-002: session 이 이미 있는 route 는 생략한다

- **목적**: session 이 이미 있는 route 를 생략하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.get_endpoints_by_ids({endpoint_id})`:
    - 반환: `[DeploymentInfo(...)]`
- **입력:**
  - `session_id = SessionId("existing-session")` 인 route `r1`
- **실행:** `await executor.provision_routes([route])`
- **검증:**
  - `successes = [r1]`(성공으로 계산한다)
  - `enqueue_session.assert_not_called()`
  - `update_route_sessions.assert_not_called()`
- **분류**: `edge-case`

---

### SC-RE-003: 엔드포인트를 찾지 못하면 에러를 기록한다

- **목적**: 배포 정보가 없을 때 EndpointNotFound 에러를 기록하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.get_endpoints_by_ids({endpoint_id})`:
    - 반환: `[]`(빈 목록)
- **입력:**
  - `endpoint_id` 가 없는 route `r1`
- **실행:** `await executor.provision_routes([route])`
- **검증:**
  - `successes = []`
  - `errors = [RouteExecutionError(r1, "Failed to provision", "Deployment not found...")]`
- **분류**: `error-case`

---

### SC-RE-004: session 생성 실패를 에러로 기록한다

- **목적**: session 생성이 예외를 발생시킬 때 에러로 기록하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.get_endpoints_by_ids(...)`:
    - 반환: 유효한 배포
  - `scheduling_controller.enqueue_session(...)`:
    - 발생: `Exception("Resource limit exceeded")`
- **입력:**
  - route `r1`
- **실행:** `await executor.provision_routes([route])`
- **검증:**
  - `successes = []`
  - `errors = [RouteExecutionError(r1, "Failed to provision", "Resource limit exceeded")]`
- **분류**: `error-case`

---

### SC-RE-005: 여러 route 중 일부만 성공한다

- **목적**: 일부 route 가 실패해도 나머지가 성공하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.get_endpoints_by_ids(...)`:
    - 반환: 유효한 배포
  - `scheduling_controller.enqueue_session(spec for r1)`:
    - 반환: `SessionId("s1")`
  - `scheduling_controller.enqueue_session(spec for r2)`:
    - 발생: `Exception("Failed")`
- **입력:**
  - route 2개: `r1`, `r2`
- **실행:** `await executor.provision_routes([r1, r2])`
- **검증:**
  - `successes = [r1]`
  - `errors = [RouteExecutionError(r2, ...)]`
  - `update_route_sessions` 를 `{r1.id: s1}` 로 호출한다
- **분류**: `error-case`

---

## terminate_routes 시나리오

### SC-RE-006: route 종료가 성공한다

- **목적**: session 종료로 route 를 종료하는지 확인한다
- **의존성(mock):**
  - `scheduling_controller.mark_sessions_for_termination([session_id])`:
    - 반환: `None`
- **입력:**
  - `session_id = SessionId("s1")` 인 route `r1`
- **실행:** `await executor.terminate_routes([route])`
- **검증:**
  - `RouteExecutionResult`:
    - `successes = [r1]`
    - `errors = []`
  - `mark_sessions_for_termination` 을 `[s1]` 로 호출한다
- **분류**: `happy-path`

---

### SC-RE-007: session 이 없는 route 는 생략한다

- **목적**: session 이 없는 route 를 생략하는지 확인한다
- **입력:**
  - `session_id = None` 인 route `r1`
- **실행:** `await executor.terminate_routes([route])`
- **검증:**
  - `successes = [r1]`(모든 입력을 성공으로 반환한다)
  - `mark_sessions_for_termination` 을 빈 목록으로 호출하거나 호출하지 않는다
- **분류**: `edge-case`

---

### SC-RE-008: 여러 route 를 한 번에 종료한다

- **목적**: 여러 session 을 한 번에 종료하는지 확인한다
- **의존성(mock):**
  - `scheduling_controller.mark_sessions_for_termination([s1, s2, s3])`:
    - 반환: `None`
- **입력:**
  - session 을 하나씩 가진 route 3개
- **실행:** `await executor.terminate_routes([r1, r2, r3])`
- **검증:**
  - `successes = [r1, r2, r3]`
  - `mark_sessions_for_termination` 을 session id 3개로 호출한다
- **분류**: `happy-path`

---

## check_running_routes 시나리오

### SC-RE-009: 실행 중 session 확인이 성공한다

- **목적**: session 이 유효한 상태일 때 성공하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_session_statuses_by_route_ids({r1.id})`:
    - 반환: `{r1.id: SessionStatus.RUNNING}`
- **입력:**
  - route `r1`
- **실행:** `await executor.check_running_routes([route])`
- **검증:**
  - `successes = [r1]`
  - `errors = []`
- **분류**: `happy-path`

---

### SC-RE-010: session 을 찾지 못하면 RouteSessionNotFound 에러를 기록한다

- **목적**: session 을 찾지 못할 때 에러를 기록하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_session_statuses_by_route_ids({r1.id})`:
    - 반환: `{}`(빈 map)
- **입력:**
  - route `r1`
- **실행:** `await executor.check_running_routes([route])`
- **검증:**
  - `successes = []`
  - `errors = [RouteExecutionError(r1, "RouteSessionNotFound", ...)]`
- **분류**: `error-case`

---

### SC-RE-011: session 이 종료되었으면 RouteSessionTerminated 에러를 기록한다

- **목적**: session 이 종료된 상태일 때 에러를 기록하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_session_statuses_by_route_ids({r1.id})`:
    - 반환: `{r1.id: SessionStatus.TERMINATED}`
- **입력:**
  - route `r1`
- **실행:** `await executor.check_running_routes([route])`
- **검증:**
  - `successes = []`
  - `errors = [RouteExecutionError(r1, "RouteSessionTerminated", ...)]`
- **분류**: `error-case`

---

## check_route_health 시나리오

### SC-RE-012: 정상 route 는 성공한다

- **목적**: Valkey 가 HEALTHY 상태를 반환할 때 성공하는지 확인한다
- **의존성(mock):**
  - `valkey_schedule.check_route_health_status([str(r1.id)])`:
    - 반환: `{str(r1.id): HealthStatus(status=HEALTHY)}`
- **입력:**
  - route `r1`
- **실행:** `await executor.check_route_health([route])`
- **검증:**
  - `successes = [r1]`
  - `errors = []`
  - `stale = []`
- **분류**: `happy-path`

---

### SC-RE-013: 비정상 route 는 에러를 기록한다

- **목적**: Valkey 가 UNHEALTHY 상태를 반환할 때 에러를 기록하는지 확인한다
- **의존성(mock):**
  - `valkey_schedule.check_route_health_status([str(r1.id)])`:
    - 반환: `{str(r1.id): HealthStatus(status=UNHEALTHY)}`
- **입력:**
  - route `r1`
- **실행:** `await executor.check_route_health([route])`
- **검증:**
  - `successes = []`
  - `errors = [RouteExecutionError(r1, "RouteUnhealthy", ...)]`
  - `stale = []`
- **분류**: `error-case`

---

### SC-RE-014: stale route 는 stale 목록에 추가한다

- **목적**: Valkey 가 STALE 상태를 반환할 때 route 를 stale 목록에 추가하는지 확인한다
- **의존성(mock):**
  - `valkey_schedule.check_route_health_status([str(r1.id)])`:
    - 반환: `{str(r1.id): HealthStatus(status=STALE)}`
- **입력:**
  - route `r1`
- **실행:** `await executor.check_route_health([route])`
- **검증:**
  - `successes = []`
  - `errors = []`
  - `stale = [r1]`
- **분류**: `edge-case`

---

### SC-RE-015: health data 가 없으면 stale 로 처리한다

- **목적**: Valkey 에 data 가 없을 때 route 를 stale 로 처리하는지 확인한다
- **의존성(mock):**
  - `valkey_schedule.check_route_health_status([str(r1.id)])`:
    - 반환: `{}`(빈 map)
- **입력:**
  - route `r1`
- **실행:** `await executor.check_route_health([route])`
- **검증:**
  - `successes = []`
  - `errors = []`
  - `stale = [r1]`
- **분류**: `edge-case`

---

### SC-RE-016: 결과가 섞여 있으면 상태별로 분류한다

- **목적**: 여러 route 를 상태별로 올바르게 분류하는지 확인한다
- **의존성(mock):**
  - `valkey_schedule.check_route_health_status(...)`:
    - 반환: `{r1: HEALTHY, r2: UNHEALTHY, r3: STALE}`
- **입력:**
  - route 3개: `r1`, `r2`, `r3`
- **실행:** `await executor.check_route_health([r1, r2, r3])`
- **검증:**
  - `successes = [r1]`
  - `errors = [RouteExecutionError(r2, ...)]`
  - `stale = [r3]`
- **분류**: `happy-path`

---

## sync_service_discovery 시나리오

### SC-RE-017: 서비스 디스커버리 동기화가 성공한다

- **목적**: 정상 route 를 서비스 디스커버리에 등록하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_route_service_discovery_info({r1.id})`:
    - 반환: `[RouteDiscoveryData(route_id=r1.id, host="192.168.1.1", port=8080, ...)]`
  - `service_discovery.sync_model_service_routes(metadata_list)`:
    - 반환: `None`
- **입력:**
  - `session_id` 를 가진 route `r1`
- **실행:** `await executor.sync_service_discovery([route])`
- **검증:**
  - `RouteExecutionResult`:
    - `successes = []`(빈 결과를 반환한다)
    - `errors = []`
  - `ModelServiceMetadata` 를 인자로 `sync_model_service_routes` 를 호출한다
- **분류**: `happy-path`

---

### SC-RE-018: session 이 없는 route 는 생략한다

- **목적**: session 이 없는 route 를 서비스 디스커버리에서 제외하는지 확인한다
- **입력:**
  - `session_id = None` 인 route `r1`
- **실행:** `await executor.sync_service_discovery([route])`
- **검증:**
  - `successes = []`
  - `errors = []`
  - `fetch_route_service_discovery_info.assert_not_called()`
  - `sync_model_service_routes.assert_not_called()`
- **분류**: `edge-case`

---

## cleanup_routes_by_config 시나리오

### SC-RE-019: 정리 대상 route 를 필터링한다

- **목적**: 자원 그룹 config 로 정리 대상을 고르는지 확인한다
- **의존성(mock):**
  - `deployment_repo.get_endpoints_by_ids({endpoint_id})`:
    - 반환: `[DeploymentInfo(resource_group="sg1", ...)]`
  - `deployment_repo.get_scaling_group_cleanup_configs(["sg1"])`:
    - 반환: `{"sg1": CleanupConfig(cleanup_target_statuses=[UNHEALTHY, DEGRADED])}`
- **입력:**
  - `status = RouteStatus.UNHEALTHY` 인 route `r1`
- **실행:** `await executor.cleanup_routes_by_config([route])`
- **검증:**
  - `successes = [r1]`(정리 대상)
- **분류**: `happy-path`

---

### SC-RE-020: 정리 대상이 아닌 route

- **목적**: 정리 대상 상태가 아닌 route 를 제외하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.get_endpoints_by_ids({endpoint_id})`:
    - 반환: `[DeploymentInfo(resource_group="sg1", ...)]`
  - `deployment_repo.get_scaling_group_cleanup_configs(["sg1"])`:
    - 반환: `{"sg1": CleanupConfig(cleanup_target_statuses=[UNHEALTHY])}`
- **입력:**
  - `status = RouteStatus.HEALTHY` 인 route `r1`
- **실행:** `await executor.cleanup_routes_by_config([route])`
- **검증:**
  - `successes = []`(정리 대상이 아니다)
- **분류**: `edge-case`

---

### SC-RE-021: 정리 config 가 없으면 모두 제외한다

- **목적**: 정리 config 가 없을 때 모든 route 를 제외하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.get_endpoints_by_ids({endpoint_id})`:
    - 반환: `[DeploymentInfo(resource_group="sg1", ...)]`
  - `deployment_repo.get_scaling_group_cleanup_configs(["sg1"])`:
    - 반환: `{}`(빈 config)
- **입력:**
  - route `r1`
- **실행:** `await executor.cleanup_routes_by_config([route])`
- **검증:**
  - `successes = []`(정리 대상이 없다)
- **분류**: `edge-case`

---

## 빈 입력 시나리오

### SC-RE-022: 빈 route 목록은 즉시 반환한다

- **목적**: 빈 입력이면 즉시 반환하는지 확인한다
- **입력:**
  - `routes = []`
- **실행(모든 method):**
  - `await executor.provision_routes([])`
  - `await executor.terminate_routes([])`
  - `await executor.check_running_routes([])`
  - `await executor.check_route_health([])`
  - `await executor.sync_service_discovery([])`
  - `await executor.cleanup_routes_by_config([])`
- **검증:**
  - 모든 경우: `RouteExecutionResult(successes=[], errors=[], stale=[])`
  - repository 와 controller 호출을 최소화한다
- **분류**: `edge-case`

---

## 통합 시나리오

### SC-RE-INT-001: route 전체 수명 주기

- **목적**: route 생성부터 종료까지 전체 흐름을 확인한다
- **준비:**
  - 프로비저닝을 기다리는 route `r1`
- **실행 흐름:**
  1. `provision_routes([r1])` → session 을 생성하고 연결한다
  2. `check_running_routes([r1])` → session 상태를 확인한다
  3. `check_route_health([r1])` → 헬스 체크(HEALTHY 로 가정)
  4. `sync_service_discovery([r1])` → 서비스 디스커버리에 등록한다
  5. (시간이 지나 UNHEALTHY 를 감지한다)
  6. `check_route_health([r1])` → 헬스 체크(UNHEALTHY)
  7. `cleanup_routes_by_config([r1])` → 정리 대상을 고른다
  8. `terminate_routes([r1])` → session 을 종료한다
- **검증:**
  - 각 단계가 알맞은 결과를 반환한다
  - route 가 최종적으로 종료된다
- **분류**: `happy-path`

---

### SC-RE-INT-002: 헬스 체크 기반 자동 복구 흐름

- **목적**: 헬스 체크 실패 뒤 자동 복구 흐름을 확인한다
- **준비:**
  - UNHEALTHY 상태의 route `r1`
- **실행 흐름:**
  1. `check_route_health([r1])` → r1 이 errors 에 추가된다
  2. `cleanup_routes_by_config([r1])` → 정리 대상임을 확인한다
  3. `terminate_routes([r1])` → 기존 session 을 종료한다
  4. (새 route 생성은 상위 handler 가 처리한다)
- **검증:**
  - UNHEALTHY route 를 올바르게 종료한다
  - 새 route 를 생성할 수 있는 상태가 된다
- **분류**: `happy-path`
