"""Tests for ReplicaProbeTarget registration and initial_delay behavior."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from dateutil.tz import tzutc

from ai.backend.common.clients.valkey_client.valkey_schedule.types import (
    ReplicaHealthResult,
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
from ai.backend.manager.repositories.deployment.types import RouteData, RouteSessionKernelInfo
from ai.backend.manager.sokovan.deployment.route.executor import RouteExecutor
from ai.backend.manager.sokovan.deployment.route.handlers.observer.health_check import (
    RouteHealthObserver,
)
from ai.backend.manager.sokovan.deployment.route.recorder.context import RouteRecorderContext


def _make_route(
    created_at_ts: int = 1000,
    session_id: SessionId | None = None,
    health_check: ModelHealthCheck | None = None,
) -> RouteData:
    return RouteData(
        route_id=ReplicaID(uuid4()),
        deployment_id=DeploymentID(uuid4()),
        session_id=session_id or SessionId(uuid4()),
        status=RouteStatus.RUNNING,
        health_status=RouteHealthStatus.NOT_CHECKED,
        traffic_ratio=1.0,
        created_at=datetime.fromtimestamp(created_at_ts, tz=tzutc()),
        revision_id=DeploymentRevisionID(uuid4()),
        traffic_status=RouteTrafficStatus.INACTIVE,
        health_check=health_check,
        replica_host="10.0.0.1",
        replica_port=8000,
    )


# =============================================================================
# _register_route_probe_targets
# =============================================================================


class TestRegisterReplicaProbeTargets:
    """Tests for _register_route_probe_targets."""

    async def test_registers_probe_target_with_health_config(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """health_path comes from route.health_check when present."""
        route = _make_route(health_check=ModelHealthCheck(path="/healthz", initial_delay=60.0))
        replica_id = ReplicaID(route.route_id)

        await route_executor._register_route_probe_targets(
            [route],
            {replica_id: RouteSessionKernelInfo(replica_host="10.0.0.2", replica_port=9000)},
        )

        call_args = mock_valkey_schedule.register_route_probe_targets_batch.call_args
        targets: list[ReplicaProbeTarget] = call_args[0][0]
        assert len(targets) == 1
        assert targets[0].replica_id == replica_id
        assert targets[0].health_path == "/healthz"
        assert targets[0].inference_port == 9000
        assert targets[0].replica_host == "10.0.0.2"

    async def test_skips_route_without_health_check(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """Route with health_check=None is not registered."""
        route = _make_route(health_check=None)
        replica_id = ReplicaID(route.route_id)

        await route_executor._register_route_probe_targets(
            [route],
            {replica_id: RouteSessionKernelInfo(replica_host="10.0.0.1", replica_port=8000)},
        )

        mock_valkey_schedule.register_route_probe_targets_batch.assert_not_awaited()

    async def test_registers_multiple_routes(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """Multiple routes with health_check produce multiple ReplicaProbeTarget entries."""
        health_check = ModelHealthCheck(path="/health", initial_delay=60.0)
        routes = [_make_route(health_check=health_check) for _ in range(3)]
        replica_infos = {
            ReplicaID(r.route_id): RouteSessionKernelInfo(
                replica_host="10.0.0.1", replica_port=8000 + i
            )
            for i, r in enumerate(routes)
        }

        await route_executor._register_route_probe_targets(routes, replica_infos)

        call_args = mock_valkey_schedule.register_route_probe_targets_batch.call_args
        targets: list[ReplicaProbeTarget] = call_args[0][0]
        assert len(targets) == 3


class TestSyncReplicaProbeTargets:
    """Tests for sync_route_probe_targets."""

    async def test_syncs_routes_with_replica_info(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """Routes with health_check, replica_host and replica_port are synced."""
        route = _make_route(health_check=ModelHealthCheck(path="/health", initial_delay=60.0))

        with RouteRecorderContext.scope("test", entity_ids=[route.route_id]):
            result = await route_executor.sync_route_probe_targets([route])

        mock_valkey_schedule.register_route_probe_targets_batch.assert_awaited_once()
        assert result.successes == []
        assert result.errors == []

    async def test_skips_routes_without_health_check_or_replica_info(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """Routes missing health_check or replica info are silently skipped."""
        route = _make_route(health_check=ModelHealthCheck(path="/health", initial_delay=60.0))
        route_no_health_check = _make_route(health_check=None)
        route_no_replica = RouteData(
            route_id=ReplicaID(uuid4()),
            deployment_id=DeploymentID(uuid4()),
            session_id=SessionId(uuid4()),
            status=RouteStatus.RUNNING,
            health_status=RouteHealthStatus.NOT_CHECKED,
            traffic_ratio=1.0,
            created_at=datetime.fromtimestamp(1000, tz=tzutc()),
            revision_id=DeploymentRevisionID(uuid4()),
            traffic_status=RouteTrafficStatus.INACTIVE,
            health_check=ModelHealthCheck(path="/health", initial_delay=60.0),
            replica_host=None,
            replica_port=None,
        )

        with RouteRecorderContext.scope(
            "test",
            entity_ids=[route.route_id, route_no_health_check.route_id, route_no_replica.route_id],
        ):
            await route_executor.sync_route_probe_targets([
                route,
                route_no_health_check,
                route_no_replica,
            ])

        call_args = mock_valkey_schedule.register_route_probe_targets_batch.call_args
        targets: list[ReplicaProbeTarget] = call_args[0][0]
        assert len(targets) == 1
        assert targets[0].replica_id == ReplicaID(route.route_id)

    async def test_all_routes_missing_replica_info_returns_empty(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """No routes with replica info → no Valkey call, empty result."""
        route_no_info = RouteData(
            route_id=ReplicaID(uuid4()),
            deployment_id=DeploymentID(uuid4()),
            session_id=SessionId(uuid4()),
            status=RouteStatus.RUNNING,
            health_status=RouteHealthStatus.NOT_CHECKED,
            traffic_ratio=1.0,
            created_at=datetime.fromtimestamp(1000, tz=tzutc()),
            revision_id=DeploymentRevisionID(uuid4()),
            traffic_status=RouteTrafficStatus.INACTIVE,
            health_check=None,
            replica_host=None,
            replica_port=None,
        )

        result = await route_executor.sync_route_probe_targets([route_no_info])

        mock_valkey_schedule.register_route_probe_targets_batch.assert_not_awaited()
        assert result.successes == []
        assert result.errors == []


# =============================================================================
# RouteHealthObserver: probe target based observation
# =============================================================================


class TestObserverSetsHealthStatus:
    """Tests for RouteHealthObserver writing RouteHealthStatus to Valkey."""

    async def test_observer_writes_success_result(self) -> None:
        """ID-005: Observer writes healthy=True on successful probe.

        Given: ReplicaProbeTarget exists in Valkey, HTTP check succeeds
        When: Observer runs
        Then: record_route_health_status called with (replica_id, True)
        """
        mock_deployment_repo = AsyncMock()
        mock_valkey = AsyncMock()

        route = _make_route()
        probe_target = ReplicaProbeTarget(
            replica_id=route.route_id,
            health_path="/health",
            inference_port=8000,
            replica_host="10.0.0.1",
        )
        mock_valkey.get_route_probe_targets_batch.return_value = {route.route_id: probe_target}

        observer = RouteHealthObserver(
            deployment_repository=mock_deployment_repo,
            valkey_schedule=mock_valkey,
        )
        observer._http_health_check = AsyncMock(return_value=True)  # type: ignore[method-assign]

        await observer.observe([route])

        mock_valkey.record_route_health_statuses_batch.assert_awaited_once_with([
            ReplicaHealthResult(replica_id=route.route_id, healthy=True)
        ])

    async def test_observer_writes_failure_result(self) -> None:
        """ID-006: Observer writes healthy=False on failed probe.

        Given: ReplicaProbeTarget exists in Valkey, HTTP check fails
        When: Observer runs
        Then: record_route_health_status called with (replica_id, False)
        """
        mock_deployment_repo = AsyncMock()
        mock_valkey = AsyncMock()

        route = _make_route()
        probe_target = ReplicaProbeTarget(
            replica_id=route.route_id,
            health_path="/health",
            inference_port=8000,
            replica_host="10.0.0.1",
        )
        mock_valkey.get_route_probe_targets_batch.return_value = {route.route_id: probe_target}

        observer = RouteHealthObserver(
            deployment_repository=mock_deployment_repo,
            valkey_schedule=mock_valkey,
        )
        observer._http_health_check = AsyncMock(return_value=False)  # type: ignore[method-assign]

        await observer.observe([route])

        mock_valkey.record_route_health_statuses_batch.assert_awaited_once_with([
            ReplicaHealthResult(replica_id=route.route_id, healthy=False)
        ])

    async def test_observer_skips_route_without_probe_target(self) -> None:
        """ID-007: Observer skips route when no probe target in Valkey.

        Given: No ReplicaProbeTarget in Valkey
        When: Observer runs
        Then: record_route_health_status NOT called, observed_count=0
        """
        mock_deployment_repo = AsyncMock()
        mock_valkey = AsyncMock()

        route = _make_route()
        mock_valkey.get_route_probe_targets_batch.return_value = {route.route_id: None}

        observer = RouteHealthObserver(
            deployment_repository=mock_deployment_repo,
            valkey_schedule=mock_valkey,
        )
        observer._http_health_check = AsyncMock(return_value=True)  # type: ignore[method-assign]

        result = await observer.observe([route])

        mock_valkey.record_route_health_statuses_batch.assert_not_awaited()
        assert result.observed_count == 0
