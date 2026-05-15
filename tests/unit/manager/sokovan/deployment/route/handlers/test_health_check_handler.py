"""Unit tests for HealthCheckRouteHandler.

The handler delegates the health-check work — including the AppProxy
register push for first-time HEALTHY transitions — to
``RouteExecutor.check_route_health``. The push behaviour itself is
exercised in the executor tests; here we only verify the handler stays
a thin shim.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from dateutil.tz import tzutc

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
from ai.backend.manager.sokovan.deployment.route.handlers.health_check import (
    HealthCheckRouteHandler,
)
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


class TestHealthCheckHandler:
    """Tests for HealthCheckRouteHandler delegation."""

    async def test_execute_delegates_to_executor_check_route_health(self) -> None:
        """RR-HC-001: handler.execute is a thin pass-through to check_route_health."""
        executor = AsyncMock()
        check_result = RouteExecutionResult(successes=[], errors=[], stale=[])
        executor.check_route_health = AsyncMock(return_value=check_result)
        event_producer = MagicMock()
        handler = HealthCheckRouteHandler(executor, event_producer)
        routes = [_route(RouteHealthStatus.NOT_CHECKED)]

        result = await handler.execute(routes)

        executor.check_route_health.assert_awaited_once_with(routes)
        assert result is check_result

    async def test_post_process_logs_only(self) -> None:
        """RR-HC-002: post_process is a logging shim — no executor call here.

        The register push for first-time HEALTHY transitions belongs to
        ``RouteExecutor.check_route_health`` itself; ``post_process``
        intentionally does no work whose failure must be tolerated.
        """
        executor = AsyncMock()
        event_producer = MagicMock()
        handler = HealthCheckRouteHandler(executor, event_producer)
        success_route = _route(RouteHealthStatus.NOT_CHECKED)

        await handler.post_process(
            RouteExecutionResult(successes=[success_route], errors=[], stale=[])
        )

        # Nothing besides logging.
        assert executor.method_calls == []
        assert event_producer.method_calls == []
