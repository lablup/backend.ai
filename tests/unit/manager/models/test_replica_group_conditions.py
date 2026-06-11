import uuid

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.models.replica_group.conditions import ReplicaGroupConditions
from ai.backend.manager.repositories.base import QueryCondition


def _compile(condition: QueryCondition) -> str:
    return str(condition())


def test_by_ids_generates_in_clause() -> None:
    group_ids = [ReplicaGroupID(uuid.uuid4()), ReplicaGroupID(uuid.uuid4())]
    sql = _compile(ReplicaGroupConditions.by_ids(group_ids))

    assert "replica_groups.id IN" in sql


def test_by_deployment_ids_generates_in_clause() -> None:
    deployment_ids = [DeploymentID(uuid.uuid4())]
    sql = _compile(ReplicaGroupConditions.by_deployment_ids(deployment_ids))

    assert "replica_groups.deployment_id IN" in sql


def test_by_lifecycles_generates_in_clause() -> None:
    sql = _compile(ReplicaGroupConditions.by_lifecycles([ReplicaGroupLifecycle.ROLLING]))

    assert "replica_groups.lifecycle IN" in sql


def test_by_scaling_statuses_generates_in_clause() -> None:
    sql = _compile(ReplicaGroupConditions.by_scaling_statuses([ReplicaGroupScalingStatus.SCALING]))

    assert "replica_groups.scaling_status IN" in sql
