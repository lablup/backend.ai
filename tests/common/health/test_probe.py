from __future__ import annotations

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.health import (
    AGENT,
    DATABASE,
    MANAGER,
    ComponentId,
    HealthChecker,
    HealthCheckerAlreadyRegistered,
    HealthCheckerNotFound,
    HealthCheckKey,
    HealthProbe,
)


@pytest.mark.asyncio
async def test_probe_register_checker(
    health_probe: HealthProbe,
    sample_health_check_key: HealthCheckKey,
    mock_healthy_checker: HealthChecker,
) -> None:
    """Test registering a health checker."""
    await health_probe.register(sample_health_check_key, mock_healthy_checker)

    # Verify registration by getting all registered checkers
    registered = await health_probe._get_all_registered()
    assert sample_health_check_key in registered
    assert registered[sample_health_check_key].checker == mock_healthy_checker
    assert registered[sample_health_check_key].status is None  # Not checked yet


@pytest.mark.asyncio
async def test_probe_register_duplicate_checker_raises_error(
    health_probe: HealthProbe,
    sample_health_check_key: HealthCheckKey,
    mock_healthy_checker: HealthChecker,
) -> None:
    """Test that registering a duplicate checker raises HealthCheckerAlreadyRegistered."""
    await health_probe.register(sample_health_check_key, mock_healthy_checker)

    # Try to register again with the same key
    with pytest.raises(HealthCheckerAlreadyRegistered) as exc_info:
        await health_probe.register(sample_health_check_key, mock_healthy_checker)

    # Verify the exception contains service_group and component_id
    assert sample_health_check_key.service_group in str(exc_info.value)
    assert sample_health_check_key.component_id in str(exc_info.value)


@pytest.mark.asyncio
async def test_probe_unregister_checker(
    health_probe: HealthProbe,
    sample_health_check_key: HealthCheckKey,
    mock_healthy_checker: HealthChecker,
) -> None:
    """Test unregistering a health checker."""
    await health_probe.register(sample_health_check_key, mock_healthy_checker)
    await health_probe.unregister(sample_health_check_key)

    # Verify unregistration
    registered = await health_probe._get_all_registered()
    assert sample_health_check_key not in registered


@pytest.mark.asyncio
async def test_probe_unregister_nonexistent_checker_raises_error(
    health_probe: HealthProbe,
    sample_health_check_key: HealthCheckKey,
) -> None:
    """Test that unregistering a non-existent checker raises HealthCheckerNotFound."""
    with pytest.raises(HealthCheckerNotFound) as exc_info:
        await health_probe.unregister(sample_health_check_key)

    # Verify the exception contains service_group and component_id
    assert sample_health_check_key.service_group in str(exc_info.value)
    assert sample_health_check_key.component_id in str(exc_info.value)


@pytest.mark.asyncio
async def test_probe_register_multiple_checkers(
    health_probe: HealthProbe,
    mock_healthy_checker: HealthChecker,
) -> None:
    """Test registering multiple health checkers."""
    key1 = HealthCheckKey(MANAGER, ComponentId("postgres"))
    key2 = HealthCheckKey(DATABASE, ComponentId("redis"))
    key3 = HealthCheckKey(AGENT, ComponentId("etcd"))

    await health_probe.register(key1, mock_healthy_checker)
    await health_probe.register(key2, mock_healthy_checker)
    await health_probe.register(key3, mock_healthy_checker)

    registered = await health_probe._get_all_registered()
    assert len(registered) == 3
    assert key1 in registered
    assert key2 in registered
    assert key3 in registered


@pytest.mark.asyncio
async def test_probe_check_healthy_checker(
    health_probe: HealthProbe,
    sample_health_check_key: HealthCheckKey,
    mock_healthy_checker: HealthChecker,
) -> None:
    """Test checking a healthy checker returns success status."""
    await health_probe.register(sample_health_check_key, mock_healthy_checker)

    results = await health_probe.check_all()

    assert sample_health_check_key in results
    status = results[sample_health_check_key]
    assert status.is_healthy is True
    assert status.error_message is None
    assert isinstance(status.last_checked_at, datetime)


