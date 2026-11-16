# 무중단 배포 전략 아키텍처

## 관련 이슈

- 상위 BEP: [BEP-1006: 서비스 배포 전략](BEP-1006-service-deployment-strategy.md)
- 관련 BEP: [BEP-1030: Sokovan 스케줄러 상태 전이 설계](BEP-1030-sokovan-scheduler-status-transition.md)

## 동기

BEP-1006 은 블루그린과 롤링 업데이트 배포 전략의 상위 설계를 정했다. 이 BEP 는 **구현 아키텍처**, 즉 이 전략들이 기존 Sokovan deployment lifecycle 시스템에 어떻게 통합되는지를 다룬다.

핵심 문제: **배포 전략은 본질적으로 여러 cycle 에 걸친다. 완료되거나 롤백될 때까지 coordinator 의 여러 처리 cycle 을 지난다.**

블루그린 배포는 여러 단계를 거치며 여러 coordinator cycle 에 걸친다:

1. **Cycle 1**: `INACTIVE` 트래픽으로 Green 라우트를 생성한다 → 여전히 `DEPLOYING`
2. **Cycle 2-N**: Green 라우트가 아직 provisioning 중이다 → 여전히 `DEPLOYING`
3. **Cycle N+1**: 모든 Green 라우트가 healthy 다 → 트래픽을 전환하고 `READY` 로 전이한다

롤링 업데이트도 마찬가지로 cycle 을 거치며 조금씩 진행한다. 두 전략 모두 **전략이 끝나거나 롤백될 때까지 배포를 여러 처리 cycle 동안 `DEPLOYING` 상태로 유지한다.**

### flat registry, handler 별 평가

DEPLOYING 하위 단계 handler 는 coordinator 의 `HandlerRegistry` 에 다른 lifecycle handler 와 나란히 **flat 하게** 등록되고 `(lifecycle_type, sub_step)` 으로 키를 잡는다. DEPLOYING handler 는 각자 `execute()` 메서드 안에서 전략 evaluator 와 applier 를 **직접** 호출한다. 별도의 사전 단계는 없다. evaluator 가 하위 단계 배정과 라우트 변경을 정하고, applier 가 그것을 DB 에 기록한다.

| 관점 | 동작 방식 |
|--------|-------------|
| **상태 전이** | 각 handler 가 `success/need_retry/expired/give_up` 을 담은 `status_transitions()` 를 반환하고 coordinator 의 공통 경로가 모든 전이를 처리한다 |
| **dispatch** | coordinator 가 `(lifecycle_type, sub_step)` 키로 handler 를 찾아 바로 실행한다 |
| **평가** | 각 handler 가 자기 `execute()` 에서 `evaluator.evaluate()` 와 `applier.apply()` 를 호출한다 |


## 하위 문서

| 문서 | 설명 |
|----------|-------------|
| [롤링 업데이트](BEP-1049/rolling-update.md) | 점진적 라우트 교체 전략. max_surge, max_unavailable 로 제어한다 |
| [블루그린](BEP-1049/blue-green.md) | 원자적 트래픽 전환 전략. INACTIVE 준비 상태와 승격 |

## 제안 설계

### 전체 아키텍처

