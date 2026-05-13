"""Tests for ``_initialize_health_records`` and observer ``initial_delay`` behaviour.

``initial_delay_until`` is anchored at health-record initialisation time
(current redis time), so probe failures during ``initial_delay`` after
init are ignored by the observer.

Test scenarios:
- ID-001: redis_time + initial_delay → initial_delay_until
- ID-002: different initial_delay values
- ID-005: observer ignores failure within initial_delay
- ID-006: observer writes failure after initial_delay expires
- ID-007: observer writes success even within initial_delay
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from dateutil.tz import tzutc

from ai.backend.common.clients.valkey_client.valkey_schedule import RouteHealthRecord
from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.types import SessionId
from ai.backend.manager.data.deployment.types import (
    ReplicaConnectionInfo,
    RouteHealthStatus,
    RouteStatus,
)
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.route.executor import RouteExecutor
from ai.backend.manager.sokovan.deployment.route.handlers.observer.health_check import (
    RouteHealthObserver,
)


def _make_route(
    created_at_ts: int = 1000,
    session_id: SessionId | None = None,
) -> RouteData:
    return RouteData(
        route_id=uuid4(),
        deployment_id=DeploymentID(uuid4()),
        session_id=session_id or SessionId(uuid4()),
        status=RouteStatus.WARMING_UP,
        health_status=RouteHealthStatus.NOT_CHECKED,
        traffic_ratio=1.0,
        created_at=datetime.fromtimestamp(created_at_ts, tz=tzutc()),
        revision_id=DeploymentRevisionID(uuid4()),
        replica_host="10.0.0.1",
        replica_port=8000,
    )


# =============================================================================
# _initialize_health_records: initial_delay_until calculation
# =============================================================================


class TestInitializeHealthRecordsInitialDelay:
    """Tests for initial_delay_until calculation in _initialize_health_records."""

    async def test_initial_delay_anchored_at_redis_time(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """ID-001: initial_delay_until = current redis_time + configured initial_delay."""
        route = _make_route(created_at_ts=1000)
        mock_valkey_schedule.get_redis_time.return_value = 6000

        await route_executor._initialize_health_records(
            [route],
            {route.route_id: ReplicaConnectionInfo(host="10.0.0.1", port=8000)},
            {route.revision_id: ModelHealthCheck(path="/health", initial_delay=720.0)},
        )

        call_args = mock_valkey_schedule.initialize_route_health_records_batch.call_args
        records: list[RouteHealthRecord] = call_args[0][0]
        assert len(records) == 1
        assert records[0].initial_delay_until == 6000 + 720
        assert records[0].running_at is None

    async def test_default_initial_delay_when_no_health_check(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """ID-002: When the revision has no health check, default initial_delay=60s applies."""
        route = _make_route(created_at_ts=1000)
        mock_valkey_schedule.get_redis_time.return_value = 6000

        await route_executor._initialize_health_records(
            [route],
            {route.route_id: ReplicaConnectionInfo(host="10.0.0.1", port=8000)},
            {route.revision_id: None},
        )

        call_args = mock_valkey_schedule.initialize_route_health_records_batch.call_args
        records: list[RouteHealthRecord] = call_args[0][0]
        assert records[0].health_path == "/"
        assert records[0].initial_delay_until == 6000 + 60


# =============================================================================
# RouteHealthObserver: within_initial_delay behaviour
# =============================================================================


class TestObserverInitialDelay:
    """Tests for observer's initial_delay behaviour."""

    async def test_observer_ignores_failure_within_initial_delay(self) -> None:
        """ID-005: Observer does not write failure during initial_delay period.

        Given: initial_delay_until=5720, current redis_time=5500 (within window),
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
        )
        mock_valkey.get_route_health_records_batch.return_value = {route_id_str: record}
        mock_valkey.get_redis_time.return_value = 5500  # Within initial_delay

        observer = RouteHealthObserver(
            deployment_repository=mock_deployment_repo,
            valkey_schedule=mock_valkey,
        )
        observer._http_health_check = AsyncMock(return_value=False)  # type: ignore[method-assign]

        await observer.observe([route_data])

        mock_valkey.refresh_route_health_ttl.assert_awaited_once_with(route_id_str)
        mock_valkey.update_route_manager_health.assert_not_awaited()

    async def test_observer_writes_failure_after_initial_delay(self) -> None:
        """ID-006: Observer writes failure after initial_delay expires."""
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
        """ID-007: Observer writes success even during initial_delay."""
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
        record = RouteHealthRecord(
            route_id="r1",
            created_at=1000,
            initial_delay_until=1720,
            health_path="/health",
            inference_port=8000,
            replica_host="10.0.0.1",
        )
        h = record.to_valkey_hash()
        assert "running_at" not in h

    def test_running_at_present_in_hash(self) -> None:
        record = RouteHealthRecord(
            route_id="r1",
            created_at=1000,
            initial_delay_until=5720,
            health_path="/health",
            inference_port=8000,
            replica_host="10.0.0.1",
            running_at=5100,
        )
        h = record.to_valkey_hash()
        assert h["running_at"] == "5100"

    def test_from_hash_missing_running_at_is_none(self) -> None:
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
        data = {
            "route_id": "r1",
            "created_at": "1000",
            "initial_delay_until": "5720",
            "health_path": "/health",
            "inference_port": "8000",
            "replica_host": "10.0.0.1",
            "running_at": "5100",
        }
        record = RouteHealthRecord.from_valkey_hash(data)
        assert record.running_at == 5100

    def test_roundtrip_with_running_at(self) -> None:
        original = RouteHealthRecord(
            route_id="r1",
            created_at=1000,
            initial_delay_until=5720,
            health_path="/health",
            inference_port=8000,
            replica_host="10.0.0.1",
            running_at=5100,
        )
        restored = RouteHealthRecord.from_valkey_hash(original.to_valkey_hash())
        assert restored.running_at == 5100
        assert restored.initial_delay_until == 5720

    def test_roundtrip_without_running_at(self) -> None:
        original = RouteHealthRecord(
            route_id="r1",
            created_at=1000,
            initial_delay_until=1720,
            health_path="/health",
            inference_port=8000,
            replica_host="10.0.0.1",
        )
        restored = RouteHealthRecord.from_valkey_hash(original.to_valkey_hash())
        assert restored.running_at is None
