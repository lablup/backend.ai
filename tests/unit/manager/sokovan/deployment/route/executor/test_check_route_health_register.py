"""Unit tests for ``RouteExecutor.check_route_health`` AppProxy register hook.

The executor pushes a synchronous AppProxy register call only for
routes whose pre-execute ``health_status`` was not yet HEALTHY (first-
time ``→ HEALTHY`` transition). Already-HEALTHY routes do not trigger
a fresh push because they were already on AppProxy. Push failures are
swallowed so the health-check tick never raises out — the long-cycle
``AppProxySyncRouteHandler`` converges state.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from dateutil.tz import tzutc

from ai.backend.common.clients.valkey_client.valkey_schedule import (
    ReplicaHealthStatus as ValkeyReplicaHealthStatus,
)
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica import ReplicaID
from ai.backend.common.types import SessionId
from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.route.executor import RouteExecutor
from ai.backend.manager.sokovan.deployment.route.recorder.context import RouteRecorderContext
from ai.backend.manager.sokovan.deployment.route.types import RouteExecutionResult


def _route(health_status: RouteHealthStatus) -> RouteData:
    return RouteData(
        route_id=ReplicaID(uuid4()),
        deployment_id=DeploymentID(uuid4()),
        session_id=SessionId(uuid4()),
        status=RouteStatus.RUNNING,
        health_status=health_status,
        traffic_ratio=1.0,
        revision_id=DeploymentRevisionID(uuid4()),
        traffic_status=RouteTrafficStatus.ACTIVE,
        health_check=None,
        replica_host="10.0.0.1",
        replica_port=8000,
        created_at=datetime.now(tzutc()),
    )


def _healthy_status(route: RouteData) -> ValkeyReplicaHealthStatus:
    return ValkeyReplicaHealthStatus(
        replica_id=route.route_id,
        healthy=True,
        last_check=999,
    )


def _unhealthy_status(route: RouteData) -> ValkeyReplicaHealthStatus:
    return ValkeyReplicaHealthStatus(
        replica_id=route.route_id,
        healthy=False,
        last_check=999,
    )


class TestCheckRouteHealthRegister:
    """Register-on-first-HEALTHY behaviour inside ``check_route_health``."""

    async def test_first_time_healthy_triggers_register(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """RR-EXEC-HC-001: NOT_CHECKED → HEALTHY route is pushed to AppProxy."""
        not_yet_healthy = _route(RouteHealthStatus.NOT_CHECKED)
        mock_valkey_schedule.get_route_health_statuses_batch = AsyncMock(
            return_value={not_yet_healthy.route_id: _healthy_status(not_yet_healthy)}
        )

        with patch.object(
            route_executor,
            "register_routes_now",
            AsyncMock(return_value=RouteExecutionResult(successes=[], errors=[])),
        ) as mock_register:
            with RouteRecorderContext.scope("test", entity_ids=[not_yet_healthy.route_id]):
                result = await route_executor.check_route_health([not_yet_healthy])

        assert result.successes == [not_yet_healthy]
        mock_register.assert_awaited_once()
        await_args = mock_register.await_args
        assert await_args is not None
        pushed = await_args.args[0]
        assert [r.route_id for r in pushed] == [not_yet_healthy.route_id]

    async def test_already_healthy_route_is_skipped(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """RR-EXEC-HC-002: already-HEALTHY routes do not trigger fresh register."""
        already_healthy = _route(RouteHealthStatus.HEALTHY)
        mock_valkey_schedule.get_route_health_statuses_batch = AsyncMock(
            return_value={already_healthy.route_id: _healthy_status(already_healthy)}
        )

        with patch.object(route_executor, "register_routes_now") as mock_register:
            with RouteRecorderContext.scope("test", entity_ids=[already_healthy.route_id]):
                result = await route_executor.check_route_health([already_healthy])

        assert result.successes == [already_healthy]
        mock_register.assert_not_awaited()

    async def test_unhealthy_to_healthy_triggers_register(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """RR-EXEC-HC-003: UNHEALTHY → HEALTHY recovery is treated as fresh transition."""
        recovered = _route(RouteHealthStatus.UNHEALTHY)
        mock_valkey_schedule.get_route_health_statuses_batch = AsyncMock(
            return_value={recovered.route_id: _healthy_status(recovered)}
        )

        with patch.object(
            route_executor,
            "register_routes_now",
            AsyncMock(return_value=RouteExecutionResult(successes=[], errors=[])),
        ) as mock_register:
            with RouteRecorderContext.scope("test", entity_ids=[recovered.route_id]):
                await route_executor.check_route_health([recovered])

        mock_register.assert_awaited_once()

    async def test_no_successes_skips_register(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """RR-EXEC-HC-004: routes whose probe failed do not trigger register."""
        unhealthy_route = _route(RouteHealthStatus.UNHEALTHY)
        mock_valkey_schedule.get_route_health_statuses_batch = AsyncMock(
            return_value={unhealthy_route.route_id: _unhealthy_status(unhealthy_route)}
        )

        with patch.object(route_executor, "register_routes_now") as mock_register:
            with RouteRecorderContext.scope("test", entity_ids=[unhealthy_route.route_id]):
                result = await route_executor.check_route_health([unhealthy_route])

        assert result.successes == []
        assert len(result.errors) == 1
        mock_register.assert_not_awaited()

    async def test_register_failure_is_swallowed(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """RR-EXEC-HC-005: register_routes_now raising does not break the tick.

        The fallback long-cycle sync converges state, so the executor
        must not let the synchronous push raise out — a stuck health
        cycle would block all later observations.
        """
        not_yet_healthy = _route(RouteHealthStatus.NOT_CHECKED)
        mock_valkey_schedule.get_route_health_statuses_batch = AsyncMock(
            return_value={not_yet_healthy.route_id: _healthy_status(not_yet_healthy)}
        )

        with patch.object(
            route_executor,
            "register_routes_now",
            AsyncMock(side_effect=RuntimeError("boom")),
        ) as mock_register:
            with RouteRecorderContext.scope("test", entity_ids=[not_yet_healthy.route_id]):
                # Must not raise.
                result = await route_executor.check_route_health([not_yet_healthy])

        assert result.successes == [not_yet_healthy]
        mock_register.assert_awaited_once()
