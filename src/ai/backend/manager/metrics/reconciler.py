"""Lifecycle metrics for monitoring generic entity lifecycle stages."""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Self

from ai.backend.common.metrics.safe import (
    SafeCounter as Counter,
)
from ai.backend.common.metrics.safe import (
    SafeHistogram as Histogram,
)


class ReconcilerMetricObserver:
    """Metrics for generic lifecycle stage steps (fetch, execute, apply, post_process)."""

    _instance: Self | None = None

    _step_count: Counter
    _step_duration_sec: Histogram
    _processed_count: Counter

    def __init__(self) -> None:
        self._step_count = Counter(
            name="backendai_reconciler_step_count",
            documentation="Total number of lifecycle stage step executions",
            labelnames=["kind", "handler", "step", "status"],
        )
        self._step_duration_sec = Histogram(
            name="backendai_reconciler_step_duration_sec",
            documentation="Duration of lifecycle stage step executions in seconds",
            labelnames=["kind", "handler", "step", "status"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
        )
        self._processed_count = Counter(
            name="backendai_reconciler_processed_count",
            documentation="Total number of lifecycle entities processed",
            labelnames=["kind", "handler", "result"],
        )

    @classmethod
    def instance(cls) -> Self:
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @contextmanager
    def measure(self, kind: str, handler: str, step: str) -> Iterator[None]:
        """Measure one lifecycle step, emitting step count and duration."""
        start = time.perf_counter()
        status = "success"
        try:
            yield
        except Exception:
            status = "failure"
            raise
        finally:
            duration = time.perf_counter() - start
            self._step_count.labels(kind=kind, handler=handler, step=step, status=status).inc()
            self._step_duration_sec.labels(
                kind=kind, handler=handler, step=step, status=status
            ).observe(duration)

    def observe_processed(self, kind: str, handler: str, processed: int, failed: int) -> None:
        """Emit processed/failed entity counts from a handler result."""
        if processed:
            self._processed_count.labels(kind=kind, handler=handler, result="success").inc(
                processed
            )
        if failed:
            self._processed_count.labels(kind=kind, handler=handler, result="failure").inc(failed)
