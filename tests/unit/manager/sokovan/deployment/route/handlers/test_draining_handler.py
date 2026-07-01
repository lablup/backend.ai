"""Unit tests for DrainingRouteHandler.

The handler delegates the AppProxy traffic removal to
``RouteExecutor.drain_routes``; the unregister behavior itself is
exercised in the executor tests, so here we only verify the handler
stays a thin shim and declares the DRAINING → COOLING_DOWN stage.
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
    RouteSubStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.route.handlers.draining import (
    DrainingRouteHandler,
)
from ai.backend.manager.sokovan.deployment.route.types import RouteExecutionResult


def _draining_route() -> RouteData:
    return RouteData(
        route_id=ReplicaID(uuid4()),
        deployment_id=DeploymentID(uuid4()),
        session_id=SessionId(uuid4()),
        status=RouteStatus.TERMINATING,
        health_status=RouteHealthStatus.HEALTHY,
        traffic_ratio=1.0,
        revision_id=DeploymentRevisionID(uuid4()),
        traffic_status=RouteTrafficStatus.INACTIVE,
        health_check=None,
        termination_grace_period=30.0,
        replica_host="10.0.0.1",
        replica_port=8000,
        created_at=datetime.now(tzutc()),
        sub_status=RouteSubStatus.DRAINING,
    )


class TestDrainingHandler:
    """Tests for DrainingRouteHandler delegation and stage declaration."""

    async def test_delegates_to_executor_drain_routes(self) -> None:
        """RR-DRAIN-001: handler.execute is a thin pass-through to drain_routes."""
        executor = AsyncMock()
        drain_result = RouteExecutionResult(successes=[_draining_route()], errors=[])
        executor.drain_routes = AsyncMock(return_value=drain_result)
        event_producer = MagicMock()
        handler = DrainingRouteHandler(executor, event_producer)
        routes = [_draining_route(), _draining_route()]

        result = await handler.execute(routes)

        executor.drain_routes.assert_awaited_once_with(routes)
        assert result is drain_result

    def test_targets_draining_stage(self) -> None:
        """RR-DRAIN-002: handler picks up TERMINATING routes in the DRAINING stage."""
        target = DrainingRouteHandler.target_statuses()
        assert target.lifecycle == [RouteStatus.TERMINATING]
        assert target.sub_status == [RouteSubStatus.DRAINING]

    def test_success_transitions_to_cooling_down(self) -> None:
        """RR-DRAIN-003: drained routes advance to COOLING_DOWN, status unchanged."""
        transitions = DrainingRouteHandler.status_transitions()
        assert transitions.success is not None
        assert transitions.success.status is None
        assert transitions.success.sub_status == RouteSubStatus.COOLING_DOWN
        assert transitions.failure is None
        assert transitions.stale is None

    async def test_post_process_logs_summary_only(self) -> None:
        """RR-DRAIN-004: post_process is a logging shim — no executor call here."""
        executor = AsyncMock()
        event_producer = MagicMock()
        handler = DrainingRouteHandler(executor, event_producer)

        await handler.post_process(RouteExecutionResult(successes=[], errors=[]))

        assert executor.method_calls == []
        assert event_producer.method_calls == []
