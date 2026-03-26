"""Best-effort Prometheus metric wrappers.

Provides SafeCounter, SafeGauge, and SafeHistogram that wrap
prometheus_client metric types. On mmap corruption (ValueError from
corrupted multiprocess .db files after OS sleep/wake), all metric
recording is globally disabled so that metric failures never propagate
into business logic or trigger retries.
"""

from __future__ import annotations

import logging
import threading
from datetime import UTC, datetime
from typing import Any

from prometheus_client import Counter, Gauge, Histogram

from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# ---------------------------------------------------------------------------
# Global circuit-breaker state
# ---------------------------------------------------------------------------

_metrics_disabled: bool = False
_disable_lock = threading.Lock()
_error_logged: bool = False
_tripped_at: datetime | None = None
_trip_error_message: str | None = None


def is_metrics_disabled() -> bool:
    """Return True if metric recording has been disabled due to mmap error."""
    return _metrics_disabled


def metrics_trip_info() -> tuple[datetime | None, str | None]:
    """Return (tripped_at, error_message) for health check reporting."""
    return _tripped_at, _trip_error_message


def _trip(error: Exception) -> None:
    """Disable all metric recording globally. Logs a warning once."""
    global _metrics_disabled, _error_logged, _tripped_at, _trip_error_message
    with _disable_lock:
        if _metrics_disabled:
            return
        _metrics_disabled = True
        _tripped_at = datetime.now(UTC)
        _trip_error_message = str(error)
    if not _error_logged:
        _error_logged = True
        log.warning(
            "Prometheus metric recording disabled due to mmap error: {}",
            error,
        )


# ---------------------------------------------------------------------------
# Noop sentinel (returned when metrics are disabled)
# ---------------------------------------------------------------------------


class _NoopLabeledMetric:
    """Sentinel no-op returned when metrics are disabled."""

    __slots__ = ()

    def inc(self, amount: float = 1) -> None:
        pass

    def dec(self, amount: float = 1) -> None:
        pass

    def set(self, value: float) -> None:
        pass

    def observe(self, amount: float) -> None:
        pass


_NOOP_LABELED = _NoopLabeledMetric()


# ---------------------------------------------------------------------------
# Safe labeled metric wrapper
# ---------------------------------------------------------------------------


class SafeLabeledMetric:
    """Wraps a labeled prometheus metric child, catching ValueError."""

    __slots__ = ("_child",)

    def __init__(self, child: Any) -> None:
        self._child = child

    def inc(self, amount: float = 1) -> None:
        if _metrics_disabled:
            return
        try:
            self._child.inc(amount)
        except ValueError as e:
            _trip(e)

    def dec(self, amount: float = 1) -> None:
        if _metrics_disabled:
            return
        try:
            self._child.dec(amount)
        except ValueError as e:
            _trip(e)

    def set(self, value: float) -> None:
        if _metrics_disabled:
            return
        try:
            self._child.set(value)
        except ValueError as e:
            _trip(e)

    def observe(self, amount: float) -> None:
        if _metrics_disabled:
            return
        try:
            self._child.observe(amount)
        except ValueError as e:
            _trip(e)


# ---------------------------------------------------------------------------
# Safe metric types (drop-in replacements for prometheus_client types)
# ---------------------------------------------------------------------------


class SafeCounter(Counter):
    """Counter that becomes no-op on mmap corruption."""

    def labels(self, *args: Any, **kwargs: Any) -> Any:
        if _metrics_disabled:
            return _NOOP_LABELED
        try:
            return SafeLabeledMetric(super().labels(*args, **kwargs))
        except ValueError as e:
            _trip(e)
            return _NOOP_LABELED

    def inc(self, amount: float = 1, exemplar: dict[str, str] | None = None) -> None:
        if _metrics_disabled:
            return
        try:
            super().inc(amount, exemplar)
        except ValueError as e:
            _trip(e)


class SafeGauge(Gauge):
    """Gauge that becomes no-op on mmap corruption."""

    def labels(self, *args: Any, **kwargs: Any) -> Any:
        if _metrics_disabled:
            return _NOOP_LABELED
        try:
            return SafeLabeledMetric(super().labels(*args, **kwargs))
        except ValueError as e:
            _trip(e)
            return _NOOP_LABELED

    def inc(self, amount: float = 1) -> None:
        if _metrics_disabled:
            return
        try:
            super().inc(amount)
        except ValueError as e:
            _trip(e)

    def dec(self, amount: float = 1) -> None:
        if _metrics_disabled:
            return
        try:
            super().dec(amount)
        except ValueError as e:
            _trip(e)

    def set(self, value: float) -> None:
        if _metrics_disabled:
            return
        try:
            super().set(value)
        except ValueError as e:
            _trip(e)


class SafeHistogram(Histogram):
    """Histogram that becomes no-op on mmap corruption."""

    def labels(self, *args: Any, **kwargs: Any) -> Any:
        if _metrics_disabled:
            return _NOOP_LABELED
        try:
            return SafeLabeledMetric(super().labels(*args, **kwargs))
        except ValueError as e:
            _trip(e)
            return _NOOP_LABELED

    def observe(self, amount: float, exemplar: dict[str, str] | None = None) -> None:
        if _metrics_disabled:
            return
        try:
            super().observe(amount, exemplar)
        except ValueError as e:
            _trip(e)
