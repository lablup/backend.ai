"""Tests for RouteProbeTarget registration and initial_delay behavior."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from dateutil.tz import tzutc

from ai.backend.common.clients.valkey_client.valkey_schedule import RouteHealthRecord
from ai.backend.common.clients.valkey_client.valkey_schedule.types import RouteProbeTarget
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


class TestRegisterRouteProbeTargets:
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
        targets: list[RouteProbeTarget] = call_args[0][0]
        assert len(targets) == 1
        assert targets[0].replica_id == replica_id
        assert targets[0].health_path == "/healthz"
        assert targets[0].inference_port == 9000
        assert targets[0].replica_host == "10.0.0.2"

    async def test_registers_default_health_path_when_no_config(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """health_path defaults to '/' when route.health_check is None."""
        route = _make_route(health_check=None)
        replica_id = ReplicaID(route.route_id)

        await route_executor._register_route_probe_targets(
            [route],
            {replica_id: RouteSessionKernelInfo(replica_host="10.0.0.1", replica_port=8000)},
        )

        call_args = mock_valkey_schedule.register_route_probe_targets_batch.call_args
        targets: list[RouteProbeTarget] = call_args[0][0]
        assert targets[0].health_path == "/"

    async def test_registers_multiple_routes(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """Multiple routes produce multiple RouteProbeTarget entries."""
        routes = [_make_route() for _ in range(3)]
        replica_infos = {
            ReplicaID(r.route_id): RouteSessionKernelInfo(
                replica_host="10.0.0.1", replica_port=8000 + i
            )
            for i, r in enumerate(routes)
        }

        await route_executor._register_route_probe_targets(routes, replica_infos)

        call_args = mock_valkey_schedule.register_route_probe_targets_batch.call_args
        targets: list[RouteProbeTarget] = call_args[0][0]
        assert len(targets) == 3


class TestSyncRouteProbeTargets:
    """Tests for sync_route_probe_targets."""

    async def test_syncs_routes_with_replica_info(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """Routes with replica_host and replica_port are synced."""
        route = _make_route()

        with RouteRecorderContext.scope("test", entity_ids=[route.route_id]):
            result = await route_executor.sync_route_probe_targets([route])

        mock_valkey_schedule.register_route_probe_targets_batch.assert_awaited_once()
        assert result.successes == []
        assert result.errors == []

    async def test_skips_routes_without_replica_info(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """Routes without replica_host/port are silently skipped."""
        route = _make_route()
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

        with RouteRecorderContext.scope(
            "test", entity_ids=[route.route_id, route_no_info.route_id]
        ):
            await route_executor.sync_route_probe_targets([route, route_no_info])

        call_args = mock_valkey_schedule.register_route_probe_targets_batch.call_args
        targets: list[RouteProbeTarget] = call_args[0][0]
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
# RouteHealthObserver: within_initial_delay based on running_at
# =============================================================================


class TestObserverInitialDelay:
    """Tests for observer's initial_delay behavior with running_at-based records."""

    async def test_observer_ignores_failure_within_initial_delay(self) -> None:
        """ID-005: Observer does not write failure during initial_delay period.

        Given: running_at=5000, initial_delay=720 → initial_delay_until=5720
               current redis_time=5500 (within initial_delay)
               health check fails
        When: Observer runs
        Then: update_route_manager_health NOT called for failure
        """
        mock_deployment_repo = AsyncMock()
        mock_valkey = AsyncMock()

        route = _make_route(created_at_ts=1000)
        route_id_str = str(route.route_id)
        route_data = MagicMock()
        route_data.route_id = route.route_id
        route_data.replica_host = "10.0.0.1"
        route_data.replica_port = 8000

        record = RouteHealthRecord(
            route_id=route_id_str,
            created_at=1000,
            initial_delay_until=5720,
            health_path="/health",
            inference_port=8000,
            replica_host="10.0.0.1",
            running_at=5000,
        )
        mock_valkey.get_route_health_records_batch.return_value = {route_id_str: record}
        mock_valkey.get_redis_time.return_value = 5500  # Within initial_delay

        observer = RouteHealthObserver(
            deployment_repository=mock_deployment_repo,
            valkey_schedule=mock_valkey,
        )
        # Patch HTTP check to always fail
        observer._http_health_check = AsyncMock(return_value=False)  # type: ignore[method-assign]

        await observer.observe([route_data])

        # refresh_route_health_ttl should be called (always)
        mock_valkey.refresh_route_health_ttl.assert_awaited_once_with(route_id_str)
        # update_route_manager_health should NOT be called (failure ignored during initial_delay)
        mock_valkey.update_route_manager_health.assert_not_awaited()

    async def test_observer_writes_failure_after_initial_delay(self) -> None:
        """ID-006: Observer writes failure after initial_delay expires.

        Given: running_at=5000, initial_delay=720 → initial_delay_until=5720
               current redis_time=5800 (past initial_delay)
               health check fails
        When: Observer runs
        Then: update_route_manager_health called with False
        """
        mock_deployment_repo = AsyncMock()
        mock_valkey = AsyncMock()

        route = _make_route(created_at_ts=1000)
        route_id_str = str(route.route_id)
        route_data = MagicMock()
        route_data.route_id = route.route_id
        route_data.replica_host = "10.0.0.1"
        route_data.replica_port = 8000

        record = RouteHealthRecord(
            route_id=route_id_str,
            created_at=1000,
            initial_delay_until=5720,
            health_path="/health",
            inference_port=8000,
            replica_host="10.0.0.1",
            running_at=5000,
        )
        mock_valkey.get_route_health_records_batch.return_value = {route_id_str: record}
        mock_valkey.get_redis_time.return_value = 5800  # Past initial_delay

        observer = RouteHealthObserver(
            deployment_repository=mock_deployment_repo,
            valkey_schedule=mock_valkey,
        )
        observer._http_health_check = AsyncMock(return_value=False)  # type: ignore[method-assign]

        await observer.observe([route_data])

        mock_valkey.update_route_manager_health.assert_awaited_once_with(route_id_str, False)

    async def test_observer_writes_success_within_initial_delay(self) -> None:
        """ID-007: Observer writes success even during initial_delay.

        Given: Within initial_delay, health check succeeds
        When: Observer runs
        Then: update_route_manager_health called with True
        """
        mock_deployment_repo = AsyncMock()
        mock_valkey = AsyncMock()

        route = _make_route(created_at_ts=1000)
        route_id_str = str(route.route_id)
        route_data = MagicMock()
        route_data.route_id = route.route_id
        route_data.replica_host = "10.0.0.1"
        route_data.replica_port = 8000

        record = RouteHealthRecord(
            route_id=route_id_str,
            created_at=1000,
            initial_delay_until=5720,
            health_path="/health",
            inference_port=8000,
            replica_host="10.0.0.1",
            running_at=5000,
        )
        mock_valkey.get_route_health_records_batch.return_value = {route_id_str: record}
        mock_valkey.get_redis_time.return_value = 5500  # Within initial_delay

        observer = RouteHealthObserver(
            deployment_repository=mock_deployment_repo,
            valkey_schedule=mock_valkey,
        )
        observer._http_health_check = AsyncMock(return_value=True)  # type: ignore[method-assign]

        await observer.observe([route_data])

        mock_valkey.update_route_manager_health.assert_awaited_once_with(route_id_str, True)