@pytest.mark.asyncio
async def test_probe_check_unhealthy_checker(
    health_probe: HealthProbe,
    sample_health_check_key: HealthCheckKey,
    mock_unhealthy_checker: HealthChecker,
) -> None:
    """Test checking an unhealthy checker returns failure status."""
    await health_probe.register(sample_health_check_key, mock_unhealthy_checker)

    results = await health_probe.check_all()

    assert sample_health_check_key in results
    status = results[sample_health_check_key]
    assert status.is_healthy is False
    assert "Service unavailable" in status.error_message  # type: ignore
    assert isinstance(status.last_checked_at, datetime)


@pytest.mark.asyncio
async def test_probe_check_timeout_checker(
    health_probe: HealthProbe,
    sample_health_check_key: HealthCheckKey,
    mock_timeout_checker: HealthChecker,
) -> None:
    """Test checking a timeout checker returns timeout status."""
    await health_probe.register(sample_health_check_key, mock_timeout_checker)

    results = await health_probe.check_all()

    assert sample_health_check_key in results
    status = results[sample_health_check_key]
    assert status.is_healthy is False
    assert "timed out" in status.error_message  # type: ignore
    assert isinstance(status.last_checked_at, datetime)


@pytest.mark.asyncio
async def test_probe_check_all_updates_internal_status(
    health_probe: HealthProbe,
    sample_health_check_key: HealthCheckKey,
    mock_healthy_checker: HealthChecker,
) -> None:
    """Test that check_all() updates the internal status registry."""
    await health_probe.register(sample_health_check_key, mock_healthy_checker)

    # Initially, status should be None
    registered = await health_probe._get_all_registered()
    assert registered[sample_health_check_key].status is None

    # After check_all(), status should be updated
    await health_probe.check_all()

    registered = await health_probe._get_all_registered()
    assert registered[sample_health_check_key].status is not None
    assert registered[sample_health_check_key].status.is_healthy is True  # type: ignore


@pytest.mark.asyncio
async def test_probe_check_all_mixed_results(
    health_probe: HealthProbe,
    mock_healthy_checker: HealthChecker,
    mock_unhealthy_checker: HealthChecker,
) -> None:
    """Test check_all() with a mix of healthy and unhealthy checkers."""
    key1 = HealthCheckKey(MANAGER, ComponentId("postgres"))
    key2 = HealthCheckKey(DATABASE, ComponentId("redis"))

    await health_probe.register(key1, mock_healthy_checker)
    await health_probe.register(key2, mock_unhealthy_checker)

    results = await health_probe.check_all()

    assert len(results) == 2
    assert results[key1].is_healthy is True
    assert results[key2].is_healthy is False


@pytest.mark.asyncio
async def test_probe_check_all_continues_on_exception(
    health_probe: HealthProbe,
    mock_healthy_checker: HealthChecker,
    mock_unhealthy_checker: HealthChecker,
) -> None:
    """Test that check_all() continues checking even if some checkers fail."""
    key1 = HealthCheckKey(MANAGER, ComponentId("service1"))
    key2 = HealthCheckKey(MANAGER, ComponentId("service2"))
    key3 = HealthCheckKey(MANAGER, ComponentId("service3"))

    await health_probe.register(key1, mock_healthy_checker)
    await health_probe.register(key2, mock_unhealthy_checker)
    await health_probe.register(key3, mock_healthy_checker)

    results = await health_probe.check_all()

    # All three should be checked
    assert len(results) == 3
    assert results[key1].is_healthy is True
    assert results[key2].is_healthy is False
    assert results[key3].is_healthy is True


@pytest.mark.asyncio
async def test_probe_check_all_empty_registry(
    health_probe: HealthProbe,
) -> None:
    """Test check_all() with no registered checkers returns empty dict."""
    results = await health_probe.check_all()
    assert results == {}


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
    mock_healthy_checker: HealthChecker,
) -> None:
    """Test that the probe periodically checks registered checkers."""
    key = HealthCheckKey(MANAGER, ComponentId("test"))
    await health_probe.register(key, mock_healthy_checker)

    await health_probe.start()

    # Wait for at least 2-3 check intervals
    await asyncio.sleep(0.35)

    await health_probe.stop()

    # Verify that check_health was called multiple times
    mock = mock_healthy_checker.check_health  # type: ignore[attr-defined]
    assert isinstance(mock, AsyncMock)
    assert mock.call_count >= 2


