from __future__ import annotations

import asyncio
from datetime import datetime

import pytest

from ai.backend.common.health_checker import (
    AGENT,
    DATABASE,
    MANAGER,
    AllServicesHealth,
    HealthCheckerAlreadyRegistered,
    HealthCheckerNotFound,
    HealthProbe,
    ServiceGroup,
    ServiceHealthChecker,
)


@pytest.mark.asyncio
async def test_probe_register_checker(
    health_probe: HealthProbe,
    sample_service_group: ServiceGroup,
    mock_healthy_checker: ServiceHealthChecker,
) -> None:
    """Test registering a health checker."""
    await health_probe.register(mock_healthy_checker)

    # Verify registration by getting all registered checkers
    registered = await health_probe._get_all_registered()
    assert sample_service_group in registered
    assert registered[sample_service_group].checker == mock_healthy_checker
    assert registered[sample_service_group].result is None  # Not checked yet


@pytest.mark.asyncio
async def test_probe_register_duplicate_checker_raises_error(
    health_probe: HealthProbe,
    sample_service_group: ServiceGroup,
    mock_healthy_checker: ServiceHealthChecker,
) -> None:
    """Test that registering a duplicate checker raises HealthCheckerAlreadyRegistered."""
    await health_probe.register(mock_healthy_checker)

    # Try to register again with the same key
    with pytest.raises(HealthCheckerAlreadyRegistered) as exc_info:
        await health_probe.register(mock_healthy_checker)

    # Verify the exception contains service_group
    assert str(sample_service_group) in str(exc_info.value)


@pytest.mark.asyncio
async def test_probe_unregister_checker(
    health_probe: HealthProbe,
    sample_service_group: ServiceGroup,
    mock_healthy_checker: ServiceHealthChecker,
) -> None:
    """Test unregistering a health checker."""
    await health_probe.register(mock_healthy_checker)
    await health_probe.unregister(sample_service_group)

    # Verify unregistration
    registered = await health_probe._get_all_registered()
    assert sample_service_group not in registered


@pytest.mark.asyncio
async def test_probe_unregister_nonexistent_checker_raises_error(
    health_probe: HealthProbe,
    sample_service_group: ServiceGroup,
) -> None:
    """Test that unregistering a non-existent checker raises HealthCheckerNotFound."""
    with pytest.raises(HealthCheckerNotFound) as exc_info:
        await health_probe.unregister(sample_service_group)

    # Verify the exception contains service_group
    assert str(sample_service_group) in str(exc_info.value)


@pytest.mark.asyncio
async def test_probe_register_multiple_checkers(
    health_probe: HealthProbe,
    mock_healthy_checker: ServiceHealthChecker,
) -> None:
    """Test registering multiple health checkers."""
    from datetime import datetime, timezone
    from unittest.mock import AsyncMock

    from ai.backend.common.health_checker import ComponentHealthStatus, ComponentId, ServiceHealth

    # Create separate mock checkers with different service groups
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

    manager_checker = AsyncMock(spec=ServiceHealthChecker)
    manager_checker.check_service = AsyncMock(return_value=healthy_result)
    manager_checker.timeout = 1.0
    manager_checker.target_service_group = MANAGER

    database_checker = AsyncMock(spec=ServiceHealthChecker)
    database_checker.check_service = AsyncMock(return_value=healthy_result)
    database_checker.timeout = 1.0
    database_checker.target_service_group = DATABASE

    agent_checker = AsyncMock(spec=ServiceHealthChecker)
    agent_checker.check_service = AsyncMock(return_value=healthy_result)
    agent_checker.timeout = 1.0
    agent_checker.target_service_group = AGENT

    await health_probe.register(manager_checker)
    await health_probe.register(database_checker)
    await health_probe.register(agent_checker)

    registered = await health_probe._get_all_registered()
    assert len(registered) == 3
    assert MANAGER in registered
    assert DATABASE in registered
    assert AGENT in registered


@pytest.mark.asyncio
async def test_probe_check_healthy_checker(
    health_probe: HealthProbe,
    sample_service_group: ServiceGroup,
    mock_healthy_checker: ServiceHealthChecker,
) -> None:
    """Test checking a healthy checker returns success result."""
    await health_probe.register(mock_healthy_checker)

    all_results = await health_probe.check_all()

    assert isinstance(all_results, AllServicesHealth)
    assert sample_service_group in all_results.results
    result = all_results.results[sample_service_group]
    # Result contains component statuses
    assert len(result.results) > 0
    for component_status in result.results.values():
        assert component_status.is_healthy is True
        assert component_status.error_message is None
        assert isinstance(component_status.last_checked_at, datetime)


