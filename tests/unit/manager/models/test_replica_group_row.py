from ai.backend.manager.data.deployment.types import (
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow


def test_replica_group_lifecycle_values() -> None:
    assert ReplicaGroupLifecycle.ROLLING.value == "rolling"
    assert ReplicaGroupLifecycle.STABLE.value == "stable"
    assert ReplicaGroupLifecycle.FAILED.value == "failed"
    assert ReplicaGroupLifecycle.DRAINING.value == "draining"
    assert ReplicaGroupLifecycle.DRAINED.value == "drained"


def test_replica_group_scaling_status_values() -> None:
    assert ReplicaGroupScalingStatus.SCALING.value == "scaling"
    assert ReplicaGroupScalingStatus.STABLE.value == "stable"


def test_replica_group_status_columns_default_to_stable() -> None:
    columns = ReplicaGroupRow.__table__.columns

    lifecycle = columns["lifecycle"]
    assert lifecycle.nullable is False
    assert lifecycle.default.arg is ReplicaGroupLifecycle.STABLE
    assert lifecycle.server_default.arg == ReplicaGroupLifecycle.STABLE.value

    scaling_status = columns["scaling_status"]
    assert scaling_status.nullable is False
    assert scaling_status.default.arg is ReplicaGroupScalingStatus.STABLE
    assert scaling_status.server_default.arg == ReplicaGroupScalingStatus.STABLE.value