@pytest.mark.asyncio
async def test_probe_dynamic_registration_during_loop(
    health_probe: HealthProbe,
    mock_healthy_checker: HealthChecker,
) -> None:
    """Test that checkers can be registered/unregistered while the loop is running."""
    key1 = HealthCheckKey(MANAGER, ComponentId("service1"))
    key2 = HealthCheckKey(MANAGER, ComponentId("service2"))

    # Start with one checker
    await health_probe.register(key1, mock_healthy_checker)
    await health_probe.start()

    # Wait for first check
    await asyncio.sleep(0.15)

    # Add another checker while running
    await health_probe.register(key2, mock_healthy_checker)

    # Wait for next check
    await asyncio.sleep(0.15)

    # Unregister first checker
    await health_probe.unregister(key1)

    # Wait for final check
    await asyncio.sleep(0.15)

    await health_probe.stop()

    # Verify final state
    registered = await health_probe._get_all_registered()
    assert key1 not in registered
    assert key2 in registered


@pytest.mark.asyncio
async def test_probe_get_health_response_all_healthy(
    health_probe: HealthProbe,
    mock_healthy_checker: HealthChecker,
) -> None:
    """Test get_health_response() when all components are healthy."""
    key1 = HealthCheckKey(MANAGER, ComponentId("postgres"))
    key2 = HealthCheckKey(DATABASE, ComponentId("redis"))

    await health_probe.register(key1, mock_healthy_checker)
    await health_probe.register(key2, mock_healthy_checker)

    # Run checks first
    await health_probe.check_all()

    response = await health_probe.get_health_response()

    assert response.overall_healthy is True
    assert len(response.connectivity_checks) == 2
    assert isinstance(response.timestamp, datetime)


@pytest.mark.asyncio
async def test_probe_get_health_response_some_unhealthy(
    health_probe: HealthProbe,
    mock_healthy_checker: HealthChecker,
    mock_unhealthy_checker: HealthChecker,
) -> None:
    """Test get_health_response() when some components are unhealthy."""
    key1 = HealthCheckKey(MANAGER, ComponentId("postgres"))
    key2 = HealthCheckKey(DATABASE, ComponentId("redis"))

    await health_probe.register(key1, mock_healthy_checker)
    await health_probe.register(key2, mock_unhealthy_checker)

    # Run checks first
    await health_probe.check_all()

    response = await health_probe.get_health_response()

    assert response.overall_healthy is False
    assert len(response.connectivity_checks) == 2


@pytest.mark.asyncio
async def test_probe_get_health_response_empty_registry(
    health_probe: HealthProbe,
) -> None:
    """Test get_health_response() with no registered checkers."""
    response = await health_probe.get_health_response()

    assert response.overall_healthy is True  # Default to True when empty
    assert len(response.connectivity_checks) == 0
    assert isinstance(response.timestamp, datetime)


@pytest.mark.asyncio
async def test_probe_get_health_response_excludes_unchecked(
    health_probe: HealthProbe,
    mock_healthy_checker: HealthChecker,
) -> None:
    """Test that get_health_response() excludes checkers that haven't been checked yet."""
    key = HealthCheckKey(MANAGER, ComponentId("postgres"))
    await health_probe.register(key, mock_healthy_checker)

    # Don't run check_all() - status should be None

    response = await health_probe.get_health_response()

    # Should not include the unchecked component
    assert len(response.connectivity_checks) == 0
    assert response.overall_healthy is True  # Default when no checked components


@pytest.mark.asyncio
async def test_probe_get_health_response_component_fields(
    health_probe: HealthProbe,
    mock_unhealthy_checker: HealthChecker,
) -> None:
    """Test that ComponentConnectivityStatus in response has correct fields."""
    key = HealthCheckKey(MANAGER, ComponentId("postgres"))
    await health_probe.register(key, mock_unhealthy_checker)

    await health_probe.check_all()
    response = await health_probe.get_health_response()

    assert len(response.connectivity_checks) == 1
    component = response.connectivity_checks[0]

    assert component.service_group == "manager"
    assert component.component_id == "postgres"
    assert component.is_healthy is False
    assert component.error_message is not None
    assert "Service unavailable" in component.error_message
    assert isinstance(component.last_checked_at, datetime)
