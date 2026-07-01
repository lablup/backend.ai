"""Unit tests for ReplicaProbeTarget and ReplicaHealthStatus Valkey type serialization."""

from __future__ import annotations

from uuid import uuid4

import pytest

from ai.backend.common.clients.valkey_client.valkey_schedule.types import (
    ReplicaHealthStatus,
    ReplicaProbeTarget,
)
from ai.backend.common.identifier.replica import ReplicaID


class TestReplicaProbeTargetSerialization:
    @pytest.fixture
    def replica_id(self) -> ReplicaID:
        return ReplicaID(uuid4())

    @pytest.fixture
    def target(self, replica_id: ReplicaID) -> ReplicaProbeTarget:
        return ReplicaProbeTarget(
            replica_id=replica_id,
            health_path="/health",
            inference_port=8080,
            replica_host="10.0.0.1",
        )

    def test_to_valkey_hash(self, target: ReplicaProbeTarget) -> None:
        h = target.to_valkey_hash()
        assert h["replica_id"] == str(target.replica_id)
        assert h["health_path"] == "/health"
        assert h["inference_port"] == "8080"
        assert h["replica_host"] == "10.0.0.1"

    def test_from_valkey_hash(self, replica_id: ReplicaID) -> None:
        data = {
            "replica_id": str(replica_id),
            "health_path": "/healthz",
            "inference_port": "9000",
            "replica_host": "192.168.1.100",
        }
        target = ReplicaProbeTarget.from_valkey_hash(data)
        assert target.replica_id == replica_id
        assert target.health_path == "/healthz"
        assert target.inference_port == 9000
        assert target.replica_host == "192.168.1.100"

    def test_round_trip(self, target: ReplicaProbeTarget) -> None:
        restored = ReplicaProbeTarget.from_valkey_hash(target.to_valkey_hash())
        assert restored == target


class TestReplicaHealthStatusSerialization:
    @pytest.fixture
    def replica_id(self) -> ReplicaID:
        return ReplicaID(uuid4())

    @pytest.fixture
    def healthy_status(self, replica_id: ReplicaID) -> ReplicaHealthStatus:
        return ReplicaHealthStatus(
            replica_id=replica_id,
            healthy=True,
            last_check=1700000000,
        )

    def test_to_valkey_hash_healthy(self, healthy_status: ReplicaHealthStatus) -> None:
        h = healthy_status.to_valkey_hash()
        assert h["replica_id"] == str(healthy_status.replica_id)
        assert h["healthy"] == "1"
        assert h["last_check"] == "1700000000"
        assert h["consecutive_failures"] == "0"

    def test_to_valkey_hash_unhealthy(self, replica_id: ReplicaID) -> None:
        status = ReplicaHealthStatus(
            replica_id=replica_id,
            healthy=False,
            last_check=1700000000,
            consecutive_failures=3,
        )
        h = status.to_valkey_hash()
        assert h["healthy"] == "0"
        assert h["consecutive_failures"] == "3"

    def test_from_valkey_hash(self, replica_id: ReplicaID) -> None:
        data = {
            "replica_id": str(replica_id),
            "healthy": "0",
            "last_check": "1700000000",
            "consecutive_failures": "5",
        }
        status = ReplicaHealthStatus.from_valkey_hash(data)
        assert status.replica_id == replica_id
        assert status.healthy is False
        assert status.last_check == 1700000000
        assert status.consecutive_failures == 5

    def test_from_valkey_hash_missing_optional_fields(self, replica_id: ReplicaID) -> None:
        """Missing healthy/last_check/consecutive_failures fields default to safe values."""
        status = ReplicaHealthStatus.from_valkey_hash({"replica_id": str(replica_id)})
        assert status.healthy is False
        assert status.last_check == 0
        assert status.consecutive_failures == 0

    def test_round_trip_with_failures(self, replica_id: ReplicaID) -> None:
        status = ReplicaHealthStatus(
            replica_id=replica_id,
            healthy=False,
            last_check=1700000000,
            consecutive_failures=7,
        )
        restored = ReplicaHealthStatus.from_valkey_hash(status.to_valkey_hash())
        assert restored == status

    def test_round_trip(self, healthy_status: ReplicaHealthStatus) -> None:
        restored = ReplicaHealthStatus.from_valkey_hash(healthy_status.to_valkey_hash())
        assert restored == healthy_status
