from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from ai.backend.common.health_checker.types import MANAGER, ComponentId
from ai.backend.web.clients.endpoint_pool import (
    EndpointPoolSpec,
    HealthyEndpointPool,
    RoundRobinStrategy,
)
from ai.backend.web.clients.manager_pool import (
    MANAGER_ENDPOINTS,
    ManagerEndpointsHealthChecker,
    ManagerPoolGateHealthChecker,
)


def _make_spec() -> EndpointPoolSpec:
    return EndpointPoolSpec(
        probe_path="/livez",
        health_check_interval=3600.0,
        failure_threshold=1,
        recovery_timeout=60.0,
        probe_timeout=1.0,
    )


def _make_session() -> aiohttp.ClientSession:
    session = MagicMock(spec=aiohttp.ClientSession)
    session.close = AsyncMock()

    @asynccontextmanager
    async def fake_get(_path: str) -> AsyncIterator[MagicMock]:
        response = MagicMock()
        response.status = 200
        yield response

    session.get = MagicMock(side_effect=fake_get)
    return cast(aiohttp.ClientSession, session)


def _make_factory() -> Callable[[str], aiohttp.ClientSession]:
    return lambda _endpoint: _make_session()


@asynccontextmanager
async def _running_pool(pool: HealthyEndpointPool) -> AsyncIterator[HealthyEndpointPool]:
    try:
        yield pool
    finally:
        await pool.close()


async def _drive_unhealthy(pool: HealthyEndpointPool, endpoint: str) -> None:
    with pytest.raises(ConnectionError):
        async with pool.acquire_sticky(endpoint):
            raise ConnectionError("simulated")


class TestManagerPoolGateHealthChecker:
    async def test_targets_manager_service_group(self) -> None:
        pool = HealthyEndpointPool(
            endpoints=["http://m1"],
            spec=_make_spec(),
            strategy=RoundRobinStrategy(),
            probe_session_factory=_make_factory(),
        )
        async with _running_pool(pool):
            checker = ManagerPoolGateHealthChecker(pool)
            assert checker.target_service_group == MANAGER

    async def test_healthy_when_any_endpoint_is_up(self) -> None:
        pool = HealthyEndpointPool(
            endpoints=["http://m1", "http://m2"],
            spec=_make_spec(),
            strategy=RoundRobinStrategy(),
            probe_session_factory=_make_factory(),
        )
        async with _running_pool(pool):
            await _drive_unhealthy(pool, "http://m1")
            checker = ManagerPoolGateHealthChecker(pool)

            health = await checker.check_service()
            component = next(iter(health.results.values()))
            assert component.is_healthy is True
            assert component.error_message is None

    async def test_unhealthy_when_no_endpoint_is_up(self) -> None:
        pool = HealthyEndpointPool(
            endpoints=["http://m1", "http://m2"],
            spec=_make_spec(),
            strategy=RoundRobinStrategy(),
            probe_session_factory=_make_factory(),
        )
        async with _running_pool(pool):
            await _drive_unhealthy(pool, "http://m1")
            await _drive_unhealthy(pool, "http://m2")
            checker = ManagerPoolGateHealthChecker(pool)

            health = await checker.check_service()
            component = next(iter(health.results.values()))
            assert component.is_healthy is False
            assert component.error_message == "no healthy manager endpoint"


class TestManagerEndpointsHealthChecker:
    async def test_targets_manager_endpoints_service_group(self) -> None:
        pool = HealthyEndpointPool(
            endpoints=["http://m1"],
            spec=_make_spec(),
            strategy=RoundRobinStrategy(),
            probe_session_factory=_make_factory(),
        )
        async with _running_pool(pool):
            checker = ManagerEndpointsHealthChecker(pool)
            assert checker.target_service_group == MANAGER_ENDPOINTS

    async def test_emits_one_component_per_endpoint(self) -> None:
        pool = HealthyEndpointPool(
            endpoints=["http://m1", "http://m2", "http://m3"],
            spec=_make_spec(),
            strategy=RoundRobinStrategy(),
            probe_session_factory=_make_factory(),
        )
        async with _running_pool(pool):
            checker = ManagerEndpointsHealthChecker(pool)
            health = await checker.check_service()
            assert set(health.results) == {
                ComponentId("http://m1"),
                ComponentId("http://m2"),
                ComponentId("http://m3"),
            }
            assert all(component.is_healthy for component in health.results.values())
            assert all(component.error_message is None for component in health.results.values())

    async def test_reports_individual_unhealthy_endpoint(self) -> None:
        pool = HealthyEndpointPool(
            endpoints=["http://m1", "http://m2"],
            spec=_make_spec(),
            strategy=RoundRobinStrategy(),
            probe_session_factory=_make_factory(),
        )
        async with _running_pool(pool):
            await _drive_unhealthy(pool, "http://m1")
            checker = ManagerEndpointsHealthChecker(pool)
            health = await checker.check_service()
            assert health.results[ComponentId("http://m1")].is_healthy is False
            assert health.results[ComponentId("http://m1")].error_message == "endpoint unreachable"
            assert health.results[ComponentId("http://m2")].is_healthy is True
            assert health.results[ComponentId("http://m2")].error_message is None
