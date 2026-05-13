"""Tests for initial_delay calculation based on warming_up_at.

Test scenarios:
- ID-001: warming_up_at is set → initial_delay_until based on warming_up_at
- ID-002: warming_up_at is None → fallback to redis_time
- ID-003: created_at has expired but warming_up_at has not → still within initial_delay
- ID-005: observer ignores failure within initial_delay (warming_up_at based)
- ID-006: observer writes failure after initial_delay expires (warming_up_at based)
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
from ai.backend.manager.data.deployment.types import RouteHealthStatus, RouteStatus
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

    async def test_warming_up_at_present_uses_warming_up_at(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """ID-001: When warming_up_at exists in Valkey, initial_delay_until is anchored to it.

        Given: Route with warming_up_at=5000 in Valkey, initial_delay=720
        When: _initialize_health_records
        Then: initial_delay_until = 5000 + 720 = 5720
        """
        route = _make_route(created_at_ts=1000)
        route_id_str = str(route.route_id)

        mock_valkey_schedule.get_route_warming_up_at_batch.return_value = {
            route_id_str: 5000,
        }
        mock_valkey_schedule.get_redis_time.return_value = 5100
        mock_deployment_repo.fetch_health_check_configs_by_revision_ids.return_value = {
            route.revision_id: ModelHealthCheck(path="/health", initial_delay=720.0),
        }

        await route_executor._initialize_health_records(
            [route],
            {route.route_id: ("10.0.0.1", 8000)},
        )

        call_args = mock_valkey_schedule.initialize_route_health_records_batch.call_args
        records: list[RouteHealthRecord] = call_args[0][0]
        assert len(records) == 1
        assert records[0].warming_up_at == 5000
        assert records[0].initial_delay_until == 5000 + 720

    async def test_warming_up_at_none_falls_back_to_redis_time(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """ID-002: When warming_up_at is None, fallback to current redis_time.

        Given: No existing record in Valkey (warming_up_at not set), redis_time=6000
        When: _initialize_health_records
        Then: initial_delay_until = 6000 + 720 = 6720, warming_up_at = 6000
        """
        route = _make_route(created_at_ts=1000)

        mock_valkey_schedule.get_route_warming_up_at_batch.return_value = {}
        mock_valkey_schedule.get_redis_time.return_value = 6000
        mock_deployment_repo.fetch_health_check_configs_by_revision_ids.return_value = {
            route.revision_id: ModelHealthCheck(path="/health", initial_delay=720.0),
        }

        await route_executor._initialize_health_records(
            [route],
            {route.route_id: ("10.0.0.1", 8000)},
        )

        call_args = mock_valkey_schedule.initialize_route_health_records_batch.call_args
        records: list[RouteHealthRecord] = call_args[0][0]
        assert len(records) == 1
        assert records[0].warming_up_at == 6000
        assert records[0].initial_delay_until == 6000 + 720

    async def test_created_at_expired_but_warming_up_at_not_expired(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """ID-003: created_at-based delay would have expired, but warming_up_at-based has not.

        Given: created_at=1000, warming_up_at=5000, initial_delay=720, current_time=1800
               created_at + 720 = 1720 < 1800 (expired if created_at based)
               warming_up_at + 720 = 5720 > 1800 (NOT expired with warming_up_at based)
        When: _initialize_health_records
        Then: initial_delay_until = 5720 (based on warming_up_at, not created_at)
        """
        route = _make_route(created_at_ts=1000)
        route_id_str = str(route.route_id)

        mock_valkey_schedule.get_route_warming_up_at_batch.return_value = {
            route_id_str: 5000,
        }
        mock_valkey_schedule.get_redis_time.return_value = 1800
        mock_deployment_repo.fetch_health_check_configs_by_revision_ids.return_value = {
            route.revision_id: ModelHealthCheck(path="/health", initial_delay=720.0),
        }

        await route_executor._initialize_health_records(
            [route],
            {route.route_id: ("10.0.0.1", 8000)},
        )

        call_args = mock_valkey_schedule.initialize_route_health_records_batch.call_args
        records: list[RouteHealthRecord] = call_args[0][0]
        assert records[0].initial_delay_until == 5720
        assert records[0].created_at == 1000


# =============================================================================
# RouteHealthObserver: within_initial_delay based on warming_up_at
# =============================================================================


class TestObserverInitialDelay:
    """Tests for observer's initial_delay behavior with warming_up_at-based records."""

    async def test_observer_ignores_failure_within_initial_delay(self) -> None:
        """ID-005: Observer does not write failure during initial_delay period.

        Given: warming_up_at=5000, initial_delay=720 → initial_delay_until=5720
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
            warming_up_at=5000,
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

        Given: warming_up_at=5000, initial_delay=720 → initial_delay_until=5720
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
            warming_up_at=5000,
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
            warming_up_at=5000,
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
# RouteHealthRecord serialization: warming_up_at and running_at
# =============================================================================


class TestRouteHealthRecordTimestamps:
    """Tests for RouteHealthRecord warming_up_at / running_at serialization."""

    def test_timestamps_none_not_in_hash(self) -> None:
        """warming_up_at=None and running_at=None should not appear in serialized hash."""
        record = RouteHealthRecord(
            route_id="r1",
            created_at=1000,
            initial_delay_until=1720,
            health_path="/health",
            inference_port=8000,
            replica_host="10.0.0.1",
        )
        h = record.to_valkey_hash()
        assert "warming_up_at" not in h
        assert "running_at" not in h

    def test_timestamps_present_in_hash(self) -> None:
        """warming_up_at and running_at with values should appear in serialized hash."""
        record = RouteHealthRecord(
            route_id="r1",
            created_at=1000,
            initial_delay_until=5720,
            health_path="/health",
            inference_port=8000,
            replica_host="10.0.0.1",
            warming_up_at=5000,
            running_at=5100,
        )
        h = record.to_valkey_hash()
        assert h["warming_up_at"] == "5000"
        assert h["running_at"] == "5100"

    def test_from_hash_missing_timestamps_are_none(self) -> None:
        """Deserializing hash without warming_up_at/running_at fields yields None."""
        data = {
            "route_id": "r1",
            "created_at": "1000",
            "initial_delay_until": "1720",
            "health_path": "/health",
            "inference_port": "8000",
            "replica_host": "10.0.0.1",
        }
        record = RouteHealthRecord.from_valkey_hash(data)
        assert record.warming_up_at is None
        assert record.running_at is None

    def test_from_hash_zero_timestamps_are_none(self) -> None:
        """Deserializing hash with timestamp=0 yields None (backward compat)."""
        data = {
            "route_id": "r1",
            "created_at": "1000",
            "initial_delay_until": "1720",
            "health_path": "/health",
            "inference_port": "8000",
            "replica_host": "10.0.0.1",
            "warming_up_at": "0",
            "running_at": "0",
        }
        record = RouteHealthRecord.from_valkey_hash(data)
        assert record.warming_up_at is None
        assert record.running_at is None

    def test_from_hash_valid_timestamps(self) -> None:
        """Deserializing hash with valid timestamps yields ints."""
        data = {
            "route_id": "r1",
            "created_at": "1000",
            "initial_delay_until": "5720",
            "health_path": "/health",
            "inference_port": "8000",
            "replica_host": "10.0.0.1",
            "warming_up_at": "5000",
            "running_at": "5100",
        }
        record = RouteHealthRecord.from_valkey_hash(data)
        assert record.warming_up_at == 5000
        assert record.running_at == 5100

    def test_roundtrip_with_timestamps(self) -> None:
        """Serialize → deserialize preserves warming_up_at and running_at."""
        original = RouteHealthRecord(
            route_id="r1",
            created_at=1000,
            initial_delay_until=5720,
            health_path="/health",
            inference_port=8000,
            replica_host="10.0.0.1",
            warming_up_at=5000,
            running_at=5100,
        )
        restored = RouteHealthRecord.from_valkey_hash(original.to_valkey_hash())
        assert restored.warming_up_at == 5000
        assert restored.running_at == 5100
        assert restored.initial_delay_until == 5720

    def test_roundtrip_without_timestamps(self) -> None:
        """Serialize → deserialize preserves None timestamps."""
        original = RouteHealthRecord(
            route_id="r1",
            created_at=1000,
            initial_delay_until=1720,
            health_path="/health",
            inference_port=8000,
            replica_host="10.0.0.1",
        )
        restored = RouteHealthRecord.from_valkey_hash(original.to_valkey_hash())
        assert restored.warming_up_at is None
        assert restored.running_at is None
