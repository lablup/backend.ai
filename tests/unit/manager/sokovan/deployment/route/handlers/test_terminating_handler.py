"""Unit tests for TerminatingRouteHandler.

The handler delegates termination — including the AppProxy drain step
that must precede kernel destruction — to ``RouteExecutor.terminate_routes``.
The drain ordering itself is exercised in the executor tests; here we
only verify the handler stays a thin shim.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from dateutil.tz import tzutc

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.types import SessionId
from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.route.handlers.terminating import (
    TerminatingRouteHandler,
)
from ai.backend.manager.sokovan.deployment.route.types import RouteExecutionResult


def _terminating_route() -> RouteData:
    return RouteData(
        route_id=uuid4(),
        deployment_id=DeploymentID(uuid4()),
        session_id=SessionId(uuid4()),
        status=RouteStatus.TERMINATING,
        health_status=RouteHealthStatus.HEALTHY,
        traffic_ratio=1.0,
        revision_id=DeploymentRevisionID(uuid4()),
        traffic_status=RouteTrafficStatus.INACTIVE,
        replica_host="10.0.0.1",
        replica_port=8000,
        created_at=datetime.now(tzutc()),
    )


class TestTerminatingExecute:
    """Tests for TerminatingRouteHandler.execute delegation."""

    async def test_delegates_to_executor_terminate_routes(self) -> None:
        """RR-TERM-001: handler.execute is a thin pass-through to terminate_routes."""
        executor = AsyncMock()
        terminate_result = RouteExecutionResult(successes=[_terminating_route()], errors=[])
        executor.terminate_routes = AsyncMock(return_value=terminate_result)
        event_producer = MagicMock()
        handler = TerminatingRouteHandler(executor, event_producer)
        routes = [_terminating_route(), _terminating_route()]

        result = await handler.execute(routes)

        executor.terminate_routes.assert_awaited_once_with(routes)
        assert result is terminate_result

    async def test_post_process_logs_summary_only(self) -> None:
        """RR-TERM-002: post_process is a logging shim — no executor call here."""
        executor = AsyncMock()
        event_producer = MagicMock()
        handler = TerminatingRouteHandler(executor, event_producer)

        await handler.post_process(RouteExecutionResult(successes=[], errors=[]))

        assert executor.method_calls == []
        assert event_producer.method_calls == []