@pytest.mark.asyncio
async def test_probe_check_unhealthy_checker(
    health_probe: HealthProbe,
    sample_service_group: ServiceGroup,
    mock_unhealthy_checker: ServiceHealthChecker,
) -> None:
    """Test checking an unhealthy checker returns failure result."""
    await health_probe.register(mock_unhealthy_checker)

    all_results = await health_probe.check_all()

    assert isinstance(all_results, AllServicesHealth)
    assert sample_service_group in all_results.results
    result = all_results.results[sample_service_group]
    assert len(result.results) > 0
    for component_status in result.results.values():
        assert component_status.is_healthy is False
        assert "Service unavailable" in component_status.error_message  # type: ignore
        assert isinstance(component_status.last_checked_at, datetime)


@pytest.mark.asyncio
async def test_probe_check_timeout_checker(
    health_probe: HealthProbe,
    sample_service_group: ServiceGroup,
    mock_timeout_checker: ServiceHealthChecker,
) -> None:
    """Test checking a timeout checker returns empty result."""
    await health_probe.register(mock_timeout_checker)

    all_results = await health_probe.check_all()

    assert isinstance(all_results, AllServicesHealth)
    assert sample_service_group in all_results.results
    result = all_results.results[sample_service_group]
    # Timeout returns empty results
    assert len(result.results) == 0


@pytest.mark.asyncio
async def test_probe_check_all_updates_internal_status(
    health_probe: HealthProbe,
    sample_service_group: ServiceGroup,
    mock_healthy_checker: ServiceHealthChecker,
) -> None:
    """Test that check_all() updates the internal result registry."""
    await health_probe.register(mock_healthy_checker)

    # Initially, result should be None
    registered = await health_probe._get_all_registered()
    assert registered[sample_service_group].result is None

    # After check_all(), result should be updated
    await health_probe.check_all()

    registered = await health_probe._get_all_registered()
    assert registered[sample_service_group].result is not None


@pytest.mark.asyncio
async def test_probe_check_all_mixed_results(
    health_probe: HealthProbe,
    mock_healthy_checker: ServiceHealthChecker,
    mock_unhealthy_checker: ServiceHealthChecker,
) -> None:
    """Test check_all() with a mix of healthy and unhealthy checkers."""
    from datetime import datetime, timezone
    from unittest.mock import AsyncMock

    from ai.backend.common.health_checker import ComponentHealthStatus, ComponentId, ServiceHealth

    # Create separate checkers with different service groups
    check_time = datetime.now(timezone.utc)

    # Healthy checker for MANAGER
    healthy_result = ServiceHealth(
        results={
            ComponentId("test-component"): ComponentHealthStatus(
                is_healthy=True,
                last_checked_at=check_time,
                error_message=None,
            )
        }
    )
    manager_checker = AsyncMock(spec=ServiceHealthChecker)
    manager_checker.check_service = AsyncMock(return_value=healthy_result)
    manager_checker.timeout = 1.0
    manager_checker.target_service_group = MANAGER

    # Unhealthy checker for DATABASE
    unhealthy_result = ServiceHealth(
        results={
            ComponentId("test-component"): ComponentHealthStatus(
                is_healthy=False,
                last_checked_at=check_time,
                error_message="Service unavailable",
            )
        }
    )
    database_checker = AsyncMock(spec=ServiceHealthChecker)
    database_checker.check_service = AsyncMock(return_value=unhealthy_result)
    database_checker.timeout = 1.0
    database_checker.target_service_group = DATABASE

    await health_probe.register(manager_checker)
    await health_probe.register(database_checker)

    all_results = await health_probe.check_all()

    assert isinstance(all_results, AllServicesHealth)
    assert len(all_results.results) == 2
    # Check healthy result
    manager_result = all_results.results[MANAGER]
    assert all(s.is_healthy for s in manager_result.results.values())
    # Check unhealthy result
    database_result = all_results.results[DATABASE]
    assert all(not s.is_healthy for s in database_result.results.values())


