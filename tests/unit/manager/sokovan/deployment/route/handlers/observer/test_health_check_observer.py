"""Tests for RouteHealthObserver interval throttle and consecutive-failure counting."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import cast
from unittest.mock import AsyncMock
from uuid import uuid4

from dateutil.tz import tzutc

from ai.backend.common.clients.valkey_client.valkey_schedule.types import (
    ReplicaHealthResult,
    ReplicaHealthStatus,
    ReplicaProbeTarget,
)
from ai.backend.common.config import ModelHealthCheck
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
from ai.backend.manager.sokovan.deployment.route.handlers.observer.health_check import (
    RouteHealthObserver,
)

_NOW = 1000


def _make_route(health_check: ModelHealthCheck | None) -> RouteData:
    return RouteData(
        route_id=ReplicaID(uuid4()),
        deployment_id=DeploymentID(uuid4()),
        session_id=SessionId(uuid4()),
        status=RouteStatus.RUNNING,
        health_status=RouteHealthStatus.HEALTHY,
        traffic_ratio=1.0,
        created_at=datetime.fromtimestamp(0, tz=tzutc()),
        revision_id=DeploymentRevisionID(uuid4()),
        traffic_status=RouteTrafficStatus.ACTIVE,
        health_check=health_check,
        replica_host="10.0.0.1",
        replica_port=8000,
    )


def _probe_target(route: RouteData) -> ReplicaProbeTarget:
    assert route.health_check is not None
    return ReplicaProbeTarget(
        replica_id=route.route_id,
        health_path=route.health_check.path,
        inference_port=route.replica_port or 8000,
        replica_host=route.replica_host or "10.0.0.1",
    )


def _make_valkey(
    *,
    probe_targets: Mapping[ReplicaID, ReplicaProbeTarget],
    statuses: Mapping[ReplicaID, ReplicaHealthStatus | None],
    now: int = _NOW,
) -> AsyncMock:
    valkey = AsyncMock()
    valkey.get_route_probe_targets_batch.return_value = probe_targets
    valkey.get_route_health_statuses_batch.return_value = statuses
    valkey.get_redis_time.return_value = now
    valkey.record_route_health_statuses_batch.return_value = None
    return valkey


def _observer(valkey: AsyncMock) -> RouteHealthObserver:
    return RouteHealthObserver(deployment_repository=AsyncMock(), valkey_schedule=valkey)


def _recorded(valkey: AsyncMock) -> list[ReplicaHealthResult]:
    return cast(
        "list[ReplicaHealthResult]",
        valkey.record_route_health_statuses_batch.call_args[0][0],
    )


class TestRouteHealthObserverCounting:
    async def test_first_probe_success_records_zero_failures(self) -> None:
        check = ModelHealthCheck(enable=True, interval=10.0)
        route = _make_route(check)
        valkey = _make_valkey(
            probe_targets={route.route_id: _probe_target(route)},
            statuses={route.route_id: None},
        )
        observer = _observer(valkey)
        observer._http_health_check = AsyncMock(return_value=True)  # type: ignore[method-assign]

        result = await observer.observe([route])

        assert result.observed_count == 1
        recorded = _recorded(valkey)
        assert recorded[0].healthy is True
        assert recorded[0].consecutive_failures == 0
        assert recorded[0].ttl_sec == check.health_status_ttl_sec()

    async def test_failure_increments_previous_count(self) -> None:
        route = _make_route(ModelHealthCheck(enable=True, interval=10.0))
        statuses = {
            route.route_id: ReplicaHealthStatus(
                replica_id=route.route_id,
                healthy=False,
                last_check=_NOW - 20,  # due: 20 >= interval 10
                consecutive_failures=2,
            )
        }
        valkey = _make_valkey(
            probe_targets={route.route_id: _probe_target(route)},
            statuses=statuses,
        )
        observer = _observer(valkey)
        observer._http_health_check = AsyncMock(return_value=False)  # type: ignore[method-assign]

        await observer.observe([route])

        recorded = _recorded(valkey)
        assert recorded[0].healthy is False
        assert recorded[0].consecutive_failures == 3

    async def test_success_resets_count(self) -> None:
        route = _make_route(ModelHealthCheck(enable=True, interval=10.0))
        statuses = {
            route.route_id: ReplicaHealthStatus(
                replica_id=route.route_id,
                healthy=False,
                last_check=_NOW - 20,
                consecutive_failures=5,
            )
        }
        valkey = _make_valkey(
            probe_targets={route.route_id: _probe_target(route)},
            statuses=statuses,
        )
        observer = _observer(valkey)
        observer._http_health_check = AsyncMock(return_value=True)  # type: ignore[method-assign]

        await observer.observe([route])

        assert _recorded(valkey)[0].consecutive_failures == 0


class TestRouteHealthObserverThrottle:
    async def test_skips_probe_within_interval(self) -> None:
        route = _make_route(ModelHealthCheck(enable=True, interval=10.0))
        statuses = {
            route.route_id: ReplicaHealthStatus(
                replica_id=route.route_id,
                healthy=True,
                last_check=_NOW - 5,  # not due: 5 < interval 10
                consecutive_failures=0,
            )
        }
        valkey = _make_valkey(
            probe_targets={route.route_id: _probe_target(route)},
            statuses=statuses,
        )
        observer = _observer(valkey)
        observer._http_health_check = AsyncMock(return_value=True)  # type: ignore[method-assign]

        result = await observer.observe([route])

        assert result.observed_count == 0
        observer._http_health_check.assert_not_called()
        valkey.record_route_health_statuses_batch.assert_not_called()

    async def test_skips_route_without_probe_target(self) -> None:
        route = _make_route(ModelHealthCheck(enable=True, interval=10.0))
        valkey = _make_valkey(probe_targets={}, statuses={route.route_id: None})
        observer = _observer(valkey)
        observer._http_health_check = AsyncMock(return_value=True)  # type: ignore[method-assign]

        result = await observer.observe([route])

        assert result.observed_count == 0
        observer._http_health_check.assert_not_called()


class TestRouteHealthObserverProbePolicy:
    async def test_probe_uses_per_route_timeout_and_status_code(self) -> None:
        route = _make_route(
            ModelHealthCheck(
                enable=True,
                interval=10.0,
                max_wait_time=42.0,
                expected_status_code=204,
                path="/livez",
            )
        )
        valkey = _make_valkey(
            probe_targets={route.route_id: _probe_target(route)},
            statuses={route.route_id: None},
        )
        observer = _observer(valkey)
        observer._http_health_check = AsyncMock(return_value=True)  # type: ignore[method-assign]

        await observer.observe([route])

        call = observer._http_health_check.call_args
        assert call.args == ("10.0.0.1", 8000, "/livez", 42.0, 204)
