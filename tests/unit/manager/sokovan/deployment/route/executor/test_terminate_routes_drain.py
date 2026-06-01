"""Unit tests for ``RouteExecutor.terminate_routes`` drain ordering.

The executor must call ``unregister_routes_now`` before
``mark_sessions_for_termination`` so no fresh request lands on a kernel
that is about to die. Failures from unregister are logged but do not
block kernel termination — the long-cycle ``AppProxySyncRouteHandler``
keeps state convergent for any leftover drift, and a stuck TERMINATING
row would block all later cleanup.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
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
from ai.backend.manager.sokovan.deployment.route.executor import RouteExecutor
from ai.backend.manager.sokovan.deployment.route.recorder.context import RouteRecorderContext
from ai.backend.manager.sokovan.deployment.route.types import (
    RouteExecutionError,
    RouteExecutionResult,
)


def _terminating_route() -> RouteData:
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
        replica_host="10.0.0.1",
        replica_port=8000,
        created_at=datetime.now(tzutc()),
    )


class TestTerminateRoutesDrain:
    """Drain-then-terminate ordering inside ``RouteExecutor.terminate_routes``."""

    async def test_unregister_called_before_mark_terminate(
        self,
        route_executor: RouteExecutor,
        mock_scheduling_controller: AsyncMock,
    ) -> None:
        """RR-EXEC-TERM-001: unregister_routes_now precedes mark_sessions_for_termination."""
        parent = MagicMock()
        parent.unregister = AsyncMock(return_value=RouteExecutionResult(successes=[], errors=[]))
        parent.mark_terminate = AsyncMock(return_value=None)
        mock_scheduling_controller.mark_sessions_for_termination = parent.mark_terminate
        routes = [_terminating_route(), _terminating_route()]

        with patch.object(route_executor, "unregister_routes_now", parent.unregister):
            with RouteRecorderContext.scope("test", entity_ids=[r.route_id for r in routes]):
                await route_executor.terminate_routes(routes)

        method_names = [call[0] for call in parent.method_calls]
        assert method_names == ["unregister", "mark_terminate"]
        parent.unregister.assert_awaited_once_with(routes)
        # mark_sessions_for_termination receives the session ids from the routes.
        called_session_ids = parent.mark_terminate.await_args_list[0].args[0]
        assert set(called_session_ids) == {route.session_id for route in routes}

    async def test_terminate_proceeds_when_unregister_returns_errors(
        self,
        route_executor: RouteExecutor,
        mock_scheduling_controller: AsyncMock,
    ) -> None:
        """RR-EXEC-TERM-002: per-entry unregister errors do not abort termination."""
        sample_route = _terminating_route()
        unregister_result = RouteExecutionResult(
            successes=[],
            errors=[
                RouteExecutionError(
                    route_info=sample_route,
                    reason="AppProxy bulk routes-unregister entry failed",
                    error_detail="circuit gone",
                    error_code=None,
                )
            ],
        )
        with patch.object(
            route_executor,
            "unregister_routes_now",
            AsyncMock(return_value=unregister_result),
        ) as mock_unregister:
            with RouteRecorderContext.scope("test", entity_ids=[sample_route.route_id]):
                result = await route_executor.terminate_routes([sample_route])

        mock_unregister.assert_awaited_once_with([sample_route])
        mock_scheduling_controller.mark_sessions_for_termination.assert_awaited_once()
        assert result.successes == [sample_route]
        assert result.errors == []

    async def test_terminate_proceeds_when_unregister_raises(
        self,
        route_executor: RouteExecutor,
        mock_scheduling_controller: AsyncMock,
    ) -> None:
        """RR-EXEC-TERM-003: an exception from unregister_routes_now is swallowed."""
        sample_route = _terminating_route()
        with patch.object(
            route_executor,
            "unregister_routes_now",
            AsyncMock(side_effect=RuntimeError("boom")),
        ) as mock_unregister:
            with RouteRecorderContext.scope("test", entity_ids=[sample_route.route_id]):
                result = await route_executor.terminate_routes([sample_route])

        mock_unregister.assert_awaited_once_with([sample_route])
        mock_scheduling_controller.mark_sessions_for_termination.assert_awaited_once()
        assert result.successes == [sample_route]

    async def test_empty_input_short_circuits(
        self,
        route_executor: RouteExecutor,
        mock_scheduling_controller: AsyncMock,
    ) -> None:
        """RR-EXEC-TERM-004: no routes → no unregister, no terminate, empty result."""
        with patch.object(route_executor, "unregister_routes_now") as mock_unregister:
            result = await route_executor.terminate_routes([])

        mock_unregister.assert_not_awaited()
        mock_scheduling_controller.mark_sessions_for_termination.assert_not_awaited()
        assert result.successes == []
        assert result.errors == []

    async def test_routes_without_session_still_unregister(
        self,
        route_executor: RouteExecutor,
        mock_scheduling_controller: AsyncMock,
    ) -> None:
        """RR-EXEC-TERM-005: a route without a session_id still goes through unregister.

        The session-less route is skipped at the mark_terminate step
        (no kernel to kill) but the AppProxy proxy still needs to be
        told the route is gone — otherwise stale traffic continues to
        hit the placeholder backend.
        """
        with_session = _terminating_route()
        without_session = RouteData(
            route_id=ReplicaID(uuid4()),
            deployment_id=DeploymentID(uuid4()),
            session_id=None,
            status=RouteStatus.TERMINATING,
            health_status=RouteHealthStatus.HEALTHY,
            traffic_ratio=1.0,
            revision_id=DeploymentRevisionID(uuid4()),
            traffic_status=RouteTrafficStatus.INACTIVE,
            health_check=None,
            replica_host=None,
            replica_port=None,
            created_at=datetime.now(tzutc()),
        )
        routes = [with_session, without_session]
        with patch.object(
            route_executor,
            "unregister_routes_now",
            AsyncMock(return_value=RouteExecutionResult(successes=[], errors=[])),
        ) as mock_unregister:
            with RouteRecorderContext.scope("test", entity_ids=[r.route_id for r in routes]):
                result = await route_executor.terminate_routes(routes)

        mock_unregister.assert_awaited_once_with(routes)
        called_session_ids = (
            mock_scheduling_controller.mark_sessions_for_termination.await_args_list[0].args[0]
        )
        assert called_session_ids == [with_session.session_id]
        assert result.successes == routes
