"""Unit tests for the replica spec updater build_values()."""

from ai.backend.manager.repositories.deployment.updaters.deployment import (
    ReplicaSpecUpdaterSpec,
)
from ai.backend.manager.types import OptionalState


def test_replica_spec_build_values_empty_when_no_fields_set() -> None:
    assert ReplicaSpecUpdaterSpec().build_values() == {}


def test_replica_spec_build_values_syncs_replicas_and_desired_replicas() -> None:
    # A manual scale must write desired_replicas alongside replicas; the scaling
    # goal is COALESCE(desired_replicas, replicas), so a stale desired_replicas
    # would otherwise override the new count (BA-6542).
    spec = ReplicaSpecUpdaterSpec(
        replica_count=OptionalState.update(5),
    )

    values = spec.build_values()

    assert values == {
        "replicas": 5,
        "desired_replicas": 5,
    }
