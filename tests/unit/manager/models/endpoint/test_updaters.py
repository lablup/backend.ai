"""Unit tests for the endpoint update specs' build_values()."""

import uuid

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.manager.models.endpoint.updaters import DeploymentUpdater
from ai.backend.manager.types import OptionalState


def _deployment_id() -> DeploymentID:
    return DeploymentID(uuid.uuid4())


def test_build_values_empty_when_no_fields_set() -> None:
    assert DeploymentUpdater(deployment_id=_deployment_id()).build_values() == {}


def test_build_values_syncs_replicas_and_desired_replicas() -> None:
    # A manual scale must write desired_replicas alongside replicas; the scaling
    # goal is COALESCE(desired_replicas, replicas), so a stale desired_replicas
    # would otherwise override the new count (BA-6542).
    updater = DeploymentUpdater(
        deployment_id=_deployment_id(),
        replica_count=OptionalState.update(5),
    )

    values = updater.build_values()

    assert values == {
        "replicas": 5,
        "desired_replicas": 5,
    }
