from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.health_checker import (
    AGENT,
    DATABASE,
    MANAGER,
    AllServicesHealth,
    ComponentHealthStatus,
    ComponentId,
    HealthCheckerAlreadyRegistered,
    HealthProbe,
    ServiceGroup,
    ServiceHealth,
    ServiceHealthChecker,
)


def _make_checker(
    service_group: ServiceGroup,
    *,
    is_healthy: bool = True,
    error_message: str | None = None,
    component_id: str = "test-component",
    timeout: float = 1.0,
) -> ServiceHealthChecker:
    check_time = datetime.now(UTC)
    result = ServiceHealth(
        results={
            ComponentId(component_id): ComponentHealthStatus(
                is_healthy=is_healthy,
                last_checked_at=check_time,
                error_message=error_message,
            )
        }
    )
    checker = AsyncMock(spec=ServiceHealthChecker)
    checker.check_service = AsyncMock(return_value=result)
    checker.timeout = timeout
    checker.target_service_group = service_group
    return checker


async def test_register_readiness_appears_in_readyz(
    health_probe: HealthProbe,
    sample_service_group: ServiceGroup,
    mock_healthy_checker: ServiceHealthChecker,
) -> None:
    await health_probe.register_readiness(mock_healthy_checker)
    await health_probe.check_all()

    readiness = await health_probe.get_readiness_status()
    liveness = await health_probe.get_liveness_status()

    assert {c.service_group for c in readiness.connectivity_checks} == {sample_service_group}
    assert liveness.connectivity_checks == []


async def test_register_liveness_appears_in_both_livez_and_readyz(
    health_probe: HealthProbe,
    sample_service_group: ServiceGroup,
    mock_healthy_checker: ServiceHealthChecker,
) -> None:
    await health_probe.register_liveness(mock_healthy_checker)
    await health_probe.check_all()

    liveness = await health_probe.get_liveness_status()
    readiness = await health_probe.get_readiness_status()

    assert {c.service_group for c in liveness.connectivity_checks} == {sample_service_group}
    assert {c.service_group for c in readiness.connectivity_checks} == {sample_service_group}


async def test_register_same_checker_to_both_runs_check_once(
    health_probe: HealthProbe,
    mock_healthy_checker: ServiceHealthChecker,
) -> None:
    await health_probe.register_readiness(mock_healthy_checker)
    await health_probe.register_liveness(mock_healthy_checker)

    await health_probe.check_all()

    mock = mock_healthy_checker.check_service
    assert isinstance(mock, AsyncMock)
    assert mock.call_count == 1


async def test_register_duplicate_in_same_kind_raises(
    health_probe: HealthProbe,
    sample_service_group: ServiceGroup,
    mock_healthy_checker: ServiceHealthChecker,
) -> None:
    await health_probe.register_readiness(mock_healthy_checker)

    with pytest.raises(HealthCheckerAlreadyRegistered) as exc_info:
        await health_probe.register_readiness(mock_healthy_checker)

    assert str(sample_service_group) in str(exc_info.value)


async def test_register_different_instance_for_same_group_raises(
    health_probe: HealthProbe,
    sample_service_group: ServiceGroup,
    mock_healthy_checker: ServiceHealthChecker,
) -> None:
    await health_probe.register_readiness(mock_healthy_checker)

    other = _make_checker(sample_service_group)

    with pytest.raises(HealthCheckerAlreadyRegistered):
        await health_probe.register_liveness(other)


async def test_check_all_with_healthy_checker(
    health_probe: HealthProbe,
    sample_service_group: ServiceGroup,
    mock_healthy_checker: ServiceHealthChecker,
) -> None:
    await health_probe.register_readiness(mock_healthy_checker)

    all_results = await health_probe.check_all()

    assert isinstance(all_results, AllServicesHealth)
    assert sample_service_group in all_results.results
    for status in all_results.results[sample_service_group].results.values():
        assert status.is_healthy is True
        assert status.error_message is None


async def test_check_all_with_unhealthy_checker(
    health_probe: HealthProbe,
    sample_service_group: ServiceGroup,
    mock_unhealthy_checker: ServiceHealthChecker,
) -> None:
    await health_probe.register_readiness(mock_unhealthy_checker)

    all_results = await health_probe.check_all()

    for status in all_results.results[sample_service_group].results.values():
        assert status.is_healthy is False
        assert status.error_message is not None
        assert "Service unavailable" in status.error_message


async def test_check_all_timeout_returns_empty(
    health_probe: HealthProbe,
    sample_service_group: ServiceGroup,
    mock_timeout_checker: ServiceHealthChecker,
) -> None:
    await health_probe.register_readiness(mock_timeout_checker)

    all_results = await health_probe.check_all()

    assert all_results.results[sample_service_group].results == {}


