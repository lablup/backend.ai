from __future__ import annotations

import pytest

from ai.backend.common.health_checker.checkers.prometheus import PrometheusHealthChecker
from ai.backend.common.health_checker.types import CID_PROMETHEUS_METRICS, PROMETHEUS


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

    async def test_healthy_when_metrics_enabled(self, mocker: "pytest.MonkeyPatch") -> None:
        mocker.patch(
            "ai.backend.common.health_checker.checkers.prometheus.is_metrics_disabled",
            return_value=False,
        )
        mocker.patch(
            "ai.backend.common.health_checker.checkers.prometheus.metrics_trip_info",
            return_value=(None, None),
        )
        checker = PrometheusHealthChecker()
        result = await checker.check_service()
        status = result.results[CID_PROMETHEUS_METRICS]
        assert status.is_healthy is True
        assert status.error_message is None

    async def test_unhealthy_when_metrics_disabled(self, mocker: "pytest.MonkeyPatch") -> None:
        from datetime import UTC, datetime

        trip_time = datetime(2026, 3, 24, 12, 0, 0, tzinfo=UTC)
        error_msg = "mmap slice assignment is wrong size"
        mocker.patch(
            "ai.backend.common.health_checker.checkers.prometheus.is_metrics_disabled",
            return_value=True,
        )
        mocker.patch(
            "ai.backend.common.health_checker.checkers.prometheus.metrics_trip_info",
            return_value=(trip_time, error_msg),
        )
        checker = PrometheusHealthChecker()
        result = await checker.check_service()
        status = result.results[CID_PROMETHEUS_METRICS]
        assert status.is_healthy is False
        assert status.error_message == error_msg
        assert status.last_checked_at == trip_time
