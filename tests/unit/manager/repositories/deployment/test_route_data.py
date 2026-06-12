"""Unit tests for RouteData termination grace judgment."""

import uuid
from datetime import UTC, datetime, timedelta

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica import ReplicaID
from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus,
    RouteStatus,
    RouteSubStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.repositories.deployment.types.endpoint import RouteData

_NOW = datetime(2026, 6, 12, 12, 0, 0, tzinfo=UTC)


def _make_route_data(
    termination_grace_period: float,
    last_transition_at: datetime | None,
) -> RouteData:
    return RouteData(
        route_id=ReplicaID(uuid.uuid4()),
        deployment_id=DeploymentID(uuid.uuid4()),
        session_id=None,
        status=RouteStatus.TERMINATING,
        health_status=RouteHealthStatus.NOT_CHECKED,
        traffic_ratio=1.0,
        created_at=_NOW - timedelta(hours=1),
        revision_id=DeploymentRevisionID(uuid.uuid4()),
        traffic_status=RouteTrafficStatus.INACTIVE,
        health_check=None,
        termination_grace_period=termination_grace_period,
        sub_status=RouteSubStatus.COOLING_DOWN,
        last_transition_at=last_transition_at,
    )


class TestIsTerminationGraceElapsed:
    def test_no_transition_history_means_immediate(self) -> None:
        route = _make_route_data(30.0, None)
        assert route.is_termination_grace_elapsed(_NOW)

    def test_zero_grace_period_means_immediate(self) -> None:
        route = _make_route_data(0.0, _NOW)
        assert route.is_termination_grace_elapsed(_NOW)

    def test_within_grace_period_is_not_elapsed(self) -> None:
        route = _make_route_data(30.0, _NOW - timedelta(seconds=10))
        assert not route.is_termination_grace_elapsed(_NOW)

    def test_past_grace_period_is_elapsed(self) -> None:
        route = _make_route_data(30.0, _NOW - timedelta(seconds=31))
        assert route.is_termination_grace_elapsed(_NOW)

    def test_exact_grace_period_boundary_is_elapsed(self) -> None:
        route = _make_route_data(30.0, _NOW - timedelta(seconds=30))
        assert route.is_termination_grace_elapsed(_NOW)
