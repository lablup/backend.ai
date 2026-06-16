"""Unit tests for replica group deploy/scaling updater spec build_values()."""

import uuid

from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.repositories.deployment.updaters.replica_group import (
    ReplicaGroupDeployUpdaterSpec,
    ReplicaGroupScalingUpdaterSpec,
)
from ai.backend.manager.types import OptionalState, TriState


def test_deploy_build_values_empty_when_no_fields_set() -> None:
    assert ReplicaGroupDeployUpdaterSpec().build_values() == {}


def test_deploy_build_values_emits_only_set_fields() -> None:
    current_revision_id = DeploymentRevisionID(uuid.uuid4())
    spec = ReplicaGroupDeployUpdaterSpec(
        current_revision_id=TriState.update(current_revision_id),
        lifecycle=OptionalState.update(ReplicaGroupLifecycle.ROLLING),
    )

    values = spec.build_values()

    assert values == {
        "current_revision_id": current_revision_id,
        "lifecycle": ReplicaGroupLifecycle.ROLLING,
    }


def test_deploy_build_values_nullifies_target_revision_id() -> None:
    spec = ReplicaGroupDeployUpdaterSpec(
        target_revision_id=TriState.nullify(),
        lifecycle=OptionalState.update(ReplicaGroupLifecycle.STABLE),
    )

    values = spec.build_values()

    assert values == {
        "target_revision_id": None,
        "lifecycle": ReplicaGroupLifecycle.STABLE,
    }


def test_scaling_build_values_empty_when_no_fields_set() -> None:
    assert ReplicaGroupScalingUpdaterSpec().build_values() == {}


def test_scaling_build_values_emits_only_set_fields() -> None:
    spec = ReplicaGroupScalingUpdaterSpec(
        desired_target_replica_count=OptionalState.update(5),
        scaling_status=OptionalState.update(ReplicaGroupScalingStatus.SCALING),
    )

    values = spec.build_values()

    assert values == {
        "desired_target_replica_count": 5,
        "scaling_status": ReplicaGroupScalingStatus.SCALING,
    }
