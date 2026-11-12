# Sokovan ObserverHandler 패턴

## 관련 이슈

- JIRA: [BA-3896](https://lablup.atlassian.net/browse/BA-3896)
- 상위 Epic: [BA-3060](https://lablup.atlassian.net/browse/BA-3060) (Fair Share Scheduler)
- 관련 BEP: [BEP-1026: Fair Share Scheduler](BEP-1026-fair-share-scheduler.md)

## 동기

Sokovan scheduler 는 현재 session 상태 전이를 처리하는 `SessionLifecycleHandler` 패턴을 갖고 있다. 그러나 상태 변경 없이 **데이터를 주기적으로 관찰하고 기록해야 하는** 사례가 있다.

### 사용 사례

1. **Kernel usage snapshot**: 실행 중인 kernel 의 resource_usage 를 주기적으로 기록한다
2. **사용량 집계**: kernel record 를 user/project/domain bucket 으로 집계한다
3. **fair share 계산**: 집계한 사용량으로 fair_share_factor 를 계산한다
4. **service discovery 등록**: kernel 상태를 service discovery 에 등록한다 (추후)

### 문제

`SessionLifecycleHandler` 는 상태 전이(`success_status`, `failure_status`, `stale_status`)를 요구한다. 위 사용 사례는 다음과 같은 특징이 있다:

- 상태를 변경하지 않는다
- 데이터를 읽어 외부 시스템에 기록하기만 한다
- 실패해도 session 상태에 영향을 주지 않는다

따라서 **별도의 handler 패턴**이 필요하다.

## 현재 설계

### SessionLifecycleHandler (기존)

```python
class SessionLifecycleHandler(ABC):
    """Handler for session state transitions."""

    @classmethod
    @abstractmethod
    def name(cls) -> str: ...

    @property
    @abstractmethod
    def target_statuses(self) -> frozenset[SessionStatus]: ...

    @property
    @abstractmethod
    def target_kernel_statuses(self) -> frozenset[KernelStatus]: ...

    @property
    @abstractmethod
    def success_status(self) -> SessionStatus: ...  # State to transition on success

    @property
    @abstractmethod
    def failure_status(self) -> SessionStatus: ...  # State to transition on failure

    @property
    @abstractmethod
    def stale_status(self) -> SessionStatus: ...    # State to transition on stale

    @abstractmethod
    async def execute(self, targets: Sequence[TTarget]) -> SessionExecutionResult: ...
```

이 패턴은 상태 전이를 중심으로 하므로 관찰만 하는 작업에 맞지 않는다.

## 제안 설계

### ObserverHandler ABC

상태 전이 없이 데이터를 관찰하고 기록하는 handler 이다.

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Sequence, TypeVar

from ai.backend.manager.models.kernel import KernelStatus
from ai.backend.manager.models.session import SessionStatus

TTarget = TypeVar("TTarget")


@dataclass
class ObserverResult:
    """Result of observer execution.

    Aligned with SessionExecutionResult field naming convention.
    Used for logging and Prometheus metrics collection.
    """
    success_count: int = 0
    failure_count: int = 0


class ObserverHandler(ABC, Generic[TTarget]):
    """Handler that observes and records data without state changes.

    Unlike SessionLifecycleHandler:
    - No success_status, failure_status, stale_status
    - Observation/recording only, no state changes
    - No LockID needed (no state changes)
    """

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Handler name."""
        raise NotImplementedError

    @property
    @abstractmethod
    def target_statuses(self) -> frozenset[SessionStatus]:
        """Target session statuses. Empty set means no filtering by session status."""
        raise NotImplementedError

    @property
    @abstractmethod
    def target_kernel_statuses(self) -> frozenset[KernelStatus]:
        """Target kernel statuses. Empty set means no filtering by kernel status."""
        raise NotImplementedError

    @abstractmethod
    async def execute(self, targets: Sequence[TTarget]) -> ObserverResult:
        """Execute observation on targets."""
        raise NotImplementedError

    async def post_process(self, result: ObserverResult) -> None:
        """Post-processing (optional). Default: no-op."""
        pass
```

### ScheduleCoordinator 의 observer 등록

**별도 Coordinator 없음**: 기존 `ScheduleCoordinator` 에 observer 등록을 추가한다.

```python
class ScheduleCoordinator:
    _observer_handlers: dict[str, ObserverHandler]

    def __init__(self, ...):
        ...
        self._observer_handlers = {}
        self._init_observers()

    def register_observer(self, handler: ObserverHandler) -> None:
        """Register an observer handler."""
        self._observer_handlers[handler.name()] = handler

    async def process_observer(self, handler_name: str) -> ObserverResult:
        """Execute observer (no lock needed - no state changes)."""
        handler = self._observer_handlers.get(handler_name)
        if handler is None:
            return ObserverResult()

        targets = await self._fetch_observer_targets(handler)
        if not targets:
            return ObserverResult()

        result = await handler.execute(targets)
        await handler.post_process(result)
        return result

    def _init_observers(self) -> None:
        """Initialize observer handlers."""
        self.register_observer(UsageRecordObserver(self._processors))
        self.register_observer(UsageAggregationObserver(self._processors))
        self.register_observer(FairShareCalculationObserver(self._processors))
```

### 설계 결정

1. **별도 Coordinator 없음**: 기존 `ScheduleCoordinator` 에 통합한다
2. **LockID 불필요**: 상태를 변경하지 않으므로 분산 잠금이 필요 없다. 한 시점에 한 번 실행되는 것은 scheduler task 자체가 보장한다
3. **short timer 없음**: 사용자 상호작용이 없으므로 short timer polling 이 필요 없다

### observer 구현 예

#### UsageRecordObserver

```python
class UsageRecordObserver(ObserverHandler[KernelRow]):
    """Record resource_usage of running kernels.

    Resource Usage = Allocated Resources × Time
    Note: measured_usage is NOT stored in DB - use Prometheus instead
    """

    @classmethod
    def name(cls) -> str:
        return "usage-record"

    @property
    def target_statuses(self) -> frozenset[SessionStatus]:
        return frozenset({SessionStatus.RUNNING})

    @property
    def target_kernel_statuses(self) -> frozenset[KernelStatus]:
        return frozenset({KernelStatus.RUNNING})

    async def execute(self, targets: Sequence[KernelRow]) -> ObserverResult:
        result = ObserverResult()

        for kernel in targets:
            try:
                await self._record_usage(kernel)
                result.success_count += 1
            except Exception:
                log.exception(f"Failed to record usage for kernel {kernel.id}")
                result.failure_count += 1

        return result
```

#### UsageAggregationObserver

```python
class UsageAggregationObserver(ObserverHandler[KernelUsageRecordRow]):
    """Aggregate kernel_usage_records into user/project/domain buckets."""

    @classmethod
    def name(cls) -> str:
        return "usage-aggregation"

    @property
    def target_statuses(self) -> frozenset[SessionStatus]:
        return frozenset()  # No filtering by session status

    @property
    def target_kernel_statuses(self) -> frozenset[KernelStatus]:
        return frozenset()  # No filtering by kernel status
```

#### FairShareCalculationObserver

```python
class FairShareCalculationObserver(ObserverHandler[UsageBucketData]):
    """Calculate fair_share_factor from usage buckets.

    Formula (Slurm compatible): F = 2^(-normalized_usage / weight)
    """

    @classmethod
    def name(cls) -> str:
        return "fair-share-calculation"
```

### 주기 task 등록

```python
def _get_observer_tasks(self) -> list[SchedulerTaskSpec]:
    """Observer periodic tasks - no short timer (no user interaction)."""
    return [
        SchedulerTaskSpec(name="usage-record", interval=timedelta(minutes=5)),
        SchedulerTaskSpec(name="usage-aggregation", interval=timedelta(hours=1)),
        SchedulerTaskSpec(name="fair-share-calculation", interval=timedelta(hours=1)),
    ]
```

## 이전 / 호환성

### 이전 버전 호환성

- 기존 `SessionLifecycleHandler` 패턴에 영향이 없다
- `ObserverHandler` 는 추가 패턴이다

### 호환성을 깨는 변경

- 없음

## 구현 계획

### 1단계: 기본 class

1. `sokovan/scheduler/observers/__init__.py` 를 생성한다
2. `sokovan/scheduler/observers/base.py` 를 생성한다. `ObserverResult`, `ObserverHandler` ABC 를 둔다

### 2단계: observer 구현

1. `usage_record.py`: `UsageRecordObserver`
2. `usage_aggregation.py`: `UsageAggregationObserver`
3. `fair_share_calculation.py`: `FairShareCalculationObserver`

### 3단계: Coordinator 통합

1. `ScheduleCoordinator` 에 `register_observer()`, `process_observer()` 를 추가한다
2. 주기 task 를 등록한다

## 열린 질문

1. **target 조회**: `target_statuses` 가 빈 집합일 때 데이터를 조회하는 방식에 대한 결정이 필요하다
   - UsageAggregationObserver: 특정 기간 안의 kernel_usage_records
   - FairShareCalculationObserver: 특정 기간 안의 usage_buckets

2. **에러 처리**: 개별 target 이 실패했을 때 batch 전체를 중단하는 방식과 계속하는 방식 중 선택이 필요하다
   - 현재 설계: 계속하고 에러를 기록한다

3. **interval 설정**: 하드코딩과 설정 파일 중 선택이 필요하다
   - 추후 설정 파일로 옮길 수 있다

## 참고

- [BEP-1026: Fair Share Scheduler](BEP-1026-fair-share-scheduler.md)
- Sokovan Scheduler: `src/ai/backend/manager/sokovan/scheduler/`
- SessionLifecycleHandler: `sokovan/scheduler/handlers/base.py`
