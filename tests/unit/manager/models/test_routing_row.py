import uuid

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.endpoint import EndpointRow

# ORM cluster registration: configure_mappers() (triggered when this isolated
# test registers a domain-cluster row) resolves string relationships against the
# registry. These rows are reachable via relationships but are not otherwise
# imported/registered by this test; _ORM_CLUSTER keeps them live.
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupForProjectRow

_ORM_CLUSTER = (
    AgentRow,
    EndpointRow,
    ScalingGroupForProjectRow,
)


def test_to_route_info_carries_replica_group_id() -> None:
    replica_group_id = ReplicaGroupID(uuid.uuid4())
    row = RoutingRow(
        id=uuid.uuid4(),
        endpoint=DeploymentID(uuid.uuid4()),
        session=None,
        status=RouteStatus.PROVISIONING,
        health_status=RouteHealthStatus.NOT_CHECKED,
        traffic_ratio=1.0,
        revision=uuid.uuid4(),
        traffic_status=RouteTrafficStatus.INACTIVE,
        health_check=None,
        replica_group_id=replica_group_id,
    )

    info = row.to_route_info()

    assert info.replica_group_id == replica_group_id
