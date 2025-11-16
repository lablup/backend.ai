from __future__ import annotations

from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.health_checker import (
    ComponentHealthStatus,
    ComponentId,
    HealthProbe,
    HealthProbeOptions,
    ServiceGroup,
    ServiceHealth,
    ServiceHealthChecker,
)

# Test-specific service group
TEST_SERVICE_GROUP: ServiceGroup = ServiceGroup("test")


@pytest.fixture
def sample_service_group() -> ServiceGroup:
    """Sample ServiceGroup for testing."""
    return TEST_SERVICE_GROUP


@pytest.fixture
def mock_healthy_checker() -> ServiceHealthChecker:
    """Mock ServiceHealthChecker that always succeeds."""
    checker = AsyncMock(spec=ServiceHealthChecker)

    # Create healthy result
    check_time = datetime.now(timezone.utc)
    healthy_result = ServiceHealth(
        results={
            ComponentId("test-component"): ComponentHealthStatus(
                is_healthy=True,
                last_checked_at=check_time,
                error_message=None,
            )
        }
    )

    checker.check_service = AsyncMock(return_value=healthy_result)
    checker.timeout = 1.0
    checker.target_service_group = TEST_SERVICE_GROUP
    return checker


@pytest.fixture
def mock_unhealthy_checker() -> ServiceHealthChecker:
    """Mock ServiceHealthChecker that returns unhealthy status."""
    checker = AsyncMock(spec=ServiceHealthChecker)

    # Create unhealthy result
    check_time = datetime.now(timezone.utc)
    unhealthy_result = ServiceHealth(
        results={
            ComponentId("test-component"): ComponentHealthStatus(
                is_healthy=False,
                last_checked_at=check_time,
                error_message="Service unavailable",
            )
        }
    )

    checker.check_service = AsyncMock(return_value=unhealthy_result)
    checker.timeout = 1.0
    checker.target_service_group = TEST_SERVICE_GROUP
    return checker


@pytest.fixture
def mock_timeout_checker() -> ServiceHealthChecker:
    """Mock ServiceHealthChecker that times out."""
    checker = AsyncMock(spec=ServiceHealthChecker)

    async def slow_check() -> ServiceHealth:
        import asyncio

        await asyncio.sleep(10)  # Will timeout
        return ServiceHealth(results={})

    checker.check_service = slow_check
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