핵심 아이디어: coordinator 는 `(lifecycle_type, sub_step)` 을 키로 하는 flat `HandlerRegistry` 를 유지한다. 단순한 lifecycle 타입(CHECK_PENDING, SCALING 등)은 `sub_step=None` 으로 등록한다. DEPLOYING 에는 handler 를 둘 등록한다. 하나는 PROVISIONING 용, 하나는 ROLLING_BACK 용이다. 각 handler 는 전략 evaluator 와 applier 를 독립적으로 호출한다.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          Periodic Task Scheduler                             │
│                                                                              │
│  DeploymentTaskSpec                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐      │
│  │ check_pending:           2s / 30s                                  │      │
│  │ check_replica:           5s / 30s                                  │      │
│  │ scaling:                 5s / 30s                                  │      │
│  │ deploying/provisioning:  5s / 30s  ← drives PROVISIONING cycle    │      │
│  │ deploying/rolling_back:  5s / 30s  ← drives ROLLING_BACK cycle    │      │
│  │ reconcile:               -- / 30s                                  │      │
│  │ destroying:              5s / 60s                                  │      │
│  └─────────────┬──────────────────────────────────────────────────────┘      │
│                │                                                             │
│                ▼                                                             │
│  DoDeploymentLifecycleEvent                                                  │
│  DoDeploymentLifecycleIfNeededEvent                                          │
│  (lifecycle_type: str, sub_step: str | None)                                 │
└────────────────┬─────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         DeploymentCoordinator                                │
│                                                                              │
│  process_deployment_lifecycle(lifecycle_type, sub_step=None)                 │
│    handler = registry.handlers[(lifecycle_type, sub_step)]                   │
│    acquire lock if handler.lock_id                                          │
│    _run_handler(handler)                                                     │
│                                                                              │
│  HandlerRegistry:                                                            │
│    handlers: dict[(DeploymentLifecycleType, DeploymentSubStep | None),       │
│                   DeploymentHandler]                                          │
│                                                                              │
│    handlers = {                                                              │
│      (CHECK_PENDING, None)           → CheckPendingHandler                   │
│      (CHECK_REPLICA, None)           → CheckReplicaHandler                   │
│      (SCALING, None)                 → ScalingHandler                        │
│      (RECONCILE, None)               → ReconcileHandler                      │
│      (DEPLOYING, PROVISIONING)       → DeployingProvisioningHandler          │
│      (DEPLOYING, ROLLING_BACK)       → DeployingRollingBackHandler           │
│      (DESTROYING, None)              → DestroyingHandler                     │
│    }                                                                         │
│                                                                              │
│  _run_handler(handler):                                                      │
│    1. Query deployments by handler.target_statuses()                         │
│    2. Build DeploymentWithHistory from scheduling history                    │
│    3. Execute handler + handle status transitions                            │
│    4. Classify failures (give_up / expired / need_retry)                     │
│    5. Check skipped deployments for timeout → expired transition             │
│    6. Post-process (reschedule, trigger dependent lifecycles)                │
│                                                                              │
│  Result handling (same generic path for all handlers):                       │
│    successes  → success status (transition + history + sub_step update)      │
│    errors     → classified into give_up / expired / need_retry               │
│    skipped    → timeout check; if expired transition defined and timed out,  │
│                 transition to expired status                                 │
└────────────────┬─────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  DeploymentHandler (base)                                                    │
│  ├─ name()               → str                              ← abstract      │
│  ├─ lock_id              → LockID | None                     ← abstract     │
│  ├─ target_statuses()    → list[DeploymentLifecycleStatus]   ← abstract     │
│  ├─ status_transitions() → DeploymentStatusTransitions       ← abstract     │
│  ├─ execute(deployments) → DeploymentExecutionResult         ← abstract     │
│  └─ post_process(result) → None                              ← abstract     │
│                                                                              │
│  DEPLOYING handlers (2 total):                                               │
│  ├─ DeployingProvisioningHandler                                             │
│  │    targets: [(DEPLOYING, PROVISIONING)]                                   │
│  │    execute: evaluator.evaluate() + applier.apply()                        │
│  │    success → READY (all routes replaced)                                  │
│  │    need_retry → DEPLOYING/PROVISIONING (route mutations executed)         │
│  │    expired → DEPLOYING/ROLLING_BACK (timeout)                             │
│  │                                                                           │
│  └─ DeployingRollingBackHandler                                              │
│       targets: [(DEPLOYING, ROLLING_BACK)]                                   │
│       execute: clear deploying_revision                                      │
│       success → READY                                                        │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 리비전 활성화 트리거 분기

리비전 전환(`activate_revision`)과 일반 수정(`update_deployment`)은 서로 다른 경로를 간다:

```
activate_revision(deployment_id, revision_id)
    │
    ├─ Guard: lifecycle == DEPLOYING?
    │    → Yes: raise DeploymentAlreadyInProgress
    │
    ├─ Policy lookup: deployment_policy exists with strategy?
    │
    ├─ No policy or no strategy (existing behavior)
    │    → current_revision = revision_id (immediate swap)
    │    → mark("check_replica")
    │
    └─ Policy with strategy (ROLLING / BLUE_GREEN)
         → begin_deployment(endpoint_id, revision_id)
            ├─ deploying_revision = revision_id
            └─ lifecycle = DEPLOYING
         → mark("deploying")
```

복제본 수 변경은 같은 리비전을 추가하거나 제거하는 일이라 전략이 필요하지 않다. 새 코드와 모델을 안전하게 교체해야 하는 리비전 전환만 전략 경로를 사용한다.

### 배포 중 오토스케일링 제외

