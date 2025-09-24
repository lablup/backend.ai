from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional, Protocol

from ai.backend.common.bgtask.types import BgtaskStatus

from ...exception import ErrorCode
from .base import AbstractTaskHook, TaskContext


class BackgroundTaskObserver(Protocol):
    def observe_bgtask_started(self, *, task_name: str) -> None: ...
    def observe_bgtask_done(
        self, *, task_name: str, status: str, duration: float, error_code: Optional[ErrorCode]
    ) -> None: ...


class NopBackgroundTaskObserver:
    def observe_bgtask_started(self, *, task_name: str) -> None:
        pass

    def observe_bgtask_done(
        self, *, task_name: str, status: str, duration: float, error_code: Optional[ErrorCode]
    ) -> None:
        pass


class MetricObserverHook(AbstractTaskHook):
    """Hook for observing task metrics."""

    _observer: BackgroundTaskObserver

    def __init__(self, observer: BackgroundTaskObserver):
        self._observer = observer

    @asynccontextmanager
    async def apply(self, context: TaskContext) -> AsyncIterator[TaskContext]:
        # Pre-execution: start metric observation
        self._observer.observe_bgtask_started(task_name=context.task_name)
        start_time = time.perf_counter()

        try:
            yield context
        finally:
            # Post-execution: finish metric observation
            duration = time.perf_counter() - start_time

            # Get status and error code from result if available
            if context.result:
                status = context.result.status()
                error_code = context.result.error_code()
            else:
                # UNREACHABLE: If the task did not produce a result, we consider it UNKNOWN
                status = BgtaskStatus.UNKNOWN
                error_code = None

            self._observer.observe_bgtask_done(
                task_name=context.task_name,
                status=status,
                duration=duration,
                error_code=error_code,
            )
