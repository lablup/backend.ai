import uuid
from datetime import UTC, datetime
from typing import Any

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.resource_group.row import ResourceGroupForProjectRow

# ORM cluster registration: configure_mappers() (triggered when this isolated
# test registers a domain-cluster row) resolves string relationships against the
# registry. These rows are reachable via relationships but are not otherwise
# imported/registered by this test; _ORM_CLUSTER keeps them live.
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.routing.searchable_fields import ReplicaSearchableFields

_ORM_CLUSTER = (
    AgentRow,
    EndpointRow,
    ImageRow,
    ResourceGroupForProjectRow,
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

    info = ReplicaSearchableFields.own.to_route_info(row)

    assert info.replica_group_id == replica_group_id


def _routing_row(error_data: dict[str, Any] | None) -> RoutingRow:
    return RoutingRow(
        id=ReplicaID(uuid.uuid4()),
        endpoint=DeploymentID(uuid.uuid4()),
        session=SessionID(uuid.uuid4()),
        status=RouteStatus.FAILED_TO_START,
        health_status=RouteHealthStatus.UNHEALTHY,
        traffic_ratio=0.5,
        revision=DeploymentRevisionID(uuid.uuid4()),
        traffic_status=RouteTrafficStatus.INACTIVE,
        health_check=None,
        created_at=datetime.now(UTC),
        error_data=error_data,
    )


def test_to_routing_data_carries_the_row_values() -> None:
    error_data = {"type": "session_cancelled", "errors": []}
    row = _routing_row(error_data)

    data = ReplicaSearchableFields.own.to_routing_data(row)

    assert data.id == row.id
    assert data.endpoint == row.endpoint
    assert data.session == row.session
    assert data.status == RouteStatus.FAILED_TO_START
    assert data.health_status == RouteHealthStatus.UNHEALTHY
    assert data.traffic_ratio == 0.5
    assert data.created_at == row.created_at
    assert data.error_data == error_data


def test_to_routing_data_turns_missing_error_data_into_an_empty_dict() -> None:
    data = ReplicaSearchableFields.own.to_routing_data(_routing_row(None))

    assert data.error_data == {}
