"""Unit tests for AppProxySyncRouteHandler.

The handler fetches ``RUNNING`` routes whose ``health_status`` is
HEALTHY (probed and passed) or NOT_CHECKED (revisions that opted out of
health_check) and forwards the AppProxy-eligible subset to
``RouteExecutor.sync_appproxy``. NOT_CHECKED rows whose revision still
has a probe (the route hasn't completed its first probe yet) are
filtered out in ``execute``.
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
from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.repositories.deployment.types import RouteData, RouteSessionData
from ai.backend.manager.sokovan.deployment.route.handlers.appproxy_sync import (
    AppProxySyncRouteHandler,
)
from ai.backend.manager.sokovan.deployment.route.types import RouteExecutionResult


def _route(
    health_status: RouteHealthStatus,
    *,
    health_check_config: ModelHealthCheck | None,
) -> RouteData:
    return RouteData(
        route_id=uuid4(),
        deployment_id=DeploymentID(uuid4()),
        session_data=RouteSessionData(session_id=SessionId(uuid4()), status=SessionStatus.RUNNING),
        status=RouteStatus.RUNNING,
        health_status=health_status,
        traffic_ratio=1.0,
        revision_id=DeploymentRevisionID(uuid4()),
        replica_host="10.0.0.1",
        replica_port=8000,
        created_at=datetime.now(tzutc()),
        health_check_config=health_check_config,
    )


class TestAppProxySyncHandler:
    """Tests for AppProxySyncRouteHandler declarations and execution."""

    def test_target_statuses_includes_healthy_and_not_checked(self) -> None:
        """The SQL fetch covers HEALTHY (probed rows) and NOT_CHECKED
        (revisions that opted out of health_check; they stay in this state
        for life). traffic=ACTIVE is required so we never register routes
        that are being drained.
        """
        target = AppProxySyncRouteHandler.target_statuses()
        assert target.lifecycle == [RouteStatus.RUNNING]
        assert target.health == [RouteHealthStatus.HEALTHY, RouteHealthStatus.NOT_CHECKED]
        assert target.traffic == RouteTrafficStatus.ACTIVE

    def test_health_check_filter_imposes_no_repo_level_gating(self) -> None:
        """The repo filter is a no-op; the (NOT_CHECKED + probe-configured)
        case that AppProxy must skip is rejected in ``execute`` instead.
        """
        filt = AppProxySyncRouteHandler.health_check_filter()
        assert filt.health_check_required is False

    async def test_execute_keeps_healthy_and_unprobed_routes(self) -> None:
        """HEALTHY rows pass through; NOT_CHECKED rows pass only when their
        revision has no ``health_check_config``.
        """
        executor = AsyncMock()
        sync_result = RouteExecutionResult(successes=[], errors=[])
        executor.sync_appproxy = AsyncMock(return_value=sync_result)
        event_producer = MagicMock()
        handler = AppProxySyncRouteHandler(executor, event_producer)

        healthy_hc_on = _route(
            RouteHealthStatus.HEALTHY,
            health_check_config=ModelHealthCheck(path="/health"),
        )
        not_checked_hc_off = _route(
            RouteHealthStatus.NOT_CHECKED,
            health_check_config=None,
        )
        not_checked_hc_on = _route(
            RouteHealthStatus.NOT_CHECKED,
            health_check_config=ModelHealthCheck(path="/health"),
        )

        result = await handler.execute([healthy_hc_on, not_checked_hc_off, not_checked_hc_on])

        executor.sync_appproxy.assert_awaited_once()
        forwarded = executor.sync_appproxy.await_args.args[0]
        assert [r.route_id for r in forwarded] == [
            healthy_hc_on.route_id,
            not_checked_hc_off.route_id,
        ]
        assert result is sync_result

    async def test_execute_returns_empty_when_no_route_eligible(self) -> None:
        """Empty eligibility set short-circuits — executor is never called."""
        executor = AsyncMock()
        executor.sync_appproxy = AsyncMock()
        event_producer = MagicMock()
        handler = AppProxySyncRouteHandler(executor, event_producer)

        not_checked_hc_on = _route(
            RouteHealthStatus.NOT_CHECKED,
            health_check_config=ModelHealthCheck(path="/health"),
        )

        result = await handler.execute([not_checked_hc_on])

        executor.sync_appproxy.assert_not_awaited()
        assert result.successes == []
        assert result.errors == []
