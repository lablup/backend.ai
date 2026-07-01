"""Unit tests for RouteCreatorSpec replica-group propagation."""

import uuid

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.repositories.deployment.creators.route import RouteCreatorSpec


def _make_route_spec(
    replica_group_id: ReplicaGroupID,
    termination_grace_period: float = 30.0,
) -> RouteCreatorSpec:
    return RouteCreatorSpec(
        deployment_id=DeploymentID(uuid.uuid4()),
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
    row = _make_route_spec(replica_group_id=replica_group_id).build_row()
    assert row.replica_group_id == replica_group_id


def test_build_row_carries_termination_grace_period() -> None:
    row = _make_route_spec(
        replica_group_id=ReplicaGroupID(uuid.uuid4()),
        termination_grace_period=45.0,
    ).build_row()
    assert row.termination_grace_period == 45.0
