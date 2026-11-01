# 블루그린 배포 전략

- 상위 문서: [BEP-1049: 무중단 배포 전략 아키텍처](../BEP-1049-deployment-strategy-handler.md)
- 관련 문서: [롤링 업데이트 배포 전략](./rolling-update.md)

## 개요

블루그린은 기존 라우트(Blue)를 그대로 두고 새 라우트(Green)를 **전부** 생성한 뒤, 모든 Green 라우트가 healthy 가 되면 트래픽을 **원자적으로** 전환하는 배포 전략이다. Green 라우트는 `INACTIVE` 상태로 생성하고 승격 전까지 트래픽을 받지 않는다.

### 설정

```
BlueGreenSpec:
  auto_promote: bool = False          # Whether to auto-switch traffic when all Green are healthy
  promote_delay_seconds: int = 0      # Wait time before auto-promotion (seconds)
```

Green 라우트가 모두 실패해 전략이 실패하면 자동 롤백을 항상 실행한다.

## 리비전 추적

`endpoints` 테이블에는 리비전 관리를 위한 column 이 둘 있다:

- `deploying_revision`: 현재 배포 중인 리비전이다. 진행 중인 배포가 없으면 NULL 이다
- `current_revision`: 현재 트래픽을 서비스하는 리비전이다

## Green 라우트 트래픽 격리

Green 라우트는 `traffic_status=INACTIVE`, `traffic_ratio=0.0` 으로 생성한다. coordinator 의 주기 sync 는 ACTIVE 라우트만 App Proxy 로 전파하므로, 승격 전까지 Green 라우트는 proxy 에 보이지 않는다. 라우트가 새어 나가더라도 Traefik 과 legacy(HTTP/TCP) backend 는 `traffic_ratio=0` 인 라우트를 거부한다.

승격하면 Manager 가 DB 를 변경하고(Green 은 ACTIVE, Blue 는 INACTIVE), coordinator sync 가 그 변경을 App Proxy 로 자동 전파한다. 필요한 것은 DB 기록뿐이고 proxy 설정을 따로 하지 않는다.

## cycle FSM

`DeploymentStrategyEvaluator` 는 블루그린 배포를 주기적으로 평가한다. 호출마다 다음 FSM 을 따른다:

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

### sub-step 종류

cycle 평가는 공유 sub-step 종류 중 하나를 바로 반환한다. 완료는 sub-step 이 아니라 `CycleEvaluationResult(sub_step=PROGRESSING, completed=True)` 로 알린다. coordinator 가 리비전 교체와 READY 전이를 직접 처리한다.

| sub-step | 조건 | handler 동작 |
|----------|-----------|----------------|
| **provisioning** | Green 라우트가 없다 → 모두 INACTIVE 로 생성한다 | DeployingProvisioningHandler → DEPLOYING→DEPLOYING, 다시 예약 |
| **provisioning** | Green 라우트가 PROVISIONING 이다 | DeployingProvisioningHandler → DEPLOYING→DEPLOYING, 다시 예약 |
| **progressing** | 모든 Green 이 healthy 가 아니다(PROVISIONING 없이 상태가 섞여 있다) | DeployingProgressingHandler → DEPLOYING→DEPLOYING, 다시 예약 |
| **progressing** | 모든 Green 이 healthy 이고 승격 트리거(수동 또는 지연)를 기다린다 | DeployingProgressingHandler → DEPLOYING→DEPLOYING, 다시 예약 |
| **progressing** (`completed=True`) | 승격을 실행했다(Green→ACTIVE, Blue→TERMINATING) | coordinator → 원자적 리비전 교체 + DEPLOYING→READY |
| **rolled_back** | Green 이 모두 실패 → Green 을 종료한다 | DeployingRolledBackHandler → DEPLOYING→READY, deploying_revision=NULL |

## promote_delay_seconds 처리

자동 승격 시점은 라우트의 `status_updated_at` column 에서 구한다. 상태를 따로 저장하지 않는다.

