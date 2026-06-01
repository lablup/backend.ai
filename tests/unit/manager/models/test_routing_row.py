import uuid

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.models.routing.row import RoutingRow


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
