---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2025-01-16
Created-Version: 26.1.0
Target-Version: 26.1.0
Implemented-Version:
---

# Sokovan Scheduler Status Transition Design

## Related Issues

- JIRA: [BA-3912](https://lablup.atlassian.net/browse/BA-3912)
- Parent Epic: [BA-3853](https://lablup.atlassian.net/browse/BA-3853) (Sokovan Scheduler)
- Related BEP: [BEP-1029: Sokovan ObserverHandler Pattern](BEP-1029-sokovan-observer-handler.md)

## Motivation

Define how each handler in the Sokovan Scheduler transitions Session and Kernel states, and manage them with a unified pattern.

### Current Problems

1. **Status transition rules are scattered**: Distributed across each handler implementation
2. **Missing kernel state transitions**: Only session states are defined, kernel states are handled implicitly
3. **Inconsistent success/failure/stale handling**: Each uses different approaches
4. **Partial kernel state issues**: When session regresses, some kernels remain in previous states

## Proposed Design

### Core Principles

1. **Handlers return only SUCCESS/FAILURE/SKIPPED** - Simple success/failure/skip lists
2. **Handlers define all state transitions** - `StatusTransitions` for success/need_retry/expired/give_up transitions
3. **Coordinator judges conditions** - Time elapsed (expired), retry count exceeded (give_up) are judged by Coordinator
4. **Coordinator applies states** - Applies transitions defined by handlers based on conditions

### Why Handlers Don't Judge Failure Types

From Manager's perspective, it's impossible to determine "unrecoverable":

- **Image registry failure**: Could be temporary network issue
- **Image pull failure**: Might succeed later
- **Container creation failure**: Human needs to check logs and decide
- **Agent communication failure**: Can't determine if it's network issue or actual loss

Therefore, handlers simply return success/failure, and expired/give_up judgment is Coordinator's responsibility.

---

## Handler Interfaces

### 1. SchedulingResult (For History Recording)

```python
class SchedulingResult(StrEnum):
    SUCCESS = "SUCCESS"        # Success
    NEED_RETRY = "NEED_RETRY"  # Will retry
    EXPIRED = "EXPIRED"        # Gave up due to time elapsed
    GIVE_UP = "GIVE_UP"        # Gave up due to retry count exceeded
    SKIPPED = "SKIPPED"        # Not attempted (e.g., resource shortage)
```

| Result | Description | State Transition |
|--------|-------------|------------------|
| SUCCESS | Handler execution succeeded | Transition to success status |
| NEED_RETRY | Failed but will retry | Transition to need_retry status |
| EXPIRED | Time elapsed in current state | Transition to expired status |
| GIVE_UP | Gave up due to retry count exceeded | Transition to give_up status |
| SKIPPED | Not attempted (queued behind other sessions, etc.) | Status maintained, only recorded in history |

### 2. StatusTransitions (State Transition Definition)

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

**Note**:
- `None` in `TransitionStatus`: Don't change that entity's status
- `None` in `StatusTransitions`: No status change at all, only record history

### 3. LifecycleHandler (Action Trigger)

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

**LifecycleHandler vs SessionPromotionHandler - Kernel Status Handling**:
- **LifecycleHandler**: Simple filtering - fetch sessions that have kernels in specified statuses
- **SessionPromotionHandler**: Condition checking - check if ALL/ANY/NOT_ANY kernels meet the condition to promote session

### 4. HandlerResult

```python
@dataclass
class HandlerResult:
    successes: list[SessionId]   # Succeeded
    failures: list[SessionId]    # Failed (attempted but failed)
    skipped: list[SessionId]     # Skipped (couldn't attempt)
```

- **failures**: Actually attempted and failed → try count increases, Coordinator judges NEED_RETRY/EXPIRED/GIVE_UP
- **skipped**: Couldn't attempt (resource shortage, etc.) → only recorded in history, doesn't affect try count

### 5. SessionPromotionHandler (Session Promotion Based on Kernel Status)

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

## Session State Transitions

### State Flow Diagram

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

**Flow Description**:
- Normal flow: Horizontal direction at top (→)
- Failure flow: Vertical direction downward (↓)
- **PENDING**: expired/give_up → CANCELLED (not started yet)
- **After SCHEDULED**: expired/give_up → PENDING (re-scheduling)
- **need_retry**: Maintain current status in all states (retry)
- PREPARING → PREPARED: SessionPromotionHandler checks Kernel status and promotes
- CREATING → RUNNING: SessionPromotionHandler checks Kernel status and promotes

### Handler State Transition Table

| Handler | Current | SUCCESS | NEED_RETRY | EXPIRED | GIVE_UP |
|---------|---------|---------|------------|---------|---------|
| **ScheduleNewSessions** | PENDING | SCHEDULED | (maintain) | CANCELLED | CANCELLED |
| **PrepareSessions** | SCHEDULED, PREPARING | PREPARING | (maintain) | PENDING | PENDING |
| **StartSessions** | PREPARED | CREATING | (maintain) | PENDING | PENDING |
| **TerminateSessions** | TERMINATING | TERMINATED | (maintain) | TERMINATED | TERMINATED |

**Note**: NEED_RETRY = (maintain) is implemented as `need_retry=None`, no status change, only history recorded

### SessionPromotionHandler State Transition Table

| Handler | Current | check_kernel_statuses | match | SUCCESS |
|---------|---------|----------------------|-------|---------|
| **PromoteToPrepared** | SCHEDULED, PREPARING | PENDING, SCHEDULED, PREPARING, PULLING | NOT_ANY | PREPARED |
| **PromoteToRunning** | CREATING | PENDING, SCHEDULED, PREPARING, PULLING, PREPARED, CREATING | NOT_ANY | RUNNING |
| **PromoteToTerminated** | TERMINATING | non-terminal (PENDING~RUNNING) | NOT_ANY | TERMINATED |
| **DetectTermination** | RUNNING | terminal (TERMINATED, CANCELLED, ERROR) | ANY | TERMINATING |

**Note**: NOT_ANY = Condition met when no kernel is in the specified statuses

---

## Coordinator Processing Flow

Handlers define all state transitions via `status_transitions()`, and Coordinator applies them:

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

## Handler Classification

### LifecycleHandler (Action Trigger, Session + Kernel Status Change)

| Handler | target Session | target Kernel |
|---------|----------------|---------------|
| **ScheduleNewSessions** | PENDING | PENDING |
| **PrepareSessions** | SCHEDULED | SCHEDULED |
| **StartSessions** | PREPARED | PREPARED |
| **TerminateSessions** | TERMINATING | non-terminal |

### StatusTransitions per LifecycleHandler

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

### SessionPromotionHandler (Check Kernel Status → Promote Session)

| Handler | target Session | check_kernel_statuses | match_type | success Session |
|---------|----------------|----------------------|------------|-----------------|
| **PromoteToPrepared** | SCHEDULED, PREPARING | PENDING, SCHEDULED, PREPARING, PULLING | NOT_ANY | PREPARED |
| **PromoteToRunning** | CREATING | PENDING~CREATING | NOT_ANY | RUNNING |
| **PromoteToTerminated** | TERMINATING | non-terminal | NOT_ANY | TERMINATED |
| **DetectTermination** | RUNNING | terminal | ANY | TERMINATING |

**Promotion Conditions**:
- NOT_ANY: Promote when no kernel is in specified statuses (= all kernels have passed those statuses)
- ANY: Detect when at least one kernel is in specified statuses

---

## DB Queries (ALL/ANY/NOT_ANY Judgment)

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

## Deployment Handler Analysis

### EndpointLifecycle States (Actual Implementation)

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

### Current Handler List (5 handlers)

| Handler | target | next | failure | Role |
|---------|--------|------|---------|------|
| **CheckPendingDeployment** | PENDING, CREATED | SCALING | None | Check pending and start scaling |
| **ScalingDeployment** | SCALING | READY | None | Perform actual scaling |
| **CheckReplicaDeployment** | READY | SCALING | None | Check replica count and scale if needed |
| **ReconcileDeployment** | READY | None | SCALING | Detect replica-route mismatch |
| **DestroyingDeployment** | DESTROYING | DESTROYED | DESTROYED | Delete deployment |

### State Flow

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

**Flow Description**:
- **PENDING/CREATED → SCALING → READY**: Normal deployment flow
- **READY ↔ SCALING**: Re-adjustment on replica mismatch (CheckReplica/Reconcile)
- **DESTROYING → DESTROYED**: Deployment deletion flow (separate trigger)
- Deployment handles only success/failure without expired/give_up

### Deployment Handler State Transition Table

| Handler | Current | SUCCESS | FAILURE |
|---------|---------|---------|---------|
| **CheckPendingDeployment** | PENDING, CREATED | SCALING | (maintain) |
| **ScalingDeployment** | SCALING | READY | (maintain) |
| **CheckReplicaDeployment** | READY | SCALING | (maintain) |
| **ReconcileDeployment** | READY | (maintain) | SCALING |
| **DestroyingDeployment** | DESTROYING | DESTROYED | DESTROYED |

---

## Route Handler Analysis

### RouteStatus States (Actual Implementation)

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

### Current Handler List (6 handlers)

| Handler | target | next | failure | stale | Role |
|---------|--------|------|---------|-------|------|
| **ProvisioningRoute** | PROVISIONING | DEGRADED | FAILED_TO_START | - | Route provisioning |
| **HealthCheckRoute** | HEALTHY, UNHEALTHY, DEGRADED | HEALTHY | UNHEALTHY | DEGRADED | Health check |
| **RunningRoute** | DEGRADED, HEALTHY, UNHEALTHY, FAILED_TO_START | - | TERMINATING | - | Check running routes |
| **RouteEviction** | UNHEALTHY | TERMINATING | - | - | Remove unhealthy routes |
| **TerminatingRoute** | TERMINATING | TERMINATED | - | - | Route termination |
| **ServiceDiscoverySync** | HEALTHY | - | - | - | Service discovery sync |

### State Flow

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

**Flow Description**:
- Normal flow: Horizontal direction at top (→)
- Failure flow: Vertical direction downward (↓)
- **PROVISIONING**: success → DEGRADED, failure → FAILED_TO_START
- **DEGRADED → HEALTHY**: HealthCheck success
- **HEALTHY/DEGRADED → UNHEALTHY**: HealthCheck failure
- **UNHEALTHY → HEALTHY**: On health recovery
- **UNHEALTHY → TERMINATING**: RouteEviction
- **FAILED_TO_START → TERMINATING**: RunningRoute failure
- Route handles only success/failure/stale without expired/give_up

### Route Handler State Transition Table

| Handler | Current | SUCCESS | FAILURE | STALE |
|---------|---------|---------|---------|-------|
| **ProvisioningRoute** | PROVISIONING | DEGRADED | FAILED_TO_START | - |
| **HealthCheckRoute** | HEALTHY, UNHEALTHY, DEGRADED | HEALTHY | UNHEALTHY | DEGRADED |
| **RunningRoute** | DEGRADED, HEALTHY, UNHEALTHY, FAILED_TO_START | (maintain) | TERMINATING | - |
| **RouteEviction** | UNHEALTHY | TERMINATING | (maintain) | - |
| **TerminatingRoute** | TERMINATING | TERMINATED | (maintain) | - |
| **ServiceDiscoverySync** | HEALTHY | (maintain) | (maintain) | - |

---

## Handler Comparison Analysis

| Item | Session Handler | Deployment Handler | Route Handler |
|------|-----------------|-------------------|---------------|
| **Handler Count** | 8 (4 Lifecycle + 4 Promotion) | 5 | 6 |
| **Entity ID** | SessionId | DeploymentId | RouteId |
| **Sub-entity** | Kernel | Route (indirect) | - |
| **Status Enum** | SessionStatus, KernelStatus | EndpointLifecycle | RouteStatus |
| **Result Types** | SUCCESS, NEED_RETRY, EXPIRED, GIVE_UP, SKIPPED | SUCCESS, FAILURE | SUCCESS, FAILURE, STALE |
| **Retry/Timeout** | Coordinator judges (expired, give_up) | None | None (only stale) |
| **History** | Recorded as SchedulingResult | Recorded as SUCCESS/FAILURE | Recorded as SUCCESS/FAILURE/STALE |

---

## Implementation Plan

### Phase 1: Basic Infrastructure

1. Define `TransitionStatus`, `StatusTransitions` dataclasses
2. Define `HandlerResult` dataclass (successes, failures, skipped)
3. Define `SchedulingResult` enum (SUCCESS, NEED_RETRY, EXPIRED, GIVE_UP, SKIPPED)
4. Modify `LifecycleHandler` interface (`status_transitions()` method)
5. Add `SessionPromotionHandler` ABC

### Phase 2: Handler Implementation

1. Migrate existing handlers to new pattern
2. Implement `status_transitions()` in 4 LifecycleHandlers
3. Implement 4 SessionPromotionHandlers

### Phase 3: Coordinator Modification

1. Implement `_handle_result()` - use `handler.status_transitions()`
2. Implement `_check_expired()` (time elapsed check)
3. Implement `_check_retry_exceeded()` (retry count exceeded check → give_up)
4. Integrate history recording logic (save `SchedulingResult`)

---

## Open Questions

1. **Maintenance handler integration scope**: What else can be integrated besides SweepStaleKernels?
2. **Deployment/Route extension timing**: Right after Session is complete? Separate BEP?
3. **RESCHEDULING status introduction**: If differentiation between PENDING and re-scheduled sessions is needed, proceed with separate BEP

## References

- [BEP-1029: Sokovan ObserverHandler Pattern](BEP-1029-sokovan-observer-handler.md)
- Sokovan Scheduler: `src/ai/backend/manager/sokovan/scheduler/`
- Deployment Handler: `src/ai/backend/manager/sokovan/deployment/handlers/`
- Route Handler: `src/ai/backend/manager/sokovan/deployment/route/handlers/`
