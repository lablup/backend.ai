from __future__ import annotations

import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.health import (
    ComponentId,
    HealthChecker,
    HealthCheckKey,
    HealthProbe,
    HealthProbeOptions,
    ServiceGroup,
)

# Test-specific service group
TEST_SERVICE_GROUP: ServiceGroup = ServiceGroup("test")


@pytest.fixture
def sample_health_check_key() -> HealthCheckKey:
    """Sample HealthCheckKey for testing."""
    return HealthCheckKey(
        service_group=TEST_SERVICE_GROUP,
        component_id=ComponentId(str(uuid.uuid4())),
    )


@pytest.fixture
def mock_healthy_checker() -> HealthChecker:
    """Mock HealthChecker that always succeeds."""
    checker = AsyncMock(spec=HealthChecker)
    checker.check_health = AsyncMock(return_value=None)
    checker.timeout = 1.0
    return checker


@pytest.fixture
def mock_unhealthy_checker() -> HealthChecker:
    """Mock HealthChecker that always fails with an exception."""
    checker = AsyncMock(spec=HealthChecker)
    checker.check_health = AsyncMock(side_effect=RuntimeError("Service unavailable"))
    checker.timeout = 1.0
    return checker


@pytest.fixture
def mock_timeout_checker() -> HealthChecker:
    """Mock HealthChecker that times out."""
    checker = AsyncMock(spec=HealthChecker)

    async def slow_check() -> None:
        import asyncio

        await asyncio.sleep(10)  # Will timeout

    checker.check_health = slow_check
    checker.timeout = 0.1  # Very short timeout
    return checker


@pytest.fixture
async def health_probe() -> AsyncGenerator[HealthProbe, None]:
    """HealthProbe instance for testing."""
    probe = HealthProbe(HealthProbeOptions(check_interval=0.1))
    yield probe
    # Cleanup: stop the probe if it's running
    if probe._running:
        await probe.stop()
