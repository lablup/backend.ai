"""Unit tests for WarmingUpRouteHandler.

The handler is a thin shim over ``RouteExecutor.check_warming_up_routes``.
The actual session-verification, replica-info population, and first-health
gate logic is exercised in the executor tests; here we only verify that
the handler declares the right targets/transitions and pass-throughs.
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
    RouteHandlerCategory,
    RouteHealthStatus,
    RouteStatus,
)
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.route.handlers.warming_up import (
    WarmingUpRouteHandler,
)
from ai.backend.manager.sokovan.deployment.route.types import RouteExecutionResult


def _route() -> RouteData:
    return RouteData(
        route_id=uuid4(),
        deployment_id=DeploymentID(uuid4()),
        session_id=SessionId(uuid4()),
        status=RouteStatus.WARMING_UP,
        health_status=RouteHealthStatus.NOT_CHECKED,
        traffic_ratio=1.0,
        revision_id=DeploymentRevisionID(uuid4()),
        replica_host="10.0.0.1",
        replica_port=8000,
        created_at=datetime.now(tzutc()),
    )


class TestWarmingUpRouteHandlerDeclarations:
    """Static handler declarations: category, targets, transitions."""

    def test_category_is_lifecycle(self) -> None:
        assert WarmingUpRouteHandler.category() == RouteHandlerCategory.LIFECYCLE

    def test_target_lifecycle_is_warming_up_only(self) -> None:
        target = WarmingUpRouteHandler.target_statuses()
        assert target.lifecycle == [RouteStatus.WARMING_UP]

    def test_target_health_covers_all_health_statuses(self) -> None:
        target = WarmingUpRouteHandler.target_statuses()
        assert set(target.health) == set(RouteHealthStatus)

    def test_success_transition_promotes_to_running_healthy(self) -> None:
        transitions = WarmingUpRouteHandler.status_transitions()
        assert transitions.success is not None
        assert transitions.success.status == RouteStatus.RUNNING
        assert transitions.success.health_status == RouteHealthStatus.HEALTHY

    def test_failure_transition_drops_to_failed_to_start(self) -> None:
        transitions = WarmingUpRouteHandler.status_transitions()
        assert transitions.failure is not None
        assert transitions.failure.status == RouteStatus.FAILED_TO_START
        assert transitions.failure.health_status == RouteHealthStatus.NOT_CHECKED

    def test_no_stale_transition(self) -> None:
        assert WarmingUpRouteHandler.status_transitions().stale is None


class TestWarmingUpRouteHandlerDelegation:
    """Handler.execute is a thin pass-through to check_warming_up_routes."""

    async def test_execute_delegates_to_check_warming_up_routes(self) -> None:
        executor = AsyncMock()
        check_result = RouteExecutionResult(successes=[], errors=[])
        executor.check_warming_up_routes = AsyncMock(return_value=check_result)
        event_producer = MagicMock()
        handler = WarmingUpRouteHandler(executor, event_producer)
        routes = [_route()]

        result = await handler.execute(routes)

        executor.check_warming_up_routes.assert_awaited_once_with(routes)
        assert result is check_result

    async def test_post_process_logs_only(self) -> None:
        executor = AsyncMock()
        event_producer = MagicMock()
        handler = WarmingUpRouteHandler(executor, event_producer)

        await handler.post_process(
            RouteExecutionResult(successes=[_route()], errors=[]),
        )

        # Logging-only shim — no executor / event_producer side effects.
        assert executor.method_calls == []
        assert event_producer.method_calls == []