`RoutingRow.status_updated_at` 은 라우트 상태가 마지막으로 변경된 시각을 기록한다. Green 라우트가 모두 healthy 이면 그중 가장 늦은 `status_updated_at` 이 마지막 라우트가 healthy 가 된 시점이다.

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

라우트가 unhealthy 가 되었다가 회복하면 회복 시 `status_updated_at` 이 변경되므로 지연 타이머가 자동으로 초기화된다. 그래서 승격은 health 가 안정된 뒤에만 일어난다.

## cycle 별 실행 예시

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

### 수동 승격 시나리오

`auto_promote=False` 일 때:

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

### 롤백 시나리오

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
  │         BLUE_GREEN → blue_green_evaluate(...)                │
  │    4. Aggregate route changes + group by sub_step            │
  │  Coordinator applies route changes after evaluation          │
  └──────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  blue_green_evaluate(deployment, routes, spec)               │
  │  (evaluator internal strategy function)                      │
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
  │  Route changes returned (applied by coordinator):            │
  │  ┌────────────────────────────────────────────────────┐      │
  │  │  ● Green creation (rollout_specs):                 │      │
  │  │    RouteCreatorSpec(                               │      │
  │  │      revision_id = deploying_revision,             │      │
  │  │      traffic_status = INACTIVE  ← differs from RU  │      │
  │  │    ) × target_count                                │      │
  │  │                                                    │      │
  │  │  ● Promotion (traffic switch):                     │      │
  │  │    promote_route_ids: Green route IDs              │      │
  │  │      → traffic_status = ACTIVE                     │      │
  │  │    drain_route_ids: Blue route IDs                 │      │
  │  │      → status = TERMINATING                        │      │
  │  │                                                    │      │
  │  │  ● Rollback:                                       │      │
  │  │    drain_route_ids: Green route IDs                │      │
  │  │      → status = TERMINATING                        │      │
  │  └────────────────────────────────────────────────────┘      │
  └──────────────────────────────────────────────────────────────┘
                             │
                             ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  Per-Sub-Step Handlers (coordinator generic path)            │
  │                                                              │
  │  PROVISIONING → DeployingProvisioningHandler                  │
  │    next_status: DEPLOYING → coordinator records history      │
  │                                                              │
  │  PROGRESSING → DeployingProgressingHandler                   │
  │    next_status: DEPLOYING → coordinator records history      │
  │    completed=True → coordinator atomic revision swap + READY │
  │                                                              │
  │  ROLLED_BACK → DeployingRolledBackHandler                    │
  │    next_status: READY → clear dep_rev + coordinator transit  │
  └──────────────────────────────────────────────────────────────┘
```

## 완료 시 리비전 교체

모든 Green 라우트가 ACTIVE 가 되고 Blue 라우트가 종료되면:

```
  completed determination (evaluator)
       │
       ▼
  Coordinator._transition_completed_deployments()
    → Atomic transaction:
      1. complete_deployment_revision_swap(ids)
         current_revision = deploying_revision
         deploying_revision = NULL
      2. DEPLOYING → READY lifecycle transition
      3. History recording
```

## 롤링 업데이트와 비교

| 관점 | 블루그린 | 롤링 업데이트 |
|--------|------------|---------------|
| **라우트 생성** | 한 번에 전부 | 점진적(max_surge 로 제어) |
| **새 라우트 트래픽** | `INACTIVE` (승격까지 대기) | `ACTIVE` (즉시 트래픽을 받는다) |
| **기존 라우트 제거** | 승격할 때 전부 | 점진적(max_unavailable 로 제어) |
| **트래픽 전환** | 원자적(Green 활성화 + Blue 종료) | 점진적(새 라우트 생성과 동시에 진행) |
| **설정** | `auto_promote`, `promote_delay_seconds` | `max_surge`, `max_unavailable` |
| **자원 사용** | 전환 중 자원 2배 | max_surge 만큼만 추가 |
| **롤백** | Green 만 종료하면 된다(Blue 는 계속 실행 중) | 부분 교체 상태에서 복구해야 한다 |
