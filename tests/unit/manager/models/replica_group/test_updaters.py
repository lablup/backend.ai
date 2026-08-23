"""Unit tests for replica group deploy/scaling update specs' build_values()."""

import uuid

from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.models.replica_group.updaters import (
    ReplicaGroupDeployUpdater,
    ReplicaGroupScalingUpdater,
)
from ai.backend.manager.types import OptionalState, TriState


def _group_id() -> ReplicaGroupID:
    return ReplicaGroupID(uuid.uuid4())


def test_deploy_build_values_empty_when_no_fields_set() -> None:
    assert ReplicaGroupDeployUpdater(replica_group_id=_group_id()).build_values() == {}


def test_deploy_build_values_emits_only_set_fields() -> None:
    current_revision_id = DeploymentRevisionID(uuid.uuid4())
    updater = ReplicaGroupDeployUpdater(
        replica_group_id=_group_id(),
        current_revision_id=TriState.update(current_revision_id),
        lifecycle=OptionalState.update(ReplicaGroupLifecycle.ROLLING),
    )

    values = updater.build_values()

    assert values == {
        "current_revision_id": current_revision_id,
        "lifecycle": ReplicaGroupLifecycle.ROLLING,
    }


def test_deploy_build_values_nullifies_target_revision_id() -> None:
    updater = ReplicaGroupDeployUpdater(
        replica_group_id=_group_id(),
        target_revision_id=TriState.nullify(),
        lifecycle=OptionalState.update(ReplicaGroupLifecycle.STABLE),
    )

    values = updater.build_values()

    assert values == {
        "target_revision_id": None,
        "lifecycle": ReplicaGroupLifecycle.STABLE,
    }


def test_scaling_build_values_empty_when_no_fields_set() -> None:
    assert ReplicaGroupScalingUpdater(replica_group_id=_group_id()).build_values() == {}


def test_scaling_build_values_emits_only_set_fields() -> None:
    updater = ReplicaGroupScalingUpdater(
        replica_group_id=_group_id(),
        desired_target_replica_count=OptionalState.update(5),
        scaling_status=OptionalState.update(ReplicaGroupScalingStatus.SCALING),
    )

    values = updater.build_values()

    assert values == {
        "desired_target_replica_count": 5,
        "scaling_status": ReplicaGroupScalingStatus.SCALING,
    }
