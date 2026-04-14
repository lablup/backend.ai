"""Tests for initial_delay calculation based on running_at.

Test scenarios:
- ID-001: running_at is set → initial_delay_until based on running_at
- ID-002: running_at is None → fallback to redis_time
- ID-003: created_at has expired but running_at has not → still within initial_delay
- ID-004: running_at has also expired → initial_delay over
- ID-005: observer ignores failure within initial_delay (running_at based)
- ID-006: observer writes failure after initial_delay expires (running_at based)
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from dateutil.tz import tzutc

from ai.backend.common.clients.valkey_client.valkey_schedule import RouteHealthRecord
from ai.backend.common.config import ModelHealthCheck
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
        endpoint_id=uuid4(),
        session_id=session_id or SessionId(uuid4()),
        status=RouteStatus.RUNNING,
        health_status=RouteHealthStatus.NOT_CHECKED,
        traffic_ratio=1.0,
        created_at=datetime.fromtimestamp(created_at_ts, tz=tzutc()),
        revision_id=uuid4(),
        replica_host="10.0.0.1",
        replica_port=8000,
    )


# =============================================================================
# _initialize_health_records: initial_delay_until calculation
# =============================================================================


class TestInitializeHealthRecordsInitialDelay:
    """Tests for initial_delay_until calculation in _initialize_health_records."""

    async def test_running_at_present_uses_running_at(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """ID-001: When running_at exists in Valkey, initial_delay_until is based on running_at.

        Given: Route with running_at=5000 in Valkey, initial_delay=720
        When: _initialize_health_records
        Then: initial_delay_until = 5000 + 720 = 5720
        """
        route = _make_route(created_at_ts=1000)
        route_id_str = str(route.route_id)

        mock_valkey_schedule.get_route_running_at_batch.return_value = {
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
        assert records[0].running_at == 5000
        assert records[0].initial_delay_until == 5000 + 720

    async def test_running_at_none_falls_back_to_redis_time(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """ID-002: When running_at is None, fallback to current redis_time.

        Given: No existing record in Valkey (running_at not set), redis_time=6000
        When: _initialize_health_records
        Then: initial_delay_until = 6000 + 720 = 6720, running_at = 6000
        """
        route = _make_route(created_at_ts=1000)

        mock_valkey_schedule.get_route_running_at_batch.return_value = {}
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
        assert records[0].running_at == 6000
        assert records[0].initial_delay_until == 6000 + 720

    async def test_created_at_expired_but_running_at_not_expired(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_valkey_schedule: AsyncMock,
    ) -> None:
        """ID-003: created_at-based delay would have expired, but running_at-based has not.

        Given: created_at=1000, running_at=5000, initial_delay=720, current_time=1800
               created_at + 720 = 1720 < 1800 (expired if created_at based)
               running_at + 720 = 5720 > 1800 (NOT expired with running_at based)
        When: _initialize_health_records
        Then: initial_delay_until = 5720 (based on running_at, not created_at)
        """
        route = _make_route(created_at_ts=1000)
        route_id_str = str(route.route_id)

        mock_valkey_schedule.get_route_running_at_batch.return_value = {
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
