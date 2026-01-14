---
Author: HyeokJin Kim (hyeokjin@lablup.com)
Status: Draft
Created: 2025-01-15
Created-Version: 26.1.0
Target-Version: 26.1.0
Implemented-Version:
---

# Sokovan ObserverHandler Pattern

## Related Issues

- JIRA: [BA-3896](https://lablup.atlassian.net/browse/BA-3896)
- Parent Epic: [BA-3060](https://lablup.atlassian.net/browse/BA-3060) (Fair Share Scheduler)
- Related BEP: [BEP-1026: Fair Share Scheduler](BEP-1026-fair-share-scheduler.md)

## Motivation

The Sokovan scheduler currently has the `SessionLifecycleHandler` pattern for handling session state transitions. However, there are use cases that require **periodic observation and recording of data without state changes**.

### Use Cases

1. **Kernel usage snapshot**: Periodically record resource_usage of running kernels
2. **Usage aggregation**: Aggregate kernel records into user/project/domain buckets
3. **Fair share calculation**: Calculate fair_share_factor from aggregated usage
4. **Service discovery registration**: Register kernel state to service discovery (future)

### Problem

`SessionLifecycleHandler` requires state transitions (`success_status`, `failure_status`, `stale_status`). The above use cases:
- Do not change state
- Simply read data and record to external systems
- Do not affect session state even on failure

Therefore, a **separate handler pattern** is needed.

## Current Design

### SessionLifecycleHandler (Existing)

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

This pattern is centered on state transitions, making it unsuitable for observation-only tasks.

## Proposed Design

### ObserverHandler ABC

A handler that observes and records data without state transitions.

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

### Observer Registration in ScheduleCoordinator

**No separate Coordinator** - add observer registration to existing `ScheduleCoordinator`.

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

### Design Decisions

1. **No separate Coordinator**: Integrate into existing `ScheduleCoordinator`
2. **No LockID needed**: No state changes, so no distributed lock required. Single execution at a point in time is guaranteed by the scheduler task itself.
3. **No short timer**: No user interaction, so short timer polling is unnecessary

### Observer Implementation Examples

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

### Periodic Task Registration

```python
def _get_observer_tasks(self) -> list[SchedulerTaskSpec]:
    """Observer periodic tasks - no short timer (no user interaction)."""
    return [
        SchedulerTaskSpec(name="usage-record", interval=timedelta(minutes=5)),
        SchedulerTaskSpec(name="usage-aggregation", interval=timedelta(hours=1)),
        SchedulerTaskSpec(name="fair-share-calculation", interval=timedelta(hours=1)),
    ]
```

## Migration / Compatibility

### Backward Compatibility

- No impact on existing `SessionLifecycleHandler` pattern
- `ObserverHandler` is an additional pattern

### Breaking Changes

- None

## Implementation Plan

### Phase 1: Base Classes

1. Create `sokovan/scheduler/observers/__init__.py`
2. Create `sokovan/scheduler/observers/base.py` - `ObserverResult`, `ObserverHandler` ABC

### Phase 2: Observer Implementations

1. `usage_record.py` - `UsageRecordObserver`
2. `usage_aggregation.py` - `UsageAggregationObserver`
3. `fair_share_calculation.py` - `FairShareCalculationObserver`

### Phase 3: Coordinator Integration

1. Add `register_observer()`, `process_observer()` to `ScheduleCoordinator`
2. Register periodic tasks

## Open Questions

1. **Target fetching**: How to fetch data when `target_statuses` is empty set?
   - UsageAggregationObserver: kernel_usage_records within a specific period
   - FairShareCalculationObserver: usage_buckets within a specific period

2. **Error handling**: Stop entire batch on individual target failure vs continue?
   - Current design: Continue and log errors

3. **Interval configuration**: Hardcoded vs config file?
   - Can be moved to config file in the future

## References

- [BEP-1026: Fair Share Scheduler](BEP-1026-fair-share-scheduler.md)
- Sokovan Scheduler: `src/ai/backend/manager/sokovan/scheduler/`
- SessionLifecycleHandler: `sokovan/scheduler/handlers/base.py`