async def test_check_all_mixed_kinds(
    health_probe: HealthProbe,
) -> None:
    manager_checker = _make_checker(MANAGER, is_healthy=True)
    database_checker = _make_checker(DATABASE, is_healthy=False, error_message="db down")
    agent_checker = _make_checker(AGENT, is_healthy=True)

    await health_probe.register_liveness(manager_checker)
    await health_probe.register_readiness(database_checker)
    await health_probe.register_readiness(agent_checker)

    all_results = await health_probe.check_all()

    assert set(all_results.results.keys()) == {MANAGER, DATABASE, AGENT}


async def test_check_all_empty_returns_empty(
    health_probe: HealthProbe,
) -> None:
    all_results = await health_probe.check_all()
    assert all_results.results == {}


async def test_start_and_stop(
    health_probe: HealthProbe,
) -> None:
    assert health_probe._running is False
    assert health_probe._loop_task is None

    await health_probe.start()
    assert health_probe._running is True
    assert health_probe._loop_task is not None  # type: ignore[unreachable]

    await health_probe.stop()
    assert health_probe._running is False
    assert health_probe._loop_task is None


async def test_periodic_check_invokes_checker(
    health_probe: HealthProbe,
    mock_healthy_checker: ServiceHealthChecker,
) -> None:
    await health_probe.register_readiness(mock_healthy_checker)
    await health_probe.start()
    await asyncio.sleep(0.35)
    await health_probe.stop()

    mock = mock_healthy_checker.check_service
    assert isinstance(mock, AsyncMock)
    assert mock.call_count >= 2


async def test_dynamic_registration_during_loop(
    health_probe: HealthProbe,
) -> None:
    manager_checker = _make_checker(MANAGER)
    database_checker = _make_checker(DATABASE)

    await health_probe.register_readiness(manager_checker)
    await health_probe.start()
    await asyncio.sleep(0.15)

    await health_probe.register_readiness(database_checker)
    await asyncio.sleep(0.25)

    await health_probe.stop()

    readiness = await health_probe.get_readiness_status()
    assert {c.service_group for c in readiness.connectivity_checks} == {MANAGER, DATABASE}


async def test_readiness_includes_liveness_registered(
    health_probe: HealthProbe,
) -> None:
    """Readiness response is a superset of liveness — if not alive, not ready."""
    readiness_checker = _make_checker(DATABASE)
    liveness_checker = _make_checker(MANAGER)

    await health_probe.register_readiness(readiness_checker)
    await health_probe.register_liveness(liveness_checker)
    await health_probe.check_all()

    readiness = await health_probe.get_readiness_status()
    liveness = await health_probe.get_liveness_status()

    assert {c.service_group for c in readiness.connectivity_checks} == {DATABASE, MANAGER}
    assert {c.service_group for c in liveness.connectivity_checks} == {MANAGER}


async def test_get_readiness_status_reflects_unhealthy(
    health_probe: HealthProbe,
) -> None:
    healthy = _make_checker(MANAGER, is_healthy=True)
    unhealthy = _make_checker(DATABASE, is_healthy=False, error_message="db down")

    await health_probe.register_readiness(healthy)
    await health_probe.register_readiness(unhealthy)
    await health_probe.check_all()

    response = await health_probe.get_readiness_status()
    assert response.overall_healthy is False
    assert len(response.connectivity_checks) == 2


async def test_liveness_excludes_readiness_only(
    health_probe: HealthProbe,
    mock_healthy_checker: ServiceHealthChecker,
) -> None:
    """A readiness-only checker must NOT appear in liveness."""
    await health_probe.register_readiness(mock_healthy_checker)
    await health_probe.check_all()

    liveness = await health_probe.get_liveness_status()

    assert liveness.overall_healthy is True
    assert liveness.connectivity_checks == []


async def test_get_connectivity_status_returns_union(
    health_probe: HealthProbe,
) -> None:
    readiness_checker = _make_checker(DATABASE)
    liveness_checker = _make_checker(MANAGER)

    await health_probe.register_readiness(readiness_checker)
    await health_probe.register_liveness(liveness_checker)
    await health_probe.check_all()

    response = await health_probe.get_connectivity_status()

    assert {c.service_group for c in response.connectivity_checks} == {DATABASE, MANAGER}
    assert response.overall_healthy is True


async def test_get_connectivity_status_excludes_unchecked(
    health_probe: HealthProbe,
    mock_healthy_checker: ServiceHealthChecker,
) -> None:
    await health_probe.register_readiness(mock_healthy_checker)

    response = await health_probe.get_connectivity_status()

    assert response.connectivity_checks == []
    assert response.overall_healthy is True


async def test_get_connectivity_status_component_fields(
    health_probe: HealthProbe,
    sample_service_group: ServiceGroup,
    mock_unhealthy_checker: ServiceHealthChecker,
) -> None:
    await health_probe.register_readiness(mock_unhealthy_checker)
    await health_probe.check_all()

    response = await health_probe.get_connectivity_status()

    assert len(response.connectivity_checks) == 1
    component = response.connectivity_checks[0]
    assert component.service_group == "test"
    assert component.component_id == "test-component"
    assert component.is_healthy is False
    assert component.error_message is not None
    assert "Service unavailable" in component.error_message
    assert isinstance(component.last_checked_at, datetime)
