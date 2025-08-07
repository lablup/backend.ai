"""Scheduler metrics for monitoring session scheduling performance."""

import time
from contextlib import contextmanager
from typing import Iterator, Optional, Self

from prometheus_client import Counter, Histogram


class SchedulerOperationMetricObserver:
    """Metrics for high-level scheduler operations (schedule, start, terminate, etc.)."""

    _instance: Optional[Self] = None

    _operation_count: Counter
    _operation_duration_sec: Histogram

    def __init__(self) -> None:
        self._operation_count = Counter(
            name="backendai_scheduler_operation_count",
            documentation="Total number of scheduler operations",
            labelnames=["operation", "status"],
        )
        self._operation_duration_sec = Histogram(
            name="backendai_scheduler_operation_duration_sec",
            documentation="Duration of scheduler operations in seconds",
            labelnames=["operation", "status"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
        )

    @classmethod
    def instance(cls) -> Self:
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def observe_operation(
        self,
        *,
        operation: str,
        status: str,
        duration: float,
    ) -> None:
        """
        Record a scheduler operation.

        Args:
            operation: The operation type (e.g., 'schedule_all_scaling_groups', 'start_session', 'terminate_session')
            status: The operation status ('success' or 'failure')
            duration: The operation duration in seconds
        """
        self._operation_count.labels(operation=operation, status=status).inc()
        self._operation_duration_sec.labels(operation=operation, status=status).observe(duration)

    @contextmanager
    def measure_operation(self, operation: str) -> Iterator[None]:
        """
        Context manager to measure a scheduler operation.

        Args:
            operation: The operation type
        """
        start = time.perf_counter()
        status = "success"
        try:
            yield
        except Exception:
            status = "failure"
            raise
        finally:
            duration = time.perf_counter() - start
            self.observe_operation(operation=operation, status=status, duration=duration)


class SchedulerPhaseMetricObserver:
    """Metrics for scheduler execution phases (validation, sequencing, allocation)."""

    _instance: Optional[Self] = None

    _phase_count: Counter
    _phase_duration_sec: Histogram

    def __init__(self) -> None:
        self._phase_count = Counter(
            name="backendai_scheduler_phase_count",
            documentation="Total number of scheduler phase executions",
            labelnames=["scaling_group", "phase", "status"],
        )
        self._phase_duration_sec = Histogram(
            name="backendai_scheduler_phase_duration_sec",
            documentation="Duration of scheduler phase executions in seconds",
            labelnames=["scaling_group", "phase", "status"],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0],
        )

    @classmethod
    def instance(cls) -> Self:
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def observe_phase(
        self,
        *,
        scaling_group: str,
        phase: str,
        status: str,
        duration: float,
    ) -> None:
        """
        Record a scheduler phase execution.

        Args:
            scaling_group: The scaling group name
            phase: The scheduler phase (e.g., 'validation', 'sequencing_fifo', 'allocation')
            status: The phase status ('success' or 'failure')
            duration: The phase duration in seconds
        """
        self._phase_count.labels(scaling_group=scaling_group, phase=phase, status=status).inc()
        self._phase_duration_sec.labels(
            scaling_group=scaling_group, phase=phase, status=status
        ).observe(duration)

    @contextmanager
    def measure_phase(self, scaling_group: str, phase: str) -> Iterator[None]:
        """
        Context manager to measure a scheduler phase.

        Args:
            scaling_group: The scaling group name
            phase: The scheduler phase
        """
        start = time.perf_counter()
        status = "success"
        try:
            yield
        except Exception:
            status = "failure"
            raise
        finally:
            duration = time.perf_counter() - start
            self.observe_phase(
                scaling_group=scaling_group, phase=phase, status=status, duration=duration
            )
