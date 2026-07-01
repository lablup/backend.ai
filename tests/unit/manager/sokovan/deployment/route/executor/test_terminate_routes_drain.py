"""Unit tests for the two-stage termination pipeline in ``RouteExecutor``.

``drain_routes`` (TERMINATING+DRAINING) pushes a synchronous AppProxy
unregister so no fresh request lands on a kernel that is about to die;
failures are logged but every route still advances to COOLING_DOWN —
the long-cycle ``AppProxySyncRouteHandler`` converges leftovers.
``terminate_routes`` (TERMINATING+COOLING_DOWN) then destroys only the
sessions whose termination grace period has elapsed since the draining
transition.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
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
from ai.backend.manager.sokovan.deployment.route.executor import RouteExecutor
from ai.backend.manager.sokovan.deployment.route.recorder.context import RouteRecorderContext
from ai.backend.manager.sokovan.deployment.route.types import (
    RouteExecutionError,
    RouteExecutionResult,
)

_NOW = datetime(2026, 6, 12, 12, 0, 0, tzinfo=tzutc())


def _terminating_route(
    sub_status: RouteSubStatus = RouteSubStatus.DRAINING,
    termination_grace_period: float = 30.0,
    last_transition_at: datetime | None = None,
    session_id: SessionId | None = None,
) -> RouteData:
    return RouteData(
        route_id=ReplicaID(uuid4()),
        deployment_id=DeploymentID(uuid4()),
        session_id=session_id,
        status=RouteStatus.TERMINATING,
        health_status=RouteHealthStatus.HEALTHY,
        traffic_ratio=1.0,
        revision_id=DeploymentRevisionID(uuid4()),
        traffic_status=RouteTrafficStatus.INACTIVE,
        health_check=None,
        termination_grace_period=termination_grace_period,
        replica_host="10.0.0.1",
        replica_port=8000,
        created_at=_NOW - timedelta(minutes=5),
        sub_status=sub_status,
        last_transition_at=last_transition_at,
    )


class TestDrainRoutes:
    """AppProxy unregister inside ``RouteExecutor.drain_routes``."""

    async def test_unregister_called_and_all_routes_advance(
        self,
        route_executor: RouteExecutor,
    ) -> None:
        """RR-EXEC-DRAIN-001: unregister runs and every route returns as success."""
        routes = [_terminating_route(), _terminating_route()]
        with patch.object(
            route_executor,
            "unregister_routes_now",
            AsyncMock(return_value=RouteExecutionResult(successes=[], errors=[])),
        ) as mock_unregister:
            with RouteRecorderContext.scope("test", entity_ids=[r.route_id for r in routes]):
                result = await route_executor.drain_routes(routes)

        mock_unregister.assert_awaited_once_with(routes)
        assert result.successes == routes
        assert result.errors == []

    async def test_drain_proceeds_when_unregister_returns_errors(
        self,
        route_executor: RouteExecutor,
    ) -> None:
        """RR-EXEC-DRAIN-002: per-entry unregister errors do not hold routes in DRAINING."""
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
        ):
            with RouteRecorderContext.scope("test", entity_ids=[sample_route.route_id]):
                result = await route_executor.drain_routes([sample_route])

        assert result.successes == [sample_route]
        assert result.errors == []

    async def test_drain_proceeds_when_unregister_raises(
        self,
        route_executor: RouteExecutor,
    ) -> None:
        """RR-EXEC-DRAIN-003: an exception from unregister_routes_now is swallowed."""
        sample_route = _terminating_route()
        with patch.object(
            route_executor,
            "unregister_routes_now",
            AsyncMock(side_effect=RuntimeError("boom")),
        ):
            with RouteRecorderContext.scope("test", entity_ids=[sample_route.route_id]):
                result = await route_executor.drain_routes([sample_route])

        assert result.successes == [sample_route]

    async def test_empty_input_short_circuits(
        self,
        route_executor: RouteExecutor,
    ) -> None:
        """RR-EXEC-DRAIN-004: no routes → no unregister, empty result."""
        with patch.object(route_executor, "unregister_routes_now") as mock_unregister:
            result = await route_executor.drain_routes([])

        mock_unregister.assert_not_awaited()
        assert result.successes == []
        assert result.errors == []


class TestTerminateRoutesGracePeriod:
    """Grace-gated session cleanup inside ``RouteExecutor.terminate_routes``."""

    async def test_route_within_grace_period_keeps_session_alive(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_scheduling_controller: AsyncMock,
    ) -> None:
        """RR-EXEC-TERM-001: in-grace route survives as stale."""
        mock_deployment_repo.get_db_now = AsyncMock(return_value=_NOW)
        waiting = _terminating_route(
            sub_status=RouteSubStatus.COOLING_DOWN,
            termination_grace_period=30.0,
            last_transition_at=_NOW - timedelta(seconds=10),
            session_id=SessionId(uuid4()),
        )
        with RouteRecorderContext.scope("test", entity_ids=[waiting.route_id]):
            result = await route_executor.terminate_routes([waiting])

        called_session_ids = (
            mock_scheduling_controller.mark_sessions_for_termination.await_args_list[0].args[0]
        )
        assert called_session_ids == []
        assert result.successes == []
        assert result.stale == [waiting]

    async def test_route_past_grace_period_is_terminated(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_scheduling_controller: AsyncMock,
    ) -> None:
        """RR-EXEC-TERM-002: grace-elapsed route gets its session terminated."""
        mock_deployment_repo.get_db_now = AsyncMock(return_value=_NOW)
        elapsed = _terminating_route(
            sub_status=RouteSubStatus.COOLING_DOWN,
            termination_grace_period=30.0,
            last_transition_at=_NOW - timedelta(seconds=31),
            session_id=SessionId(uuid4()),
        )
        with RouteRecorderContext.scope("test", entity_ids=[elapsed.route_id]):
            result = await route_executor.terminate_routes([elapsed])

        called_session_ids = (
            mock_scheduling_controller.mark_sessions_for_termination.await_args_list[0].args[0]
        )
        assert called_session_ids == [elapsed.session_id]
        assert result.successes == [elapsed]
        assert result.stale == []

    async def test_zero_grace_period_terminates_immediately(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_scheduling_controller: AsyncMock,
    ) -> None:
        """RR-EXEC-TERM-003: grace 0 terminates in the same cycle it was drained."""
        mock_deployment_repo.get_db_now = AsyncMock(return_value=_NOW)
        immediate = _terminating_route(
            sub_status=RouteSubStatus.COOLING_DOWN,
            termination_grace_period=0.0,
            last_transition_at=_NOW,
            session_id=SessionId(uuid4()),
        )
        with RouteRecorderContext.scope("test", entity_ids=[immediate.route_id]):
            result = await route_executor.terminate_routes([immediate])

        assert result.successes == [immediate]
        assert result.stale == []

    async def test_mixed_routes_partition_by_grace(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_scheduling_controller: AsyncMock,
    ) -> None:
        """RR-EXEC-TERM-004: only grace-elapsed routes terminate."""
        mock_deployment_repo.get_db_now = AsyncMock(return_value=_NOW)
        waiting = _terminating_route(
            sub_status=RouteSubStatus.COOLING_DOWN,
            termination_grace_period=60.0,
            last_transition_at=_NOW - timedelta(seconds=5),
            session_id=SessionId(uuid4()),
        )
        # last_transition_at=None: pre-migration rows have no draining
        # history, so they terminate immediately.
        legacy = _terminating_route(
            sub_status=RouteSubStatus.COOLING_DOWN,
            last_transition_at=None,
            session_id=SessionId(uuid4()),
        )
        routes = [waiting, legacy]
        with RouteRecorderContext.scope("test", entity_ids=[r.route_id for r in routes]):
            result = await route_executor.terminate_routes(routes)

        called_session_ids = (
            mock_scheduling_controller.mark_sessions_for_termination.await_args_list[0].args[0]
        )
        assert called_session_ids == [legacy.session_id]
        assert result.successes == [legacy]
        assert result.stale == [waiting]

    async def test_routes_without_session_are_skipped_at_session_cleanup(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_scheduling_controller: AsyncMock,
    ) -> None:
        """RR-EXEC-TERM-005: a route without a session_id still completes as success."""
        mock_deployment_repo.get_db_now = AsyncMock(return_value=_NOW)
        without_session = _terminating_route(
            sub_status=RouteSubStatus.COOLING_DOWN,
            last_transition_at=_NOW - timedelta(seconds=31),
            session_id=None,
        )
        with RouteRecorderContext.scope("test", entity_ids=[without_session.route_id]):
            result = await route_executor.terminate_routes([without_session])

        called_session_ids = (
            mock_scheduling_controller.mark_sessions_for_termination.await_args_list[0].args[0]
        )
        assert called_session_ids == []
        assert result.successes == [without_session]

    async def test_empty_input_short_circuits(
        self,
        route_executor: RouteExecutor,
        mock_scheduling_controller: AsyncMock,
    ) -> None:
        """RR-EXEC-TERM-006: no routes → no session termination, empty result."""
        result = await route_executor.terminate_routes([])

        mock_scheduling_controller.mark_sessions_for_termination.assert_not_awaited()
        assert result.successes == []
        assert result.errors == []
