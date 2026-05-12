"""Unit tests for HealthCheckRouteHandler.

The handler resolves the per-revision ``ModelHealthCheck`` itself and
drops routes whose revision opted out of ``service.health_check`` before
forwarding the remainder to ``RouteExecutor.check_route_health``. The
register push for first-time HEALTHY transitions is exercised in the
executor tests; here we only verify the handler stays a thin shim plus
the hc-null skip.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from dateutil.tz import tzutc

from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.types import SessionId
from ai.backend.manager.data.deployment.types import RouteHealthStatus, RouteStatus
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.route.handlers.health_check import (
    HealthCheckRouteHandler,
)
from ai.backend.manager.sokovan.deployment.route.types import RouteExecutionResult


def _route(
    health_status: RouteHealthStatus,
    revision_id: DeploymentRevisionID | None = None,
) -> RouteData:
    return RouteData(
        route_id=uuid4(),
        deployment_id=DeploymentID(uuid4()),
        session_id=SessionId(uuid4()),
        status=RouteStatus.RUNNING,
        health_status=health_status,
        traffic_ratio=1.0,
        revision_id=revision_id or DeploymentRevisionID(uuid4()),
        replica_host="10.0.0.1",
        replica_port=8000,
        created_at=datetime.now(tzutc()),
    )


class TestHealthCheckHandler:
    """Tests for HealthCheckRouteHandler delegation and hc gating."""

    async def test_execute_forwards_routes_with_health_check(self) -> None:
        """Routes whose revision declares a probe reach the executor."""
        executor = AsyncMock()
        check_result = RouteExecutionResult(successes=[], errors=[], stale=[])
        executor.check_route_health = AsyncMock(return_value=check_result)
        repo = AsyncMock()
        route = _route(RouteHealthStatus.NOT_CHECKED)
        repo.fetch_health_check_configs = AsyncMock(
            return_value={route.revision_id: ModelHealthCheck(path="/health", initial_delay=720.0)}
        )
        handler = HealthCheckRouteHandler(executor, MagicMock(), repo)

        result = await handler.execute([route])

        executor.check_route_health.assert_awaited_once_with([route])
        repo.fetch_health_check_configs.assert_awaited_once_with({route.revision_id})
        assert result is check_result

    async def test_execute_skips_routes_without_health_check(self) -> None:
        """Routes whose revision opted out of probing never reach the executor."""
        executor = AsyncMock()
        executor.check_route_health = AsyncMock(
            return_value=RouteExecutionResult(successes=[], errors=[], stale=[])
        )
        repo = AsyncMock()
        route = _route(RouteHealthStatus.NOT_CHECKED)
        repo.fetch_health_check_configs = AsyncMock(return_value={route.revision_id: None})
        handler = HealthCheckRouteHandler(executor, MagicMock(), repo)

        result = await handler.execute([route])

        executor.check_route_health.assert_not_awaited()
        assert result.successes == []

    async def test_execute_empty_routes_is_noop(self) -> None:
        executor = AsyncMock()
        repo = AsyncMock()
        handler = HealthCheckRouteHandler(executor, MagicMock(), repo)

        result = await handler.execute([])

        repo.fetch_health_check_configs.assert_not_awaited()
        executor.check_route_health.assert_not_awaited()
        assert result.successes == []

    async def test_post_process_logs_only(self) -> None:
        """post_process is a logging shim — no executor call here."""
        executor = AsyncMock()
        repo = AsyncMock()
        event_producer = MagicMock()
        handler = HealthCheckRouteHandler(executor, event_producer, repo)
        success_route = _route(RouteHealthStatus.NOT_CHECKED)

        await handler.post_process(
            RouteExecutionResult(successes=[success_route], errors=[], stale=[])
        )

        assert executor.method_calls == []
        assert event_producer.method_calls == []
