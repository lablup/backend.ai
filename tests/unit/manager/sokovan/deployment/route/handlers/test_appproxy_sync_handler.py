"""Unit tests for AppProxySyncRouteHandler.

The handler itself is a thin shim that forwards routes to
``RouteExecutor.sync_appproxy``; the hc-eligibility filter lives in the
executor and is exercised in the executor tests.
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
from ai.backend.manager.sokovan.deployment.route.handlers.appproxy_sync import (
    AppProxySyncRouteHandler,
)
from ai.backend.manager.sokovan.deployment.route.types import RouteExecutionResult


def _route(health_status: RouteHealthStatus) -> RouteData:
    return RouteData(
        route_id=uuid4(),
        deployment_id=DeploymentID(uuid4()),
        session_id=SessionId(uuid4()),
        status=RouteStatus.RUNNING,
        health_status=health_status,
        traffic_ratio=1.0,
        revision_id=DeploymentRevisionID(uuid4()),
        replica_host="10.0.0.1",
        replica_port=8000,
        created_at=datetime.now(tzutc()),
    )


class TestAppProxySyncHandler:
    """Tests for AppProxySyncRouteHandler declarations and delegation."""

    def test_target_statuses_includes_healthy_and_not_checked(self) -> None:
        """The SQL fetch covers HEALTHY (probed rows) and NOT_CHECKED
        (revisions that opted out of health_check; they stay in this state
        for life). traffic=ACTIVE is required so we never register routes
        that are being drained.
        """
        target = AppProxySyncRouteHandler.target_statuses()
        assert target.lifecycle == [RouteStatus.RUNNING]
        assert target.health == [RouteHealthStatus.HEALTHY, RouteHealthStatus.NOT_CHECKED]
        assert target.traffic == [RouteTrafficStatus.ACTIVE]

    async def test_execute_forwards_routes_to_executor(self) -> None:
        """``execute`` is a thin pass-through to ``sync_appproxy``."""
        executor = AsyncMock()
        sync_result = RouteExecutionResult(successes=[], errors=[])
        executor.sync_appproxy = AsyncMock(return_value=sync_result)
        handler = AppProxySyncRouteHandler(executor, MagicMock())

        routes = [_route(RouteHealthStatus.HEALTHY), _route(RouteHealthStatus.NOT_CHECKED)]
        result = await handler.execute(routes)

        executor.sync_appproxy.assert_awaited_once_with(routes)
        assert result is sync_result