@pytest.mark.asyncio
async def test_probe_check_all_continues_on_exception(
    health_probe: HealthProbe,
    mock_healthy_checker: ServiceHealthChecker,
    mock_unhealthy_checker: ServiceHealthChecker,
) -> None:
    """Test that check_all() continues checking even if some checkers fail."""
    from datetime import datetime, timezone
    from unittest.mock import AsyncMock

    from ai.backend.common.health_checker import ComponentHealthStatus, ComponentId, ServiceHealth

    # Create separate checkers with different service groups
    check_time = datetime.now(timezone.utc)

    # Healthy result
    healthy_result = ServiceHealth(
        results={
            ComponentId("test-component"): ComponentHealthStatus(
                is_healthy=True,
                last_checked_at=check_time,
                error_message=None,
            )
        }
    )

    # Unhealthy result
    unhealthy_result = ServiceHealth(
        results={
            ComponentId("test-component"): ComponentHealthStatus(
                is_healthy=False,
                last_checked_at=check_time,
                error_message="Service unavailable",
            )
        }
    )

    manager_checker = AsyncMock(spec=ServiceHealthChecker)
    manager_checker.check_service = AsyncMock(return_value=healthy_result)
    manager_checker.timeout = 1.0
    manager_checker.target_service_group = MANAGER

    database_checker = AsyncMock(spec=ServiceHealthChecker)
    database_checker.check_service = AsyncMock(return_value=unhealthy_result)
    database_checker.timeout = 1.0
    database_checker.target_service_group = DATABASE

    agent_checker = AsyncMock(spec=ServiceHealthChecker)
    agent_checker.check_service = AsyncMock(return_value=healthy_result)
    agent_checker.timeout = 1.0
    agent_checker.target_service_group = AGENT

    await health_probe.register(manager_checker)
    await health_probe.register(database_checker)
    await health_probe.register(agent_checker)

    all_results = await health_probe.check_all()

    # All three should be checked
    assert isinstance(all_results, AllServicesHealth)
    assert len(all_results.results) == 3
    assert MANAGER in all_results.results
    assert DATABASE in all_results.results
    assert AGENT in all_results.results


@pytest.mark.asyncio
async def test_probe_check_all_empty_registry(
    health_probe: HealthProbe,
) -> None:
    """Test check_all() with no registered checkers returns empty results."""
    all_results = await health_probe.check_all()
    assert isinstance(all_results, AllServicesHealth)
    assert all_results.results == {}


@pytest.mark.asyncio
async def test_probe_start_and_stop(
    health_probe: HealthProbe,
) -> None:
    """Test starting and stopping the health probe loop."""
    assert health_probe._running is False
    assert health_probe._loop_task is None

    await health_probe.start()
    assert health_probe._running is True
    assert health_probe._loop_task is not None

    await health_probe.stop()
    assert health_probe._running is False
    assert health_probe._loop_task is None


@pytest.mark.asyncio
async def test_probe_start_already_running(
    health_probe: HealthProbe,
) -> None:
    """Test that starting an already running probe logs a warning."""
    await health_probe.start()

    # Start again - should log warning but not crash
    await health_probe.start()

    # Should still be running
    assert health_probe._running is True

    await health_probe.stop()


@pytest.mark.asyncio
async def test_probe_stop_not_running(
    health_probe: HealthProbe,
) -> None:
    """Test that stopping a non-running probe logs a warning."""
    assert health_probe._running is False

    # Stop without starting - should log warning but not crash
    await health_probe.stop()

    # Should still be not running
    assert health_probe._running is False


@pytest.mark.asyncio
async def test_probe_periodic_check(
    health_probe: HealthProbe,
    mock_healthy_checker: ServiceHealthChecker,
) -> None:
    """Test that the probe periodically checks registered checkers."""
    await health_probe.register(mock_healthy_checker)

    await health_probe.start()

    # Wait for at least 2-3 check intervals
    await asyncio.sleep(0.35)

    await health_probe.stop()

    # Verify that check_service was called multiple times
    from unittest.mock import AsyncMock

    mock = mock_healthy_checker.check_service  # type: ignore[attr-defined]
    assert isinstance(mock, AsyncMock)
    assert mock.call_count >= 2


@pytest.mark.asyncio
async def test_probe_dynamic_registration_during_loop(
    health_probe: HealthProbe,
    mock_healthy_checker: ServiceHealthChecker,
) -> None:
    """Test that checkers can be registered/unregistered while the loop is running."""
    from datetime import datetime, timezone
    from unittest.mock import AsyncMock

    from ai.backend.common.health_checker import ComponentHealthStatus, ComponentId, ServiceHealth

    # Create separate checkers with different service groups
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

    manager_checker = AsyncMock(spec=ServiceHealthChecker)
    manager_checker.check_service = AsyncMock(return_value=healthy_result)
    manager_checker.timeout = 1.0
    manager_checker.target_service_group = MANAGER

    database_checker = AsyncMock(spec=ServiceHealthChecker)
    database_checker.check_service = AsyncMock(return_value=healthy_result)
    database_checker.timeout = 1.0
    database_checker.target_service_group = DATABASE

    # Start with one checker
    await health_probe.register(manager_checker)
    await health_probe.start()

    # Wait for first check
    await asyncio.sleep(0.15)

    # Add another checker while running
    await health_probe.register(database_checker)

    # Wait for next check
    await asyncio.sleep(0.15)

    # Unregister first checker
    await health_probe.unregister(MANAGER)

    # Wait for final check
    await asyncio.sleep(0.15)

    await health_probe.stop()

    # Verify final state
    registered = await health_probe._get_all_registered()
    assert MANAGER not in registered
    assert DATABASE in registered


