"""Unit tests for ``EndpointRow.generate_route_info`` health filter.

Routes are exposed to the AppProxy / Traefik only when they are both
``traffic_status == ACTIVE`` and ``health_status in {HEALTHY, DEGRADED}``.
Routes still in ``NOT_CHECKED`` (initial-delay window) or ``UNHEALTHY``
must be suppressed so traffic does not hit a backend that has never
proven ready.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.endpoint.row import (
    _ROUTE_SERVING_HEALTH_STATUSES,
    EndpointRow,
)


def _make_route(
    *,
    health_status: RouteHealthStatus,
    traffic_status: RouteTrafficStatus = RouteTrafficStatus.ACTIVE,
    route_status: RouteStatus = RouteStatus.RUNNING,
    session_id: uuid.UUID | None = None,
    session_running: bool = True,
) -> MagicMock:
    """Build a mock RoutingRow with the given health/traffic combination."""
    route = MagicMock()
    route.id = uuid.uuid4()
    route.health_status = health_status
    route.traffic_status = traffic_status
    route.status = route_status
    sess_id = session_id if session_id is not None else uuid.uuid4()
    route.session = sess_id
    session_row = MagicMock()
    session_row.status = SessionStatus.RUNNING if session_running else SessionStatus.PENDING
    route.session_row = session_row
    return route


def _make_endpoint() -> MagicMock:
    """Mock stand-in for ``EndpointRow``.

    ``generate_route_info`` only reads ``self.id`` so a plain MagicMock
    avoids the SQLAlchemy InstrumentedAttribute setter that ``EndpointRow``
    inherits from ``Base``.
    """
    endpoint = MagicMock()
    endpoint.id = uuid.uuid4()
    endpoint.lifecycle_stage = EndpointLifecycle.READY
    return endpoint


class TestServingHealthStatusesConstant:
    def test_includes_healthy_and_degraded(self) -> None:
        assert RouteHealthStatus.HEALTHY in _ROUTE_SERVING_HEALTH_STATUSES
        assert RouteHealthStatus.DEGRADED in _ROUTE_SERVING_HEALTH_STATUSES

    def test_excludes_not_checked_and_unhealthy(self) -> None:
        assert RouteHealthStatus.NOT_CHECKED not in _ROUTE_SERVING_HEALTH_STATUSES
        assert RouteHealthStatus.UNHEALTHY not in _ROUTE_SERVING_HEALTH_STATUSES


async def _invoke(
    endpoint: MagicMock,
    routes: list[MagicMock],
) -> tuple[dict[str, list[dict[str, Any]]], list[uuid.UUID]]:
    """Invoke ``EndpointRow.generate_route_info`` against mocked DB
    helpers and return ``(result, session_ids_passed_to_kernel_loader)``.

    The kernel-loader receives whatever session-id list survived the
    filter, so the caller can assert on the filtered set without
    threading the mock object back out.
    """
    kernel_loader = AsyncMock(return_value=[])
    db_sess = AsyncMock()
    with (
        patch(
            "ai.backend.manager.models.routing.RoutingRow.list",
            new=AsyncMock(return_value=routes),
        ),
        patch(
            "ai.backend.manager.models.kernel.KernelRow.batch_load_main_kernels_by_session_id",
            new=kernel_loader,
        ),
    ):
        # Call as an unbound method against the MagicMock stand-in so the
        # SQLAlchemy InstrumentedAttribute on ``EndpointRow`` is bypassed.
        result = await EndpointRow.generate_route_info(endpoint, db_sess)
    assert kernel_loader.await_args is not None
    session_ids: list[uuid.UUID] = list(kernel_loader.await_args.args[1])
    return result, session_ids


class TestGenerateRouteInfoHealthFilter:
    @pytest.fixture
    def endpoint(self) -> MagicMock:
        return _make_endpoint()

    async def test_healthy_route_is_kept(self, endpoint: MagicMock) -> None:
        routes = [_make_route(health_status=RouteHealthStatus.HEALTHY)]
        result, session_ids = await _invoke(endpoint, routes)
        assert len(session_ids) == 1
        # No kernels returned → connection_info is empty.
        assert result == {}

    async def test_degraded_route_is_kept(self, endpoint: MagicMock) -> None:
        routes = [_make_route(health_status=RouteHealthStatus.DEGRADED)]
        _, session_ids = await _invoke(endpoint, routes)
        assert len(session_ids) == 1

    async def test_not_checked_route_is_dropped(self, endpoint: MagicMock) -> None:
        routes = [_make_route(health_status=RouteHealthStatus.NOT_CHECKED)]
        _, session_ids = await _invoke(endpoint, routes)
        assert session_ids == []

    async def test_unhealthy_route_is_dropped(self, endpoint: MagicMock) -> None:
        routes = [_make_route(health_status=RouteHealthStatus.UNHEALTHY)]
        _, session_ids = await _invoke(endpoint, routes)
        assert session_ids == []

    async def test_inactive_traffic_route_is_dropped_even_when_healthy(
        self, endpoint: MagicMock
    ) -> None:
        # Pre-existing INACTIVE behavior must still hold (e.g. blue-green
        # deploying revision that has not been promoted yet).
        routes = [
            _make_route(
                health_status=RouteHealthStatus.HEALTHY,
                traffic_status=RouteTrafficStatus.INACTIVE,
            ),
        ]
        _, session_ids = await _invoke(endpoint, routes)
        assert session_ids == []

    async def test_mixed_routes_only_serving_subset_is_kept(self, endpoint: MagicMock) -> None:
        healthy_session = uuid.uuid4()
        degraded_session = uuid.uuid4()
        routes = [
            _make_route(health_status=RouteHealthStatus.HEALTHY, session_id=healthy_session),
            _make_route(health_status=RouteHealthStatus.NOT_CHECKED),
            _make_route(health_status=RouteHealthStatus.DEGRADED, session_id=degraded_session),
            _make_route(health_status=RouteHealthStatus.UNHEALTHY),
        ]
        _, session_ids = await _invoke(endpoint, routes)
        assert set(session_ids) == {healthy_session, degraded_session}
