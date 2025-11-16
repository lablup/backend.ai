from __future__ import annotations

from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.health_checker import (
    ComponentId,
    HealthChecker,
    HealthCheckResult,
    HealthCheckStatus,
    HealthProbe,
    HealthProbeOptions,
    ServiceGroup,
)

# Test-specific service group
TEST_SERVICE_GROUP: ServiceGroup = ServiceGroup("test")


@pytest.fixture
def sample_service_group() -> ServiceGroup:
    """Sample ServiceGroup for testing."""
    return TEST_SERVICE_GROUP


@pytest.fixture
def mock_healthy_checker() -> HealthChecker:
    """Mock HealthChecker that always succeeds."""
    checker = AsyncMock(spec=HealthChecker)

    # Create healthy result
    check_time = datetime.now(timezone.utc)
    healthy_result = HealthCheckResult(
        results={
            ComponentId("test-component"): HealthCheckStatus(
                is_healthy=True,
                last_checked_at=check_time,
                error_message=None,
            )
        }
    )

    checker.check_health = AsyncMock(return_value=healthy_result)
    checker.timeout = 1.0
    checker.target_service_group = TEST_SERVICE_GROUP
    return checker


@pytest.fixture
def mock_unhealthy_checker() -> HealthChecker:
    """Mock HealthChecker that returns unhealthy status."""
    checker = AsyncMock(spec=HealthChecker)

    # Create unhealthy result
    check_time = datetime.now(timezone.utc)
    unhealthy_result = HealthCheckResult(
        results={
            ComponentId("test-component"): HealthCheckStatus(
                is_healthy=False,
                last_checked_at=check_time,
                error_message="Service unavailable",
            )
        }
    )

    checker.check_health = AsyncMock(return_value=unhealthy_result)
    checker.timeout = 1.0
    checker.target_service_group = TEST_SERVICE_GROUP
    return checker


@pytest.fixture
def mock_timeout_checker() -> HealthChecker:
    """Mock HealthChecker that times out."""
    checker = AsyncMock(spec=HealthChecker)

    async def slow_check() -> HealthCheckResult:
        import asyncio

        await asyncio.sleep(10)  # Will timeout
        return HealthCheckResult(results={})

    checker.check_health = slow_check
    checker.timeout = 0.1  # Very short timeout
    checker.target_service_group = TEST_SERVICE_GROUP
    return checker


@pytest.fixture
async def health_probe() -> AsyncGenerator[HealthProbe, None]:
    """HealthProbe instance for testing."""
    probe = HealthProbe(HealthProbeOptions(check_interval=0.1))
    yield probe
    # Cleanup: stop the probe if it's running
    if probe._running:
        await probe.stop()