@pytest.mark.asyncio
async def test_probe_get_connectivity_status_all_healthy(
    health_probe: HealthProbe,
    mock_healthy_checker: ServiceHealthChecker,
) -> None:
    """Test get_connectivity_status() when all components are healthy."""
    from datetime import datetime, timezone
    from unittest.mock import AsyncMock

    from ai.backend.common.health_checker import ComponentHealthStatus, ComponentId, ServiceHealth

    # Create separate checkers with different service groups
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

    manager_checker = AsyncMock(spec=ServiceHealthChecker)
    manager_checker.check_service = AsyncMock(return_value=healthy_result)
    manager_checker.timeout = 1.0
    manager_checker.target_service_group = MANAGER

    database_checker = AsyncMock(spec=ServiceHealthChecker)
    database_checker.check_service = AsyncMock(return_value=healthy_result)
    database_checker.timeout = 1.0
    database_checker.target_service_group = DATABASE

    await health_probe.register(manager_checker)
    await health_probe.register(database_checker)

    # Run checks first
    await health_probe.check_all()

    response = await health_probe.get_connectivity_status()

    assert response.overall_healthy is True
    # Should have 2 components (one from each service group's checker)
    assert len(response.connectivity_checks) == 2
    assert isinstance(response.timestamp, datetime)


@pytest.mark.asyncio
async def test_probe_get_connectivity_status_some_unhealthy(
    health_probe: HealthProbe,
    mock_healthy_checker: ServiceHealthChecker,
    mock_unhealthy_checker: ServiceHealthChecker,
) -> None:
    """Test get_connectivity_status() when some components are unhealthy."""
    from datetime import datetime, timezone
    from unittest.mock import AsyncMock

    from ai.backend.common.health_checker import ComponentHealthStatus, ComponentId, ServiceHealth

    # Create separate checkers with different service groups
    check_time = datetime.now(timezone.utc)

    # Healthy result
    healthy_result = ServiceHealth(
        results={
            ComponentId("test-component"): ComponentHealthStatus(
                is_healthy=True,
                last_checked_at=check_time,
                error_message=None,
            )
        }
    )

    # Unhealthy result
    unhealthy_result = ServiceHealth(
        results={
            ComponentId("test-component"): ComponentHealthStatus(
                is_healthy=False,
                last_checked_at=check_time,
                error_message="Service unavailable",
            )
        }
    )

    manager_checker = AsyncMock(spec=ServiceHealthChecker)
    manager_checker.check_service = AsyncMock(return_value=healthy_result)
    manager_checker.timeout = 1.0
    manager_checker.target_service_group = MANAGER

    database_checker = AsyncMock(spec=ServiceHealthChecker)
    database_checker.check_service = AsyncMock(return_value=unhealthy_result)
    database_checker.timeout = 1.0
    database_checker.target_service_group = DATABASE

    await health_probe.register(manager_checker)
    await health_probe.register(database_checker)

    # Run checks first
    await health_probe.check_all()

    response = await health_probe.get_connectivity_status()

    assert response.overall_healthy is False
    assert len(response.connectivity_checks) == 2


@pytest.mark.asyncio
async def test_probe_get_connectivity_status_empty_registry(
    health_probe: HealthProbe,
) -> None:
    """Test get_connectivity_status() with no registered checkers."""
    response = await health_probe.get_connectivity_status()

    assert response.overall_healthy is True  # Default to True when empty
    assert len(response.connectivity_checks) == 0
    assert isinstance(response.timestamp, datetime)


@pytest.mark.asyncio
async def test_probe_get_connectivity_status_excludes_unchecked(
    health_probe: HealthProbe,
    mock_healthy_checker: ServiceHealthChecker,
) -> None:
    """Test that get_connectivity_status() excludes checkers that haven't been checked yet."""
    await health_probe.register(mock_healthy_checker)

    # Don't run check_all() - result should be None

    response = await health_probe.get_connectivity_status()

    # Should not include the unchecked component
    assert len(response.connectivity_checks) == 0
    assert response.overall_healthy is True  # Default when no checked components


@pytest.mark.asyncio
async def test_probe_get_connectivity_status_component_fields(
    health_probe: HealthProbe,
    sample_service_group: ServiceGroup,
    mock_unhealthy_checker: ServiceHealthChecker,
) -> None:
    """Test that ComponentConnectivityStatus in response has correct fields."""
    await health_probe.register(mock_unhealthy_checker)

    await health_probe.check_all()
    response = await health_probe.get_connectivity_status()

    assert len(response.connectivity_checks) == 1
    component = response.connectivity_checks[0]

    assert component.service_group == "test"  # From mock fixture (TEST_SERVICE_GROUP)
    assert component.component_id == "test-component"  # From mock fixture
    assert component.is_healthy is False
    assert component.error_message is not None
    assert "Service unavailable" in component.error_message
    assert isinstance(component.last_checked_at, datetime)