# =============================================================================
# RouteHealthRecord serialization: running_at
# =============================================================================


class TestRouteHealthRecordRunningAt:
    """Tests for RouteHealthRecord running_at serialization."""

    def test_running_at_none_not_in_hash(self) -> None:
        """running_at=None should not appear in serialized hash."""
        record = RouteHealthRecord(
            route_id="r1",
            created_at=1000,
            initial_delay_until=1720,
            health_path="/health",
            inference_port=8000,
            replica_host="10.0.0.1",
            running_at=None,
        )
        h = record.to_valkey_hash()
        assert "running_at" not in h

    def test_running_at_present_in_hash(self) -> None:
        """running_at with value should appear in serialized hash."""
        record = RouteHealthRecord(
            route_id="r1",
            created_at=1000,
            initial_delay_until=5720,
            health_path="/health",
            inference_port=8000,
            replica_host="10.0.0.1",
            running_at=5000,
        )
        h = record.to_valkey_hash()
        assert h["running_at"] == "5000"

    def test_from_hash_missing_running_at_is_none(self) -> None:
        """Deserializing hash without running_at field yields None."""
        data = {
            "route_id": "r1",
            "created_at": "1000",
            "initial_delay_until": "1720",
            "health_path": "/health",
            "inference_port": "8000",
            "replica_host": "10.0.0.1",
        }
        record = RouteHealthRecord.from_valkey_hash(data)
        assert record.running_at is None

    def test_from_hash_zero_running_at_is_none(self) -> None:
        """Deserializing hash with running_at=0 yields None (backward compat)."""
        data = {
            "route_id": "r1",
            "created_at": "1000",
            "initial_delay_until": "1720",
            "health_path": "/health",
            "inference_port": "8000",
            "replica_host": "10.0.0.1",
            "running_at": "0",
        }
        record = RouteHealthRecord.from_valkey_hash(data)
        assert record.running_at is None

    def test_from_hash_valid_running_at(self) -> None:
        """Deserializing hash with valid running_at yields int."""
        data = {
            "route_id": "r1",
            "created_at": "1000",
            "initial_delay_until": "5720",
            "health_path": "/health",
            "inference_port": "8000",
            "replica_host": "10.0.0.1",
            "running_at": "5000",
        }
        record = RouteHealthRecord.from_valkey_hash(data)
        assert record.running_at == 5000

    def test_roundtrip_with_running_at(self) -> None:
        """Serialize → deserialize preserves running_at."""
        original = RouteHealthRecord(
            route_id="r1",
            created_at=1000,
            initial_delay_until=5720,
            health_path="/health",
            inference_port=8000,
            replica_host="10.0.0.1",
            running_at=5000,
        )
        restored = RouteHealthRecord.from_valkey_hash(original.to_valkey_hash())
        assert restored.running_at == 5000
        assert restored.initial_delay_until == 5720

    def test_roundtrip_without_running_at(self) -> None:
        """Serialize → deserialize preserves running_at=None."""
        original = RouteHealthRecord(
            route_id="r1",
            created_at=1000,
            initial_delay_until=1720,
            health_path="/health",
            inference_port=8000,
            replica_host="10.0.0.1",
            running_at=None,
        )
        restored = RouteHealthRecord.from_valkey_hash(original.to_valkey_hash())
        assert restored.running_at is None
