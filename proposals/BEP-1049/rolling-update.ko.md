# 롤링 업데이트 배포 전략

- 상위 문서: [BEP-1049: 무중단 배포 전략 아키텍처](../BEP-1049-deployment-strategy-handler.md)
- 관련 문서: [블루그린 배포 전략](./blue-green.md)

## 개요

롤링 업데이트는 기존 라우트(Old Revision)를 새 라우트(New Revision)로 **점진적으로** 교체하는 배포 전략이다. `max_surge` 와 `max_unavailable` 두 파라미터가 교체 속도를 제어하고, 교체가 완전히 끝날 때까지 배포는 여러 cycle 에 걸쳐 `DEPLOYING` 상태에 머문다.

### 설정

```
RollingUpdateSpec:
  max_surge: int = 1           # Max additional routes to create simultaneously beyond desired_replicas
  max_unavailable: int = 0     # Max unavailable routes to allow relative to desired_replicas
```

## 리비전 추적

`endpoints` 테이블에는 리비전 관리를 위한 column 이 둘 있다:

- `deploying_revision`: 현재 배포 중인 리비전이다. 진행 중인 배포가 없으면 NULL 이다
- `current_revision`: 현재 트래픽을 서비스하는 리비전이다

## cycle FSM

`DeploymentStrategyEvaluator` 는 롤링 업데이트 배포를 주기적으로 평가한다. 호출마다 다음 FSM 을 따른다:

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

롤백은 FSM 이 **결정하지 않는다**. 새 라우트가 모두 실패하면 FSM 은 surge, unavailable 계산으로 새 라우트 생성을 계속 시도한다. 결국 DEPLOYING timeout 인 30분을 초과하고 coordinator 가 `expired` 경로를 통해 배포를 ROLLING_BACK 으로 전이한다.

### 라우트 분류

라우트는 리비전과 상태로 분류한다:

| 분류 | 조건 | 설명 |
|----------|-----------|-------------|
| `old_active` | revision != deploying_revision, is_active() | 현재 트래픽을 받는 기존 라우트 |
| `new_provisioning` | revision == deploying_revision, PROVISIONING | 생성 중인 새 라우트 |
| `new_healthy` | revision == deploying_revision, HEALTHY | 서비스할 준비가 된 새 라우트 |
| `new_unhealthy` | revision == deploying_revision, UNHEALTHY/DEGRADED | 문제가 있는 새 라우트 |
| `new_failed` | revision == deploying_revision, FAILED/TERMINATED | 실패한 새 라우트 |

### handler 흐름

모든 DEPLOYING 배포는 `DeployingProvisioningHandler` 가 맡고, 배포 lifecycle 내내 PROVISIONING sub-step 에 머문다. handler 는 cycle 마다 전략 evaluator 를 실행한다:

| 결과 | 조건 | handler 동작 |
|--------|-----------|----------------|
| **success** | evaluator 가 COMPLETED 를 반환한다(old 라우트가 없고 healthy 인 new 라우트가 desired 이상) | coordinator 가 READY 로 전이한다 |
| **need_retry** | 라우트 변경(생성, 정리)을 실행했다 | DEPLOYING/PROVISIONING 에 머물고 이력을 기록한다 |
| **skipped** | 변경이 없다. 라우트가 아직 provisioning 중이거나 대기 중이다 | 전이하지 않는다. coordinator 가 timeout 을 검사한다 |
| **expired** | skipped 배포가 DEPLOYING timeout 인 30분을 초과했다 | coordinator 가 DEPLOYING/ROLLING_BACK 으로 전이한다 |

배포가 ROLLING_BACK 으로 전이하면 `DeployingRollingBackHandler` 가 `deploying_revision` 을 비우고 바로 READY 로 전이한다.

### 안전 장치

- **무중단 보호**: `max_unavailable < desired` 이면 새 라우트 하나 이상이 healthy 가 되기 전까지 기존 라우트를 전부 종료하지 않는다
- **교착 방지**: `RollingUpdateSpec` validator 가 `max_surge` 와 `max_unavailable` 중 하나 이상이 양수임을 보장한다
- **timeout 기반 롤백**: FSM 은 실패를 감지하지 않는다. coordinator 의 timeout 장치가 처리한다. 배포가 DEPLOYING timeout 인 30분 안에 끝나지 않으면 coordinator 가 `expired` 경로를 통해 ROLLING_BACK 으로 전이한다

## max_surge / max_unavailable 계산

`desired_replicas = 3`, `max_surge = 1`, `max_unavailable = 1` 인 예:

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

## cycle 별 실행 예시

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

## timeout 과 롤백

배포 timeout 은 coordinator 의 공통 `expired` 전이 장치로 처리한다:

1. `DeployingProvisioningHandler` 가 `status_transitions()` 에 `expired → DEPLOYING/ROLLING_BACK` 을 선언한다
2. coordinator 는 cycle 마다 `result.skipped` 에 있는 배포의 DEPLOYING 경과 시간을 DEPLOYING timeout 인 30분과 비교한다
3. timeout 은 `DeploymentWithHistory` 의 `phase_started_at` 을 기준으로 판단한다. `phase_started_at` 은 이 handler 단계의 첫 scheduling 이력 레코드의 `created_at` 이다
4. `phase_started_at` 은 재시도해도 그대로다. phase/error_code/to_status 가 같은 이력 레코드는 병합되어 `attempts` 만 증가하고 `created_at` 은 변경되지 않는다
5. timeout 을 초과한 배포는 DEPLOYING/ROLLING_BACK 으로 전이한다
6. `DeployingRollingBackHandler` 가 `deploying_revision` 을 비우고 READY 로 전이한다

timeout handler 나 주기 task 를 따로 두지 않는다. coordinator 는 표준 전이 처리에서 timeout 을 검사한다.

## 구성 요소 구조

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

## 완료 시 리비전 교체

모든 old 라우트가 제거되고 healthy 상태인 new 라우트가 desired_replicas 이상이면:

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