`DEPLOYING` 상태인 엔드포인트는 오토스케일링 규칙 평가에서 제외한다. 전략 기반 배포에서는 evaluator 가 라우트 생성과 종료를 직접 관리한다(롤링 업데이트의 surge, unavailable, 블루그린의 Green 준비). 오토스케일링이 동시에 라우트를 추가하거나 제거하면 evaluator 의 라우트 관리와 충돌한다. surge 한도를 초과하거나, evaluator 가 있어야 한다고 보는 라우트를 종료하거나, 잘못된 리비전으로 라우트를 생성할 수 있다.

배포가 끝나 엔드포인트가 `READY` 상태로 복귀하면 오토스케일링은 자동으로 다시 시작한다.

### sub-step 종류

블루그린과 롤링 업데이트의 cycle FSM 은 공통된 **sub-step 종류** 묶음을 공유한다. evaluator 가 배포마다 sub-step 을 배정하고 applier 가 `sub_step` column 에 기록한다.

| sub-step | 설명 | 처리 | 전이 |
|----------|-------------|------------|------------|
| **PROVISIONING** | 새 라우트를 생성하는 중이거나, 전략이 진행 중이거나, 라우트가 healthy 가 되기를 기다린다 | DeployingProvisioningHandler | success → READY, need_retry → DEPLOYING/PROVISIONING, expired → DEPLOYING/ROLLING_BACK |
| **ROLLING_BACK** | 롤백 중이다. deploying_revision 을 비우고 이전 리비전을 복원한다 | DeployingRollingBackHandler | success → READY |

### DeploymentStrategyEvaluator

`DeploymentStrategyEvaluator` 는 DEPLOYING 상태의 배포를 평가해 sub-step 배정과 라우트 변경을 정한다. DEPLOYING handler 는 각자 evaluator 와 applier 짝을 가지고 `execute()` 에서 호출한다.

#### 실행 흐름

```
DeploymentStrategyEvaluator.evaluate(deployments)
    │
    │  Phase 1: Load policies and routes
    │  ┌─────────────────────────────────────────────────────────┐
    │  │  policy_map = load_policies(deployments)                │
    │  │  route_map = search_routes(non-terminated)               │
    │  └─────────────────────────────────────────────────────────┘
    │
    │  Phase 2: Run per-deployment strategy FSM
    │  ┌─────────────────────────────────────────────────────────┐
    │  │  for deployment in deployments:                         │
    │  │    policy = policy_map[deployment.id]                   │
    │  │    routes = route_map[deployment.id]                    │
    │  │                                                         │
    │  │    strategy_fsm = create_strategy(policy)                │
    │  │    cycle_result = strategy_fsm.evaluate_cycle(...)      │
    │  │                                                         │
    │  │    assignments[deployment.id] = cycle_result.sub_step   │
    │  │    route_changes.merge(cycle_result.route_changes)       │
    │  └─────────────────────────────────────────────────────────┘
    │
    ▼
  StrategyEvaluationSummary {
    assignments: {
      deploy_A_id: PROVISIONING,
      deploy_B_id: PROVISIONING,
      deploy_C_id: COMPLETED,
    },
    route_changes: RouteChanges {
      rollout_specs:    [Creator, ...],  # new routes to create
      drain_route_ids:  [UUID, ...],     # old routes to terminate
    },
    errors: [EvaluationErrorData, ...],
  }
```

#### 핵심 설계 원칙

1. **evaluator 와 applier 를 handler 마다 호출한다**: DEPLOYING handler 는 `execute()` 에서 `evaluator.evaluate()` 다음 `applier.apply()` 를 호출한다. applier 는 sub-step 배정과 라우트 변경을 `StrategyTransaction` 으로 원자적으로 기록한다.
2. **전략 FSM 은 registry 로 공통 인터페이스를 구현한다**: 모든 전략 구현은 `AbstractDeploymentStrategy` 를 상속하고 `evaluate_cycle()` 을 구현한다. 구체 클래스(`RollingUpdateStrategy`, `BlueGreenStrategy`)는 전용 모듈 파일에 둔다. `DeploymentStrategyRegistry` 는 evaluator 에 주입한다.
3. **완료는 evaluator 가 판정한다**: 전략 FSM 이 모든 라우트가 교체됐다고 판정하면 COMPLETED 를 반환한다. applier 가 리비전 교체(`deploying_revision` → `current_revision`)를 실행한다. provisioning handler 가 이를 success 로 반환하고 coordinator 가 READY 로 전이한다.
4. **ROLLING_BACK 은 정리 handler 다**: provisioning handler 의 skipped 배포가 timeout 을 초과하면(expired) coordinator 가 DEPLOYING/ROLLING_BACK 으로 전이한다. `DeployingRollingBackHandler` 는 `deploying_revision` 을 비우고 바로 READY 로 전이한다. 여러 cycle 에 걸친 롤백이 아니라 한 단계 정리다.

