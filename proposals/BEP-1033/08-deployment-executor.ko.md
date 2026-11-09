# DeploymentExecutor 테스트 시나리오

## 개요

실제 코드 동작을 바탕으로 `DeploymentExecutor` 의 테스트 시나리오를 정의한다.

DeploymentExecutor 는 다음을 처리한다.
1. **대기 배포 확인**: proxy 에 엔드포인트를 등록한다
2. **스케일링 필요 여부 확인**: 복제본 수를 확인한다
3. **배포 스케일링**: route 를 늘리거나 줄인다
4. **목표 복제본 수 계산**: 오토스케일링 복제본 수를 계산한다
5. **배포 종료**: route 를 종료하고 엔드포인트 등록을 해제한다

**소스 파일:** `sokovan/deployment/executor.py`

---

## 의존성(mock 대상)

- `deployment_repo: DeploymentRepository`
  - `fetch_scaling_group_proxy_targets()` → `Mapping[str, ScalingGroupProxyTarget]`
  - `update_endpoint_urls_bulk()` → `None`
  - `fetch_active_routes_by_endpoint_ids()` → `Mapping[UUID, Sequence[RouteData]]`
  - `scale_routes()` → `None`
  - `fetch_auto_scaling_rules_by_endpoint_ids()` → `Mapping[UUID, Sequence[AutoScalingRule]]`
  - `fetch_metrics_for_autoscaling()` → `AutoScalingMetricsData`
  - `update_desired_replicas_bulk()` → `None`
  - `calculate_desired_replicas_for_deployment()` → `Optional[int]`
  - `mark_terminating_route_status_bulk()` → `None`
- `client_pool: ClientPool`
  - `load_client_session()` → `ClientSession`
- `AppProxyClient` (내부에서 생성한다)
  - `create_endpoint()` → `"endpoint"` key 를 가진 `dict`
  - `delete_endpoint()` → `None`

---

## 결과 타입

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

## check_pending_deployments 시나리오

### SC-DE-001: 모든 배포의 엔드포인트 등록이 성공한다

- **목적**: 모든 배포에서 엔드포인트를 proxy 에 등록하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_scaling_group_proxy_targets({"sg1"})`:
    - 반환: `{"sg1": ScalingGroupProxyTarget(addr="proxy:8080", api_token="token")}`
  - `AppProxyClient.create_endpoint(d1.id, request_body)`:
    - 반환: `{"endpoint": "https://endpoint1.example.com"}`
  - `deployment_repo.update_endpoint_urls_bulk({d1.id: "https://endpoint1.example.com"})`:
    - 반환: `None`
- **입력:**
  - target_revision(resource_group="sg1") 을 가진 배포 `d1`
- **실행:** `await executor.check_pending_deployments([deployment])`
- **검증:**
  - `DeploymentExecutionResult`:
    - `successes = [d1]`
    - `errors = []`
  - `create_endpoint` 를 호출한다
  - `update_endpoint_urls_bulk` 를 호출한다
- **분류**: `happy-path`

---

### SC-DE-002: target_revision 이 없는 배포는 생략한다

- **목적**: target_revision 이 없는 배포를 생략하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_scaling_group_proxy_targets()`:
    - 반환: `{"sg1": ScalingGroupProxyTarget(...)}`
- **입력:**
  - `target_revision = None` 인 배포 `d1`
- **실행:** `await executor.check_pending_deployments([deployment])`
- **검증:**
  - `DeploymentExecutionResult`:
    - `successes = []`
    - `errors = []`
  - warning 을 기록한다
  - `create_endpoint.assert_not_called()`
- **분류**: `edge-case`

---

### SC-DE-003: proxy target 이 없는 자원 그룹의 배포는 생략한다

- **목적**: proxy target 이 없는 자원 그룹에 속한 배포를 생략하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_scaling_group_proxy_targets({"sg1"})`:
    - 반환: `{"sg1": None}` 또는 `{}`
- **입력:**
  - `resource_group = "sg1"` 인 배포
- **실행:** `await executor.check_pending_deployments([deployment])`
- **검증:**
  - `successes = []`
  - `errors = []`
  - warning 을 기록한다
- **분류**: `edge-case`

---

### SC-DE-004: 엔드포인트 등록 실패를 에러로 기록한다

- **목적**: proxy 등록 실패를 에러로 기록하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_scaling_group_proxy_targets()`:
    - 반환: 유효한 proxy target
  - `AppProxyClient.create_endpoint()`:
    - 발생: `Exception("Connection refused")`
