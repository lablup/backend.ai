# Sokovan Scheduler 상태 전이 설계

## 관련 이슈

- JIRA: [BA-3912](https://lablup.atlassian.net/browse/BA-3912)
- 상위 Epic: [BA-3853](https://lablup.atlassian.net/browse/BA-3853) (Sokovan Scheduler)
- 관련 BEP: [BEP-1029: Sokovan ObserverHandler 패턴](BEP-1029-sokovan-observer-handler.md)

## 동기

Sokovan Scheduler 의 handler 마다 session 과 kernel 상태를 어떻게 전이하는지 정의하고, 하나의 패턴으로 관리한다.

### 현재 문제

1. **상태 전이 규칙이 흩어져 있다**: 각 handler 구현에 나뉘어 있다
2. **kernel 상태 전이가 빠져 있다**: session 상태만 정의하고 kernel 상태는 암묵적으로 처리한다
3. **성공, 실패, stale 처리 방식이 일관되지 않다**: 각 handler 가 서로 다른 방식을 사용한다
4. **kernel 상태가 일부 남는 문제**: session 이 되돌아갈 때 일부 kernel 이 이전 상태에 남는다

## 제안 설계

### 핵심 원칙

1. **handler 는 SUCCESS, FAILURE, SKIPPED 만 반환한다**: 성공, 실패, 건너뜀 목록이 단순하다
2. **handler 가 모든 상태 전이를 정의한다**: 성공, need_retry, expired, give_up 전이를 `StatusTransitions` 로 정의한다
3. **sokovan coordinator 가 조건을 판정한다**: 경과 시간(expired), 재시도 횟수 초과(give_up)는 coordinator 가 판정한다
4. **sokovan coordinator 가 상태를 적용한다**: handler 가 정의한 전이를 조건에 따라 적용한다

### handler 가 실패 유형을 판단하지 않는 이유

Manager 관점에서는 "복구 불가능"을 판정할 수 없다.

- **image registry 실패**: 일시적인 네트워크 문제일 수 있다
- **image pull 실패**: 나중에 성공할 수 있다
- **container 생성 실패**: 사람이 로그를 확인하고 결정해야 한다
- **agent 통신 실패**: 네트워크 문제인지 실제 소실인지 판정할 수 없다

따라서 handler 는 성공, 실패만 반환하고 expired, give_up 판정은 sokovan coordinator 가 맡는다.

---

## handler 인터페이스

### 1. SchedulingResult (이력 기록용)

```python
class SchedulingResult(StrEnum):
    SUCCESS = "SUCCESS"        # Success
    NEED_RETRY = "NEED_RETRY"  # Will retry
    EXPIRED = "EXPIRED"        # Gave up due to time elapsed
    GIVE_UP = "GIVE_UP"        # Gave up due to retry count exceeded
    SKIPPED = "SKIPPED"        # Not attempted (e.g., resource shortage)
```

| 결과 | 설명 | 상태 전이 |
|--------|-------------|------------------|
| SUCCESS | handler 실행 성공 | 성공 상태로 전이 |
| NEED_RETRY | 실패했지만 재시도한다 | need_retry 상태로 전이 |
| EXPIRED | 현재 상태에서 시간이 경과했다 | expired 상태로 전이 |
| GIVE_UP | 재시도 횟수를 초과해 포기했다 | give_up 상태로 전이 |
| SKIPPED | 시도하지 않았다(다른 session 뒤에 대기 등) | 상태를 유지하고 이력에만 기록 |

### 2. StatusTransitions (상태 전이 정의)

```python
@dataclass(frozen=True)
class TransitionStatus:
    session: SessionStatus | None = None  # None = no change
    kernel: KernelStatus | None = None    # None = no change

@dataclass(frozen=True)
class StatusTransitions:
    success: TransitionStatus | None = None
    need_retry: TransitionStatus | None = None
    expired: TransitionStatus | None = None
    give_up: TransitionStatus | None = None
```

**참고**:
- `TransitionStatus` 의 `None`: 해당 entity 의 상태를 변경하지 않는다
- `StatusTransitions` 의 `None`: 상태를 전혀 변경하지 않고 이력만 기록한다

### 3. LifecycleHandler (Action 트리거)

```python
class LifecycleHandler(ABC):
    @classmethod
    @abstractmethod
    def name(cls) -> str: ...

    @property
    @abstractmethod
    def target_session_statuses(self) -> frozenset[SessionStatus]: ...

    @property
    @abstractmethod
    def target_kernel_statuses(self) -> Optional[list[KernelStatus]]:
        """Kernel statuses to filter sessions.

        Returns:
            None: No kernel filtering (include sessions regardless of kernel status)
            list[KernelStatus]: Include sessions that have kernels in these statuses

        Note: This is simple filtering, not condition checking.
        For condition checking (ALL/ANY/NOT_ANY), use SessionPromotionHandler.
        """
        ...

    @classmethod
    @abstractmethod
    def status_transitions(cls) -> StatusTransitions:
        """Define state transitions for success/failure"""
        ...

    @abstractmethod
    async def execute(self, targets: Sequence[SessionWithKernels]) -> HandlerResult:
        ...
```

**LifecycleHandler 와 SessionPromotionHandler 의 kernel 상태 처리 차이**:
- **LifecycleHandler**: 단순 필터링. 지정한 상태의 kernel 을 가진 session 을 조회한다
- **SessionPromotionHandler**: 조건 검사. ALL/ANY/NOT_ANY 로 kernel 이 조건을 만족하는지 검사해 session 을 승격한다

### 4. HandlerResult

```python
@dataclass
class HandlerResult:
    successes: list[SessionId]   # Succeeded
    failures: list[SessionId]    # Failed (attempted but failed)
    skipped: list[SessionId]     # Skipped (couldn't attempt)
```

- **failures**: 실제로 시도했다가 실패한 경우다. 시도 횟수가 늘고 sokovan coordinator 가 NEED_RETRY, EXPIRED, GIVE_UP 을 판정한다
- **skipped**: 시도하지 못한 경우다(자원 부족 등). 이력에만 기록하고 시도 횟수에 영향을 주지 않는다

### 5. SessionPromotionHandler (kernel 상태 기반 session 승격)

```python
class KernelMatchType(Enum):
    ALL = "all"        # All kernels meet condition
    ANY = "any"        # At least one kernel meets condition
    NOT_ANY = "not_any"  # No kernel meets condition

class SessionPromotionHandler(ABC):
    @classmethod
    @abstractmethod
    def name(cls) -> str: ...

    @property
    @abstractmethod
    def target_session_statuses(self) -> frozenset[SessionStatus]: ...

    @property
    @abstractmethod
    def check_kernel_statuses(self) -> frozenset[KernelStatus]:
        """Kernel statuses to check (these statuses mean completed)"""
        ...

    @property
    @abstractmethod
    def match_type(self) -> KernelMatchType: ...

    @classmethod
    @abstractmethod
    def success_session_status(cls) -> SessionStatus:
        """Session status when promoted"""
        ...

    # Kernel status is not changed (only Session is promoted)
```

---

## session 상태 전이

### 상태 흐름 다이어그램

```
(create)
    │
    ▼
┌─────────┐        ┌───────────┐        ┌───────────┐        ┌──────────┐        ┌──────────┐        ┌─────────┐
│ PENDING │───────►│ SCHEDULED │───────►│ PREPARING │───────►│ PREPARED │───────►│ CREATING │───────►│ RUNNING │
└────┬────┘        └─────┬─────┘        └─────┬─────┘        └────┬─────┘        └────┬─────┘        └────┬────┘
     │                   │                    │                   │                   │                   │
     │need_retry         │need_retry          │need_retry         │need_retry         │need_retry         │kernel
     │(maintain)         │(maintain)          │(maintain)         │(maintain)         │(maintain)         │failure
     │                   │                    │                   │                   │                   │
     │expired/give_up    │expired/give_up     │expired/give_up    │expired/give_up    │expired/give_up    │
     │                   │                    │                   │                   │                   │
     ▼                   ▼                    ▼                   ▼                   ▼                   ▼
┌───────────┐       ┌─────────┐          ┌─────────┐        ┌─────────┐        ┌─────────┐        ┌─────────────┐
│ CANCELLED │       │ PENDING │          │ PENDING │        │ PENDING │        │ PENDING │        │ TERMINATING │
└───────────┘       └─────────┘          └─────────┘        └─────────┘        └─────────┘        └──────┬──────┘
                         ▲                    ▲                  ▲                  ▲                    │
                         │                    │                  │                  │                    │success
                         └────────────────────┴──────────────────┴──────────────────┘                    │/expired
                                           (re-scheduling)                                               ▼
                                                                                                  ┌────────────┐
                                                                                                  │ TERMINATED │
                                                                                                  └────────────┘
```

**흐름 설명**:
- 정상 흐름: 위쪽 가로 방향(→)
- 실패 흐름: 아래쪽 세로 방향(↓)
- **PENDING**: expired, give_up → CANCELLED (아직 시작하지 않음)
- **SCHEDULED 이후**: expired, give_up → PENDING (재스케줄링)
- **need_retry**: 모든 상태에서 현재 상태를 유지한다(재시도)
- PREPARING → PREPARED: SessionPromotionHandler 가 kernel 상태를 확인해 승격한다
- CREATING → RUNNING: SessionPromotionHandler 가 kernel 상태를 확인해 승격한다

### handler 상태 전이 표

| handler | 현재 | SUCCESS | NEED_RETRY | EXPIRED | GIVE_UP |
|---------|---------|---------|------------|---------|---------|
| **ScheduleNewSessions** | PENDING | SCHEDULED | (유지) | CANCELLED | CANCELLED |
| **PrepareSessions** | SCHEDULED, PREPARING | PREPARING | (유지) | PENDING | PENDING |
| **StartSessions** | PREPARED | CREATING | (유지) | PENDING | PENDING |
| **TerminateSessions** | TERMINATING | TERMINATED | (유지) | TERMINATED | TERMINATED |

**참고**: NEED_RETRY = (유지) 는 `need_retry=None` 으로 구현하며, 상태를 변경하지 않고 이력만 기록한다

### SessionPromotionHandler 상태 전이 표

| handler | 현재 | check_kernel_statuses | match | SUCCESS |
|---------|---------|----------------------|-------|---------|
| **PromoteToPrepared** | SCHEDULED, PREPARING | PENDING, SCHEDULED, PREPARING, PULLING | NOT_ANY | PREPARED |
| **PromoteToRunning** | CREATING | PENDING, SCHEDULED, PREPARING, PULLING, PREPARED, CREATING | NOT_ANY | RUNNING |
| **PromoteToTerminated** | TERMINATING | non-terminal (PENDING~RUNNING) | NOT_ANY | TERMINATED |
| **DetectTermination** | RUNNING | terminal (TERMINATED, CANCELLED, ERROR) | ANY | TERMINATING |

**참고**: NOT_ANY 는 지정한 상태에 있는 kernel 이 하나도 없을 때 조건을 만족한다

---

## sokovan coordinator 처리 흐름

handler 가 `status_transitions()` 로 모든 상태 전이를 정의하고 sokovan coordinator 가 이를 적용한다.

```python
async def _handle_result(
    self,
    handler: LifecycleHandler,
    result: HandlerResult,
    sessions: Sequence[SessionWithKernels],
) -> None:
    transitions = handler.status_transitions()

    # 1. SUCCESS → Apply success status
    if result.successes:
        await self._repository.update_statuses(
            session_ids=result.successes,
            session_status=transitions.success.session,
            kernel_status=transitions.success.kernel,
        )
        await self._record_history(result.successes, SchedulingResult.SUCCESS)

    # 2. FAILURE → Judge NEED_RETRY / EXPIRED / GIVE_UP
    if result.failures:
        # Increment try count
        await self._increment_try_count(result.failures)

        # GIVE_UP: Retry count exceeded
        give_up_ids = await self._check_retry_exceeded(result.failures)
        if give_up_ids:
            await self._repository.update_statuses(
                session_ids=give_up_ids,
                session_status=transitions.give_up.session,
                kernel_status=transitions.give_up.kernel,
            )
            await self._record_history(give_up_ids, SchedulingResult.GIVE_UP)

        # NEED_RETRY: Will retry (maintain status, only record history)
        retry_ids = [sid for sid in result.failures if sid not in give_up_ids]
        if retry_ids:
            # If need_retry is None, no status change, only record history
            if transitions.need_retry is not None:
                await self._repository.update_statuses(
                    session_ids=retry_ids,
                    session_status=transitions.need_retry.session,
                    kernel_status=transitions.need_retry.kernel,
                )
            await self._record_history(retry_ids, SchedulingResult.NEED_RETRY)

    # 3. EXPIRED: Time elapsed in current state (excluding failures)
    remaining = [s for s in sessions if s.id not in result.successes and s.id not in result.failures]
    expired_ids = await self._check_expired(remaining)
    if expired_ids:
        await self._repository.update_statuses(
            session_ids=expired_ids,
            session_status=transitions.expired.session,
            kernel_status=transitions.expired.kernel,
        )
        await self._record_history(expired_ids, SchedulingResult.EXPIRED)

    # 4. SKIPPED: Couldn't attempt (only record in history)
    if result.skipped:
        await self._record_history(result.skipped, SchedulingResult.SKIPPED)
```

---

## handler 분류

### LifecycleHandler (Action 트리거, session 과 kernel 상태 변경)

| handler | 대상 session | 대상 kernel |
|---------|----------------|---------------|
| **ScheduleNewSessions** | PENDING | PENDING |
| **PrepareSessions** | SCHEDULED | SCHEDULED |
| **StartSessions** | PREPARED | PREPARED |
| **TerminateSessions** | TERMINATING | non-terminal |

### LifecycleHandler 별 StatusTransitions

```python
# ScheduleNewSessions
StatusTransitions(
    success=TransitionStatus(session=SCHEDULED, kernel=SCHEDULED),
    need_retry=None,  # Maintain (PENDING → PENDING)
    expired=TransitionStatus(session=CANCELLED, kernel=CANCELLED),
    give_up=TransitionStatus(session=CANCELLED, kernel=CANCELLED),
)

# PrepareSessions
StatusTransitions(
    success=TransitionStatus(session=PREPARING, kernel=PREPARING),
    need_retry=None,  # Maintain (SCHEDULED/PREPARING)
    expired=TransitionStatus(session=PENDING, kernel=PENDING),   # Re-scheduling
    give_up=TransitionStatus(session=PENDING, kernel=PENDING),   # Re-scheduling
)

# StartSessions
StatusTransitions(
    success=TransitionStatus(session=CREATING, kernel=CREATING),
    need_retry=None,  # Maintain (PREPARED)
    expired=TransitionStatus(session=PENDING, kernel=PENDING),   # Re-scheduling
    give_up=TransitionStatus(session=PENDING, kernel=PENDING),   # Re-scheduling
)

# TerminateSessions
StatusTransitions(
    success=TransitionStatus(session=TERMINATED, kernel=TERMINATED),
    need_retry=None,  # Maintain (TERMINATING)
    expired=TransitionStatus(session=TERMINATED, kernel=TERMINATED),
    give_up=TransitionStatus(session=TERMINATED, kernel=TERMINATED),
)
```

### SessionPromotionHandler (kernel 상태 확인 → session 승격)

| handler | 대상 session | check_kernel_statuses | match_type | 성공 시 session |
|---------|----------------|----------------------|------------|-----------------|
| **PromoteToPrepared** | SCHEDULED, PREPARING | PENDING, SCHEDULED, PREPARING, PULLING | NOT_ANY | PREPARED |
| **PromoteToRunning** | CREATING | PENDING~CREATING | NOT_ANY | RUNNING |
| **PromoteToTerminated** | TERMINATING | non-terminal | NOT_ANY | TERMINATED |
| **DetectTermination** | RUNNING | terminal | ANY | TERMINATING |

**승격 조건**:
- NOT_ANY: 지정한 상태에 있는 kernel 이 없을 때 승격한다(모든 kernel 이 해당 상태를 지난 경우)
- ANY: 지정한 상태에 있는 kernel 이 하나라도 있으면 감지한다

---

## DB query (ALL, ANY, NOT_ANY 판정)

```sql
-- ALL: All kernels meet condition
-- → Find sessions with kernels not in condition, the rest meet ALL
SELECT DISTINCT session_id FROM kernels
WHERE session_id IN (:session_ids)
  AND status NOT IN (:check_statuses)
-- session_id not in result = meets ALL condition

-- ANY: At least one kernel meets condition
SELECT DISTINCT session_id FROM kernels
WHERE session_id IN (:session_ids)
  AND status IN (:check_statuses)
-- session_id in result = meets ANY condition

-- NOT_ANY: No kernel meets condition
-- → Find sessions with kernels in condition, the rest meet NOT_ANY
SELECT DISTINCT session_id FROM kernels
WHERE session_id IN (:session_ids)
  AND status IN (:check_statuses)
-- session_id not in result = meets NOT_ANY condition
```

---

## deployment handler 분석

### EndpointLifecycle 상태 (실제 구현)

```python
class EndpointLifecycle(Enum):
    PENDING = "pending"
    CREATED = "created"     # Deprecated, use READY instead
    SCALING = "scaling"
    READY = "ready"
    DEPLOYING = "deploying"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"
```

### 현재 handler 목록 (handler 5개)

| handler | 대상 | 다음 | 실패 | 역할 |
|---------|--------|------|---------|------|
| **CheckPendingDeployment** | PENDING, CREATED | SCALING | None | pending 상태를 확인하고 scaling 을 시작한다 |
| **ScalingDeployment** | SCALING | READY | None | 실제 scaling 을 수행한다 |
| **CheckReplicaDeployment** | READY | SCALING | None | replica 수를 확인하고 필요하면 scaling 한다 |
| **ReconcileDeployment** | READY | None | SCALING | replica 와 route 불일치를 감지한다 |
| **DestroyingDeployment** | DESTROYING | DESTROYED | DESTROYED | deployment 를 삭제한다 |

### 상태 흐름

```
(create)
    │
    ▼
┌─────────────────┐        ┌─────────┐        ┌─────────┐
│ PENDING/CREATED │───────►│ SCALING │───────►│  READY  │◄──┐
└─────────────────┘        └─────────┘        └────┬────┘   │
                                                   │        │
                                                   │        │ replica adjustment
                                                   ▼        │
                                              ┌─────────┐   │
                                              │ SCALING │───┘
                                              └─────────┘
                                             (CheckReplica/Reconcile)

(destroy request)
    │
    ▼
┌────────────┐        ┌───────────┐
│ DESTROYING │───────►│ DESTROYED │
└────────────┘        └───────────┘
```

**흐름 설명**:
- **PENDING/CREATED → SCALING → READY**: 정상 deployment 흐름
- **READY → SCALING → READY**: replica 불일치 시 재조정(CheckReplica/Reconcile)
- **DESTROYING → DESTROYED**: deployment 삭제 흐름(별도 트리거)
- deployment 는 expired, give_up 없이 성공, 실패만 처리한다

### deployment handler 상태 전이 표

| handler | 현재 | SUCCESS | FAILURE |
|---------|---------|---------|---------|
| **CheckPendingDeployment** | PENDING, CREATED | SCALING | (유지) |
| **ScalingDeployment** | SCALING | READY | (유지) |
| **CheckReplicaDeployment** | READY | SCALING | (유지) |
| **ReconcileDeployment** | READY | (유지) | SCALING |
| **DestroyingDeployment** | DESTROYING | DESTROYED | DESTROYED |

---

## route handler 분석

### RouteStatus 상태 (실제 구현)

```python
class RouteStatus(StrEnum):
    PROVISIONING = "provisioning"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    TERMINATING = "terminating"
    TERMINATED = "terminated"
    FAILED_TO_START = "failed_to_start"
```

### 현재 handler 목록 (handler 6개)

| handler | 대상 | 다음 | 실패 | stale | 역할 |
|---------|--------|------|---------|-------|------|
| **ProvisioningRoute** | PROVISIONING | DEGRADED | FAILED_TO_START | - | route 프로비저닝 |
| **HealthCheckRoute** | HEALTHY, UNHEALTHY, DEGRADED | HEALTHY | UNHEALTHY | DEGRADED | health check |
| **RunningRoute** | DEGRADED, HEALTHY, UNHEALTHY, FAILED_TO_START | - | TERMINATING | - | 실행 중인 route 확인 |
| **RouteEviction** | UNHEALTHY | TERMINATING | - | - | 비정상 route 제거 |
| **TerminatingRoute** | TERMINATING | TERMINATED | - | - | route 종료 |
| **ServiceDiscoverySync** | HEALTHY | - | - | - | service discovery 동기화 |

### 상태 흐름

```
(create)
    │
    ▼
┌──────────────┐        ┌──────────┐        ┌─────────┐
│ PROVISIONING │───────►│ DEGRADED │───────►│ HEALTHY │◄──┐
└──────┬───────┘        └────┬─────┘        └────┬────┘   │
       │                     │                   │        │
       │failure              │health fail        │health  │
       │                     │                   │fail    │
       ▼                     ▼                   ▼        │
┌─────────────────┐    ┌───────────┐       ┌───────────┐  │
│ FAILED_TO_START │    │ UNHEALTHY │───────│           │──┘
└────────┬────────┘    └─────┬─────┘       │(recovery) │
         │                   │             └───────────┘
         │                   │eviction
         │failure            │
         │(RunningRoute)     │
         │                   ▼
         │             ┌─────────────┐        ┌────────────┐
         └────────────►│ TERMINATING │───────►│ TERMINATED │
                       └─────────────┘        └────────────┘
```

**흐름 설명**:
- 정상 흐름: 위쪽 가로 방향(→)
- 실패 흐름: 아래쪽 세로 방향(↓)
- **PROVISIONING**: 성공 → DEGRADED, 실패 → FAILED_TO_START
- **DEGRADED → HEALTHY**: HealthCheck 성공
- **HEALTHY/DEGRADED → UNHEALTHY**: HealthCheck 실패
- **UNHEALTHY → HEALTHY**: 상태가 회복될 때
- **UNHEALTHY → TERMINATING**: RouteEviction
- **FAILED_TO_START → TERMINATING**: RunningRoute 실패
- route 는 expired, give_up 없이 성공, 실패, stale 만 처리한다

### route handler 상태 전이 표

| handler | 현재 | SUCCESS | FAILURE | STALE |
|---------|---------|---------|---------|-------|
| **ProvisioningRoute** | PROVISIONING | DEGRADED | FAILED_TO_START | - |
| **HealthCheckRoute** | HEALTHY, UNHEALTHY, DEGRADED | HEALTHY | UNHEALTHY | DEGRADED |
| **RunningRoute** | DEGRADED, HEALTHY, UNHEALTHY, FAILED_TO_START | (유지) | TERMINATING | - |
| **RouteEviction** | UNHEALTHY | TERMINATING | (유지) | - |
| **TerminatingRoute** | TERMINATING | TERMINATED | (유지) | - |
| **ServiceDiscoverySync** | HEALTHY | (유지) | (유지) | - |

---

## handler 비교 분석

| 항목 | session handler | deployment handler | route handler |
|------|-----------------|-------------------|---------------|
| **handler 수** | 8 (Lifecycle 4 + Promotion 4) | 5 | 6 |
| **entity ID** | SessionId | DeploymentId | RouteId |
| **하위 entity** | Kernel | Route (간접) | - |
| **상태 enum** | SessionStatus, KernelStatus | EndpointLifecycle | RouteStatus |
| **결과 유형** | SUCCESS, NEED_RETRY, EXPIRED, GIVE_UP, SKIPPED | SUCCESS, FAILURE | SUCCESS, FAILURE, STALE |
| **재시도/타임아웃** | sokovan coordinator 가 판정(expired, give_up) | 없음 | 없음(stale 만) |
| **이력** | SchedulingResult 로 기록 | SUCCESS/FAILURE 로 기록 | SUCCESS/FAILURE/STALE 로 기록 |

---

## 구현 계획

### Phase 1: 기본 인프라

1. `TransitionStatus`, `StatusTransitions` dataclass 정의
2. `HandlerResult` dataclass 정의(successes, failures, skipped)
3. `SchedulingResult` enum 정의(SUCCESS, NEED_RETRY, EXPIRED, GIVE_UP, SKIPPED)
4. `LifecycleHandler` 인터페이스 수정(`status_transitions()` 메서드)
5. `SessionPromotionHandler` ABC 추가

### Phase 2: handler 구현

1. 기존 handler 를 새 패턴으로 이전
2. LifecycleHandler 4개에 `status_transitions()` 구현
3. SessionPromotionHandler 4개 구현

### Phase 3: sokovan coordinator 수정

1. `_handle_result()` 구현: `handler.status_transitions()` 사용
2. `_check_expired()` 구현(경과 시간 확인)
3. `_check_retry_exceeded()` 구현(재시도 횟수 초과 확인 → give_up)
4. 이력 기록 로직 통합(`SchedulingResult` 저장)

---

## 열린 질문

1. **maintenance handler 통합 범위**: SweepStaleKernels 외에 통합할 수 있는 대상
2. **deployment, route 확장 시점**: session 완료 직후 진행과 별도 BEP 분리 중 선택이 필요하다
3. **RESCHEDULING 상태 도입**: PENDING 과 재스케줄된 session 을 구분해야 하면 별도 BEP 로 진행한다

## 참고

- [BEP-1029: Sokovan ObserverHandler 패턴](BEP-1029-sokovan-observer-handler.md)
- Sokovan Scheduler: `src/ai/backend/manager/sokovan/scheduler/`
- Deployment Handler: `src/ai/backend/manager/sokovan/deployment/handlers/`
- Route Handler: `src/ai/backend/manager/sokovan/deployment/route/handlers/`