### DEPLOYING handler

두 handler 가 모든 DEPLOYING sub-step 을 맡는다.

#### DeployingProvisioningHandler

`(DEPLOYING, PROVISIONING)` 을 대상으로 한다. 주요 DEPLOYING handler 로, cycle 마다 전략 FSM 을 실행해 라우트를 생성하고 정리하며 완료 여부를 확인한다.

- **success**: 모든 라우트가 교체됐다(COMPLETED) → READY 로 전이한다.
- **need_retry**: 라우트 변경(생성, 정리)을 실행했다 → 이력 기록과 함께 PROVISIONING 에 머문다.
- **skipped**: 변경이 없고 라우트를 계속 기다린다 → 전이하지 않는다. **coordinator 가 timeout 을 검사한다**: `phase_started_at` 이 DEPLOYING timeout 임계값을 초과하면 `expired` 로 분류해 ROLLING_BACK 으로 전이한다.
- **errors**: 평가 에러 → give_up/expired/need_retry 로 분류한다.

```python
class DeployingProvisioningHandler(DeploymentHandler):
    # targets: [(DEPLOYING, PROVISIONING)]
    # success → READY
    # need_retry → DEPLOYING/PROVISIONING
    # expired → DEPLOYING/ROLLING_BACK

    async def execute(self, deployments):
        summary = await self._evaluator.evaluate(deployment_infos)
        apply_result = await self._applier.apply(summary)
        # Classify by apply_result:
        #   completed_ids → successes (coordinator transitions to READY)
        #   route mutations → need_retry (stays in PROVISIONING)
        #   no changes → skipped (coordinator checks timeout)
        #   evaluation errors → errors
        return DeploymentExecutionResult(successes=..., errors=..., skipped=..., need_retry=...)
```

#### DeployingRollingBackHandler

`(DEPLOYING, ROLLING_BACK)` 을 대상으로 한다. `deploying_revision` 을 비우고 바로 READY 로 전이한다.

- **success**: 배포 중인 리비전을 비웠다 → READY 로 전이한다.

```python
class DeployingRollingBackHandler(DeploymentHandler):
    # targets: [(DEPLOYING, ROLLING_BACK)]
    # success → READY

    async def execute(self, deployments):
        await self._applier.clear_deploying_revision(deployment_ids)
        return DeploymentExecutionResult(successes=list(deployments))
```

### 실패 분류와 timeout 처리

coordinator 는 handler 에러를 분류하고 skipped 배포의 timeout 을 검사한다:

```
_handle_status_transitions(handler, result, records)
    │
    │  Success transitions:
    │    result.successes → transitions.success status
    │
    │  Need-retry transitions (explicit from handler):
    │    result.need_retry → transitions.need_retry status
    │    (never escalated to give_up — represents normal progress)
    │
    │  Skipped timeout check:
    │    If transitions.expired is defined and result.skipped is non-empty:
    │      For each skipped deployment, check phase_started_at against
    │      DEPLOYMENT_STATUS_TIMEOUT_MAP threshold.
    │      Timed-out deployments → transitions.expired status.
    │
    │  Failure classification (priority order):
    │    1. give_up:    phase_attempts >= SERVICE_MAX_RETRIES
    │    2. expired:    phase_started_at elapsed > timeout threshold
    │    3. need_retry: default (can be retried next cycle)
    │
    │  Each category uses its own transition from status_transitions():
    │    give_up  → transitions.give_up
    │    expired  → transitions.expired
    │    need_retry → transitions.need_retry
```

`DeploymentWithHistory` 는 scheduling 이력에서 배포별 상태를 추적한다:
- `phase_attempts`: 같은 handler 단계에서 연속으로 시도한 횟수
- `phase_started_at`: 현재 단계의 이력 레코드가 처음 생성된 시각. 재시도해도 초기화하지 않는다. phase/error_code/to_status 가 같은 이력 레코드는 병합되어 `created_at` 을 변경하지 않고 `attempts` 만 증가한다

skipped timeout 검사는 DEPLOYING 에 중요하다. 배포가 평가 에러도 라우트 변경도 없이 라우트의 healthy 전이를 기다리기만 하면 `skipped` 로 나타난다. 이 검사가 없으면 `_classify_failures` 가 `result.errors` 만 처리하므로 `expired` 경로에 절대 도달하지 않는다.