- **입력:**
  - 유효한 배포 `d1`
- **실행:** `await executor.check_pending_deployments([deployment])`
- **검증:**
  - `DeploymentExecutionResult`:
    - `successes = []`
    - `errors = [DeploymentExecutionError(d1, "Connection refused", "Failed to register endpoint")]`
- **분류**: `error-case`

---

### SC-DE-005: 일부 성공: 일부 배포가 실패한다

- **목적**: 일부 배포가 실패해도 성공한 배포는 계속 처리하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_scaling_group_proxy_targets()`:
    - 반환: 유효한 proxy target
  - `AppProxyClient.create_endpoint(d1.id, ...)`:
    - 반환: `{"endpoint": "https://endpoint1.example.com"}`
  - `AppProxyClient.create_endpoint(d2.id, ...)`:
    - 발생: `Exception("Timeout")`
- **입력:**
  - 배포 2개: `d1`, `d2`
- **실행:** `await executor.check_pending_deployments([d1, d2])`
- **검증:**
  - `successes = [d1]`
  - `errors = [DeploymentExecutionError(d2, ...)]`
  - `update_endpoint_urls_bulk` 를 d1 에만 호출한다
- **분류**: `error-case`

---

## check_ready_deployments_that_need_scaling 시나리오

### SC-DE-006: 복제본 수가 일치하면 성공한다

- **목적**: 실제 route 수가 목표 복제본 수와 같을 때 성공하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_active_routes_by_endpoint_ids({d1.id})`:
    - 반환: `{d1.id: [route1, route2, route3]}`
- **입력:**
  - `target_replica_count = 3` 인 배포 `d1`
- **실행:** `await executor.check_ready_deployments_that_need_scaling([d1])`
- **검증:**
  - `successes = [d1]`
  - `errors = []`
- **분류**: `happy-path`

---

### SC-DE-007: 복제본 수가 다르면 에러를 기록한다

- **목적**: route 수가 목표와 다를 때 ReplicaCountMismatch 에러를 기록하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_active_routes_by_endpoint_ids({d1.id})`:
    - 반환: `{d1.id: [route1, route2]}`(2개뿐이다)
- **입력:**
  - `target_replica_count = 3` 인 배포 `d1`
- **실행:** `await executor.check_ready_deployments_that_need_scaling([d1])`
- **검증:**
  - `successes = []`
  - `errors = [DeploymentExecutionError(d1, "Mismatched active routes", ...)]`
- **분류**: `error-case`

---

## scale_deployment 시나리오

### SC-DE-008: 스케일 아웃: route 를 생성한다

- **목적**: 목표 복제본 수가 현재보다 클 때 새 route 를 생성하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_active_routes_by_endpoint_ids({d1.id})`:
    - 반환: `{d1.id: [route1]}`(1개)
  - `deployment_repo.scale_routes(creators, None)`:
    - 반환: `None`
- **입력:**
  - `target_replica_count = 3` 인 배포 `d1`
- **실행:** `await executor.scale_deployment([d1])`
- **검증:**
  - `successes = [d1]`
  - Creator 2개로 `scale_routes` 를 호출한다
- **분류**: `happy-path`

---

### SC-DE-009: 스케일 인: route 를 종료한다

- **목적**: 목표 복제본 수가 현재보다 작을 때 route 를 종료하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_active_routes_by_endpoint_ids({d1.id})`:
    - 반환: `{d1.id: [route1, route2, route3, route4]}`(4개)
  - `deployment_repo.scale_routes([], updater)`:
    - 반환: `None`
- **입력:**
  - `target_replica_count = 2` 인 배포 `d1`
- **실행:** `await executor.scale_deployment([d1])`
- **검증:**
  - `successes = [d1]`
  - route id 2개를 담은 BatchUpdater 로 `scale_routes` 를 호출한다
  - updater 상태는 `TERMINATING` 이다
- **분류**: `happy-path`

---

### SC-DE-010: 스케일링이 필요 없으면 생략한다

- **목적**: 목표 복제본 수가 현재와 같을 때 배포를 생략하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_active_routes_by_endpoint_ids({d1.id})`:
    - 반환: `{d1.id: [route1, route2]}`(2개)
