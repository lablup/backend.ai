"""Valkey data types for route health management."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from ai.backend.common.identifier.replica import ReplicaID


@dataclass
class ReplicaProbeTarget:
    """Probe configuration for a route stored in Valkey.

    Stored as a hash at key `route_probe:{replica_id}`.
    Written once by the coordinator when the route enters WARMING_UP (host/port available).
    Read by RouteHealthObserver to know what endpoint to probe.
    """

    replica_id: ReplicaID
    health_path: str
    inference_port: int
    replica_host: str

    def to_valkey_hash(self) -> Mapping[str, str]:
        return {
            "replica_id": str(self.replica_id),
            "health_path": self.health_path,
            "inference_port": str(self.inference_port),
            "replica_host": self.replica_host,
        }

    @classmethod
    def from_valkey_hash(cls, data: Mapping[str, str]) -> ReplicaProbeTarget:
        return cls(
            replica_id=ReplicaID(UUID(data["replica_id"])),
            health_path=data["health_path"],
            inference_port=int(data["inference_port"]),
            replica_host=data["replica_host"],
        )


@dataclass
class ReplicaHealthResult:
    """Input type for recording a health check outcome.

    Passed to ``record_route_health_statuses_batch``; ``last_check`` is
    assigned by the client using the current Redis time.
    """

    replica_id: ReplicaID
    healthy: bool


@dataclass
class ReplicaHealthStatus:
    """Health check result for a route stored in Valkey.

    Stored as a hash at key `route_health:{replica_id}`.
    Written by RouteHealthObserver after each HTTP probe.
    Short TTL — key expiry signals DEGRADED (no recent check).
    """

    replica_id: ReplicaID
    healthy: bool
    last_check: int  # Unix timestamp (Redis time)

    def to_valkey_hash(self) -> Mapping[str, str]:
        return {
            "replica_id": str(self.replica_id),
            "healthy": "1" if self.healthy else "0",
            "last_check": str(self.last_check),
        }

    @classmethod
    def from_valkey_hash(cls, data: Mapping[str, str]) -> ReplicaHealthStatus:
        return cls(
            replica_id=ReplicaID(UUID(data["replica_id"])),
            healthy=data.get("healthy", "0") == "1",
            last_check=int(data.get("last_check", "0")),
        )
