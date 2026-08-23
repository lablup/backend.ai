"""Unit tests for ReplicaCreator replica-group propagation."""

import uuid

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.manager.models.routing.creators import ReplicaCreator


def _make_route_creator(
    replica_group_id: ReplicaGroupID,
    termination_grace_period: float = 30.0,
) -> ReplicaCreator:
    return ReplicaCreator(
        session_owner_id=uuid.uuid4(),
        domain="default",
        project_id=uuid.uuid4(),
        revision_id=DeploymentRevisionID(uuid.uuid4()),
        health_check=None,
        termination_grace_period=termination_grace_period,
        replica_group_id=replica_group_id,
    )


def test_build_row_carries_replica_group_id() -> None:
    replica_group_id = ReplicaGroupID(uuid.uuid4())
    row = _make_route_creator(replica_group_id=replica_group_id).build_row(
        DeploymentID(uuid.uuid4())
    )
    assert row.replica_group_id == replica_group_id


def test_build_row_carries_termination_grace_period() -> None:
    row = _make_route_creator(
        replica_group_id=ReplicaGroupID(uuid.uuid4()),
        termination_grace_period=45.0,
    ).build_row(DeploymentID(uuid.uuid4()))
    assert row.termination_grace_period == 45.0


def test_build_row_carries_owner_as_endpoint() -> None:
    deployment_id = DeploymentID(uuid.uuid4())
    row = _make_route_creator(replica_group_id=ReplicaGroupID(uuid.uuid4())).build_row(
        deployment_id
    )
    assert row.endpoint == deployment_id