- **입력:**
  - `target_replica_count = 2` 인 배포 `d1`
- **실행:** `await executor.scale_deployment([d1])`
- **검증:**
  - `successes = []`
  - `skipped = [d1]`
  - `scale_routes.assert_not_called()`
- **분류**: `edge-case`

---

## calculate_desired_replicas 시나리오

### SC-DE-011: 오토스케일링 규칙으로 복제본 수를 계산한다

- **목적**: 오토스케일링 규칙으로 목표 복제본 수를 계산하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_auto_scaling_rules_by_endpoint_ids({d1.id})`:
    - 반환: `{d1.id: [AutoScalingRule(...)]}`
  - `deployment_repo.fetch_metrics_for_autoscaling(...)`:
    - 반환: `AutoScalingMetricsData(...)`
  - `deployment_repo.calculate_desired_replicas_for_deployment(d1, rules, metrics)`:
    - 반환: `5`
  - `deployment_repo.update_desired_replicas_bulk({d1.id: 5})`:
    - 반환: `None`
- **입력:**
  - 오토스케일링을 구성한 배포 `d1`
- **실행:** `await executor.calculate_desired_replicas([d1])`
- **검증:**
  - `successes = [d1]`
  - `update_desired_replicas_bulk` 를 `{d1.id: 5}` 로 호출한다
- **분류**: `happy-path`

---

### SC-DE-012: 오토스케일링 규칙이 없으면 수동 복제본 수를 사용한다

- **목적**: 오토스케일링 규칙이 없을 때 수동 `replica_count` 를 사용하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_auto_scaling_rules_by_endpoint_ids({d1.id})`:
    - 반환: `{d1.id: []}`(규칙이 없다)
  - `deployment_repo.fetch_metrics_for_autoscaling(...)`:
    - 반환: `AutoScalingMetricsData(routes_by_endpoint={d1.id: [route1]})`
- **입력:**
  - `replica_count = 3` 인 배포 `d1`(현재 route 1개)
- **실행:** `await executor.calculate_desired_replicas([d1])`
- **검증:**
  - `successes = [d1]`
  - `update_desired_replicas_bulk` 를 `{d1.id: 3}` 으로 호출한다
- **분류**: `happy-path`

---

### SC-DE-013: 변경이 필요 없으면 생략한다

- **목적**: 오토스케일링 결과가 None 일 때 생략하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_auto_scaling_rules_by_endpoint_ids({d1.id})`:
    - 반환: `{d1.id: [AutoScalingRule(...)]}`
  - `deployment_repo.calculate_desired_replicas_for_deployment(...)`:
    - 반환: `None`(변경 없음)
- **입력:**
  - 배포 `d1`
- **실행:** `await executor.calculate_desired_replicas([d1])`
- **검증:**
  - `successes = []`
  - `skipped = [d1]`
  - `update_desired_replicas_bulk.assert_not_called()`
- **분류**: `edge-case`

---

### SC-DE-014: 복제본 수 계산 실패를 에러로 기록한다

- **목적**: 복제본 수 계산이 예외를 발생시킬 때 에러로 기록하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_auto_scaling_rules_by_endpoint_ids(...)`:
    - 반환: 유효한 규칙
  - `deployment_repo.calculate_desired_replicas_for_deployment(...)`:
    - 발생: `Exception("Metrics unavailable")`
- **입력:**
  - 배포 `d1`
- **실행:** `await executor.calculate_desired_replicas([d1])`
- **검증:**
  - `successes = []`
  - `errors = [DeploymentExecutionError(d1, "Metrics unavailable", "Failed to calculate desired replicas")]`
- **분류**: `error-case`

---

## destroy_deployment 시나리오

### SC-DE-015: 배포 종료가 성공한다

