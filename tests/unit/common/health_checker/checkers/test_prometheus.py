from __future__ import annotations

from datetime import UTC, datetime

import pytest

import ai.backend.common.metrics.safe as safe_mod
from ai.backend.common.health_checker.checkers.prometheus import PrometheusHealthChecker
from ai.backend.common.health_checker.types import CID_PROMETHEUS_METRICS, PROMETHEUS


@pytest.fixture(autouse=True)
def _reset_circuit_breaker(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset global circuit breaker state before each test and restore it after."""
    monkeypatch.setattr(safe_mod, "_metrics_disabled", False)
    monkeypatch.setattr(safe_mod, "_error_logged", False)
    monkeypatch.setattr(safe_mod, "_tripped_at", None)
    monkeypatch.setattr(safe_mod, "_trip_error_message", None)


class TestPrometheusHealthChecker:
    def test_target_service_group(self) -> None:
        checker = PrometheusHealthChecker()
        assert checker.target_service_group == PROMETHEUS

    def test_timeout_default(self) -> None:
        checker = PrometheusHealthChecker()
        assert checker.timeout == 1.0

    def test_timeout_custom(self) -> None:
        checker = PrometheusHealthChecker(timeout=5.0)
        assert checker.timeout == 5.0

    async def test_healthy_when_metrics_enabled(self) -> None:
        checker = PrometheusHealthChecker()
        result = await checker.check_service()
        status = result.results[CID_PROMETHEUS_METRICS]
        assert status.is_healthy is True
        assert status.error_message is None

    async def test_unhealthy_when_metrics_disabled(self) -> None:
        trip_time = datetime(2026, 3, 24, 12, 0, 0, tzinfo=UTC)
        safe_mod._metrics_disabled = True
        safe_mod._tripped_at = trip_time
        safe_mod._trip_error_message = "mmap slice assignment is wrong size"

        checker = PrometheusHealthChecker()
        result = await checker.check_service()
        status = result.results[CID_PROMETHEUS_METRICS]
        assert status.is_healthy is False
        assert status.error_message == "mmap slice assignment is wrong size"
        assert status.last_checked_at == trip_time
