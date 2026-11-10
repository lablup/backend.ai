"""Unit tests for RunningRouteHandler stage declaration.

The session-liveness check itself lives in the executor tests; here we only
pin down which routes the handler picks up and where a dead session sends them.
"""

from __future__ import annotations

from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus,
    RouteStatus,
    RouteSubStatus,
)
from ai.backend.manager.sokovan.deployment.route.handlers.running import (
    RunningRouteHandler,
)


class TestRunningHandler:
    """Tests for RunningRouteHandler target statuses and transitions."""

    def test_targets_provisioning_and_running_stages(self) -> None:
        """RR-HANDLER-001: PROVISIONING routes are checked alongside RUNNING ones."""
        target = RunningRouteHandler.target_statuses()
        assert target.lifecycle == [RouteStatus.PROVISIONING, RouteStatus.RUNNING]
        assert target.sub_status is None
        assert target.health is None

    def test_failure_transitions_to_terminating(self) -> None:
        """RR-HANDLER-002: a dead session drains the route and resets its health."""
        transitions = RunningRouteHandler.status_transitions()
        assert transitions.failure is not None
        assert transitions.failure.status == RouteStatus.TERMINATING
        assert transitions.failure.sub_status == RouteSubStatus.DRAINING
        assert transitions.failure.health_status == RouteHealthStatus.NOT_CHECKED
        assert transitions.success is None
        assert transitions.stale is None