- **목적**: 모든 route 를 종료하고 엔드포인트 등록을 해제하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_active_routes_by_endpoint_ids({d1.id})`:
    - 반환: `{d1.id: [route1, route2]}`
  - `deployment_repo.fetch_scaling_group_proxy_targets({"sg1"})`:
    - 반환: `{"sg1": ScalingGroupProxyTarget(...)}`
  - `deployment_repo.mark_terminating_route_status_bulk({route1.id, route2.id})`:
    - 반환: `None`
  - `AppProxyClient.delete_endpoint(d1.id)`:
    - 반환: `None`
- **입력:**
  - route 2개를 가진 배포 `d1`
- **실행:** `await executor.destroy_deployment([d1])`
- **검증:**
  - `successes = [d1]`
  - `mark_terminating_route_status_bulk` 를 route id 와 함께 호출한다
  - `delete_endpoint` 를 호출한다
- **분류**: `happy-path`

---

### SC-DE-016: 엔드포인트 삭제 실패를 에러로 기록한다

- **목적**: 엔드포인트 삭제 실패를 에러로 기록하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_active_routes_by_endpoint_ids(...)`:
    - 반환: 유효한 route
  - `deployment_repo.fetch_scaling_group_proxy_targets(...)`:
    - 반환: 유효한 proxy target
  - `deployment_repo.mark_terminating_route_status_bulk(...)`:
    - 반환: `None`
  - `AppProxyClient.delete_endpoint(d1.id)`:
    - 발생: `Exception("Endpoint not found")`
- **입력:**
  - 배포 `d1`
- **실행:** `await executor.destroy_deployment([d1])`
- **검증:**
  - `successes = []`
  - `errors = [DeploymentExecutionError(d1, "Failed to unregister endpoint", ...)]`
  - route 상태는 이미 `TERMINATING` 이다
- **분류**: `error-case`

---

### SC-DE-017: proxy target 이 없으면 기록하고 계속한다

- **목적**: proxy target 이 없어도 배포 종료가 성공하는지 확인한다
- **의존성(mock):**
  - `deployment_repo.fetch_active_routes_by_endpoint_ids(...)`:
    - 반환: 유효한 route
  - `deployment_repo.fetch_scaling_group_proxy_targets({"sg1"})`:
    - 반환: `{"sg1": None}`
  - `deployment_repo.mark_terminating_route_status_bulk(...)`:
    - 반환: `None`
- **입력:**
  - 배포 `d1`
- **실행:** `await executor.destroy_deployment([d1])`
- **검증:**
  - `successes = [d1]`
  - warning 을 기록한다
  - `delete_endpoint.assert_not_called()`
- **분류**: `edge-case`

---

## 빈 입력 시나리오

### SC-DE-018: 빈 배포 목록은 즉시 반환한다

- **목적**: 빈 입력이면 즉시 반환하는지 확인한다
- **입력:**
  - `deployments = []`
- **실행(모든 method):**
  - `await executor.check_pending_deployments([])`
  - `await executor.check_ready_deployments_that_need_scaling([])`
  - `await executor.scale_deployment([])`
  - `await executor.calculate_desired_replicas([])`
  - `await executor.destroy_deployment([])`
- **검증:**
  - 모든 경우: `DeploymentExecutionResult(successes=[], errors=[], skipped=[])`
  - repository 호출을 최소화한다
- **분류**: `edge-case`

---

## 통합 시나리오

### SC-DE-INT-001: 배포 전체 수명 주기

- **목적**: 배포 생성부터 종료까지 전체 흐름을 확인한다
- **준비:**
  - pending 상태의 배포 `d1`
- **실행 흐름:**
  1. `check_pending_deployments([d1])` → 엔드포인트를 등록한다
  2. `calculate_desired_replicas([d1])` → 목표 복제본 수를 계산한다
  3. `scale_deployment([d1])` → route 를 생성한다
  4. `check_ready_deployments_that_need_scaling([d1])` → 복제본 수를 확인한다
  5. `destroy_deployment([d1])` → 정리한다
- **검증:**
  - 각 단계가 성공한다
  - 모든 자원을 올바르게 생성하고 정리한다
- **분류**: `happy-path`