### coordinator 흐름

coordinator 는 모든 handler 에 **하나의 dispatch 경로**를 사용한다:

```
process_deployment_lifecycle(lifecycle_type, sub_step=None)
    │
    │  handler = registry.handlers[(lifecycle_type, sub_step)]
    │  acquire lock if handler.lock_id
    │
    │  _run_handler(handler):
    │    │
    │    │  1. Query deployments by handler.target_statuses()
    │    │     (lifecycles + sub_steps extracted from DeploymentLifecycleStatus list)
    │    │  2. Build DeploymentWithHistory from scheduling history
    │    │  3. Enter DeploymentRecorderContext.scope()
    │    │  ┌───────────────────────────────────────────────────────┐
    │    │  │  result = handler.execute(deployments)                │
    │    │  │  all_records = pool.build_all_records()               │
    │    │  │  _handle_status_transitions(                          │
    │    │  │      handler, result, records)                        │
    │    │  └───────────────────────────────────────────────────────┘
    │    │  4. handler.post_process(result)
    │    │
    │    ▼
```

핵심 설계:
- coordinator 에는 **DEPLOYING 전용 로직이 없다**. 단순 handler 와 sub-step handler 모두 같은 `_run_handler()` 와 `_handle_status_transitions()` 경로를 사용한다.
- DB 필터링은 handler 의 `target_statuses()` 를 사용한다. lifecycle 은 `.lifecycle` 로, sub-step 은 `.sub_status` 로 조회한다.
- `_handle_status_transitions()` 는 `status_transitions()` 의 `sub_status` 를 `EndpointLifecycleBatchUpdaterSpec` 에 적용해, lifecycle 전이와 함께 `sub_step` column 이 변경되게 한다.
- skipped timeout 검사는 공통 장치다. `transitions.expired` 를 선언한 handler 는 누구나 skipped 배포에 대한 timeout 검사를 자동으로 받는다.

### sub-step 기록

cycle 평가마다 sub-step 항목이 생성되고 기존 `DeploymentRecorderContext` 로 기록된다. coordinator 의 `_handle_status_transitions()` 는 handler 결과마다 `extract_sub_steps_for_entity()` 를 호출해 이력에 배포의 sub-step 정보를 추가한다.

#### sub-step 기록: 라우트 변경 단위

sub-step 은 evaluator 의 `_record_route_changes()` 가 **라우트 변경 단위**로 기록한다. 라우트 변경 종류(rollout, drain)마다 영향을 받은 라우트 수와 함께 별도 sub-step 항목으로 기록한다.

**PROVISIONING cycle**: 새 라우트 생성

```
sub_steps:
  rollout       → SUCCESS (message: "3 new route(s)")
  provisioning  → SUCCESS
```

**PROVISIONING cycle**: 새 라우트 생성과 기존 라우트 종료

```
sub_steps:
  rollout       → SUCCESS (message: "1 new route(s)")
  drain         → SUCCESS (message: "1 route(s)")
  provisioning  → SUCCESS
```

**COMPLETED cycle (롤링 업데이트)**: 마지막 drain:

```
sub_steps:
  drain         → SUCCESS (message: "1 route(s)")
```

이로써 다음이 가능하다:

- **관측**: 배포별 진행 상황을 라우트 변경 단위로 엔티티마다 추적한다
- **디버깅**: sub-step 이력이 cycle 마다 어떤 라우트 변경이 있었는지 정확히 보여 준다
- **일관성**: 모든 handler 가 coordinator 의 공통 경로를 그대로 사용한다

### 전략별 설정

| 전략 | 설정 | 설명 |
|----------|---------|-------------|
| **블루그린** | `auto_promote: bool` | 모든 Green 이 healthy 면 트래픽을 자동으로 전환한다 |
| | `promote_delay_seconds: int` | 승격 전 대기 시간 |
| **롤링 업데이트** | `max_surge: int` | 동시에 생성할 수 있는 추가 라우트 최대 수 |
| | `max_unavailable: int` | 허용하는 사용 불가 라우트 최대 수 |

새 라우트가 모두 실패해 전략이 실패하면 자동 롤백을 항상 실행한다.

## 참고

- [BEP-1006: 서비스 배포 전략](BEP-1006-service-deployment-strategy.md): 블루그린과 롤링 업데이트의 상위 설계
- [BEP-1030: Sokovan 스케줄러 상태 전이 설계](BEP-1030-sokovan-scheduler-status-transition.md): Sokovan 스케줄러의 상태 전이 패턴
