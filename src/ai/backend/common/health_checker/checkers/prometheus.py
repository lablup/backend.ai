from __future__ import annotations

from datetime import UTC, datetime

from ai.backend.common.health_checker.abc import StaticServiceHealthChecker
from ai.backend.common.health_checker.types import (
    CID_PROMETHEUS_METRICS,
    PROMETHEUS,
    ComponentHealthStatus,
    ServiceGroup,
    ServiceHealth,
)


class PrometheusHealthChecker(StaticServiceHealthChecker):
    """Health checker for the Prometheus metric recording subsystem.

    Reports unhealthy when the metric circuit breaker has tripped
    (e.g., due to mmap corruption after OS sleep/wake).
    """

    _timeout: float

    def __init__(self, timeout: float = 1.0) -> None:
        self._timeout = timeout

    @property
    def target_service_group(self) -> ServiceGroup:
        return PROMETHEUS

    async def check_service(self) -> ServiceHealth:
        from ai.backend.common.metrics.safe import is_metrics_disabled, metrics_trip_info

        disabled = is_metrics_disabled()
        tripped_at, error_msg = metrics_trip_info()
        return ServiceHealth(
            results={
                CID_PROMETHEUS_METRICS: ComponentHealthStatus(
                    is_healthy=not disabled,
                    last_checked_at=tripped_at or datetime.now(UTC),
                    error_message=error_msg if disabled else None,
                ),
            }
        )

    @property
    def timeout(self) -> float:
        return self._timeout
