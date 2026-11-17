"""What a replica search can filter and order by, and how a routing row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.model_deployment.types import (
    ActivenessStatus,
    LivenessStatus,
    ReadinessStatus,
)
from ai.backend.common.types import SessionId
from ai.backend.manager.data.deployment.types import (
    ModelReplicaData,
    RouteData,
    RouteHealthStatus,
    RouteInfo,
    RouteStatus,
    RouteSubStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.model_serving.types import RoutingData
from ai.backend.manager.models.deployment_revision.query_spec import (
    ModelRevisionQuerySpec,
)
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.number import FloatConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToOneCorrelation
from ai.backend.manager.models.specs.search.field import NestedQueryColumn, QueryColumn


class _ReplicaOwnColumns(RowDataConverter[RoutingRow, ModelReplicaData]):
    """The replica's own columns.

    ``error_data`` and ``health_check`` are JSON, so neither carries a filter or an order.
    The readiness, liveness and activeness statuses are folded from ``health_status`` and
    ``traffic_status``; they have no column of their own.
    """

    field_id = QueryColumn(RoutingRow.id, UUIDConditions(RoutingRow.id), ColumnOrder(RoutingRow.id))
    deployment_id = QueryColumn(
        RoutingRow.endpoint,
        UUIDConditions(RoutingRow.endpoint),
        ColumnOrder(RoutingRow.endpoint),
    )
    session = QueryColumn(
        RoutingRow.session, UUIDConditions(RoutingRow.session), ColumnOrder(RoutingRow.session)
    )
    session_owner = QueryColumn(
        RoutingRow.session_owner,
        UUIDConditions(RoutingRow.session_owner),
        ColumnOrder(RoutingRow.session_owner),
    )
    domain = QueryColumn(
        RoutingRow.domain, StringConditions(RoutingRow.domain), ColumnOrder(RoutingRow.domain)
    )
    project = QueryColumn(
        RoutingRow.project, UUIDConditions(RoutingRow.project), ColumnOrder(RoutingRow.project)
    )
    status = QueryColumn(
        RoutingRow.status,
        EnumConditions(RoutingRow.status, RouteStatus),
        ColumnOrder(RoutingRow.status),
    )
    health_status = QueryColumn(
        RoutingRow.health_status,
        EnumConditions(RoutingRow.health_status, RouteHealthStatus),
        ColumnOrder(RoutingRow.health_status),
    )
    traffic_status = QueryColumn(
        RoutingRow.traffic_status,
        EnumConditions(RoutingRow.traffic_status, RouteTrafficStatus),
        ColumnOrder(RoutingRow.traffic_status),
    )
    sub_status = QueryColumn(
        RoutingRow.sub_status,
        EnumConditions(RoutingRow.sub_status, RouteSubStatus),
        ColumnOrder(RoutingRow.sub_status),
    )
    weight = QueryColumn(
        RoutingRow.weight, IntConditions(RoutingRow.weight), ColumnOrder(RoutingRow.weight)
    )
    traffic_ratio = QueryColumn(
        RoutingRow.traffic_ratio,
        FloatConditions(RoutingRow.traffic_ratio),
        ColumnOrder(RoutingRow.traffic_ratio),
    )
    replica_host = QueryColumn(
        RoutingRow.replica_host,
        StringConditions(RoutingRow.replica_host),
        ColumnOrder(RoutingRow.replica_host),
    )
    replica_port = QueryColumn(
        RoutingRow.replica_port,
        IntConditions(RoutingRow.replica_port),
        ColumnOrder(RoutingRow.replica_port),
    )
    termination_grace_period = QueryColumn(
        RoutingRow.termination_grace_period,
        FloatConditions(RoutingRow.termination_grace_period),
        ColumnOrder(RoutingRow.termination_grace_period),
    )
    revision = QueryColumn(
        RoutingRow.revision,
        UUIDConditions(RoutingRow.revision),
        ColumnOrder(RoutingRow.revision),
    )
    replica_group_id = QueryColumn(
        RoutingRow.replica_group_id,
        UUIDConditions(RoutingRow.replica_group_id),
        ColumnOrder(RoutingRow.replica_group_id),
    )
    created_at = QueryColumn(
        RoutingRow.created_at,
        DateTimeConditions(RoutingRow.created_at),
        ColumnOrder(RoutingRow.created_at),
    )
    updated_at = QueryColumn(
        RoutingRow.updated_at,
        DateTimeConditions(RoutingRow.updated_at),
        ColumnOrder(RoutingRow.updated_at),
    )
    error_data = QueryColumn(RoutingRow.error_data, None, None)
    health_check = QueryColumn(RoutingRow.health_check, None, None)

    @override
    def to_data(self, row: RoutingRow) -> ModelReplicaData:
        health_status = self.health_status.read(row)
        readiness = self._readiness_status(health_status)
        liveness = LivenessStatus(health_status.value)
        return ModelReplicaData(
            id=self.field_id.read(row),
            deployment_id=self.deployment_id.read(row),
            revision_id=self.revision.read(row),
            session_id=self.session.read(row),
            readiness_status=readiness,
            liveness_status=liveness,
            activeness_status=self._activeness_status(
                self.traffic_status.read(row), readiness, liveness
            ),
            status=self.status.read(row),
            traffic_status=self.traffic_status.read(row),
            health_status=health_status,
            detail=self.error_data.read(row) or {},
            created_at=self.created_at.read(row),
        )

    def to_route_info(self, row: RoutingRow) -> RouteInfo:
        """The same row read as a route."""
        session_id = self.session.read(row)
        return RouteInfo(
            route_id=self.field_id.read(row),
            deployment_id=self.deployment_id.read(row),
            session_id=SessionId(session_id) if session_id else None,
            status=self.status.read(row),
            health_status=self.health_status.read(row),
            traffic_ratio=self.traffic_ratio.read(row),
            created_at=self.created_at.read(row),
            revision_id=self.revision.read(row),
            traffic_status=self.traffic_status.read(row),
            health_check=self.health_check.read(row),
            replica_group_id=self.replica_group_id.read(row),
            error_data=self.error_data.read(row) or {},
        )

    def to_routing_data(self, row: RoutingRow) -> RoutingData:
        """The same row read as the routing record the replica specs and route reads return."""
        session_id = self.session.read(row)
        return RoutingData(
            id=self.field_id.read(row),
            endpoint=self.deployment_id.read(row),
            session=SessionId(session_id) if session_id else None,
            status=self.status.read(row),
            health_status=self.health_status.read(row),
            traffic_ratio=self.traffic_ratio.read(row),
            created_at=self.created_at.read(row),
            error_data=self.error_data.read(row) or {},
        )

    def to_route_data(self, row: RoutingRow) -> RouteData:
        """The same row read as the reconciler's route record.

        ``last_transition_at`` stays unset: it comes from the route history, which is
        read separately.
        """
        session_id = self.session.read(row)
        return RouteData(
            route_id=self.field_id.read(row),
            deployment_id=self.deployment_id.read(row),
            session_id=SessionId(session_id) if session_id else None,
            status=self.status.read(row),
            health_status=self.health_status.read(row),
            traffic_ratio=self.traffic_ratio.read(row),
            created_at=self.created_at.read(row),
            revision_id=self.revision.read(row),
            traffic_status=self.traffic_status.read(row),
            health_check=self.health_check.read(row),
            termination_grace_period=self.termination_grace_period.read(row),
            replica_host=self.replica_host.read(row),
            replica_port=self.replica_port.read(row),
            updated_at=self.updated_at.read(row),
            sub_status=self.sub_status.read(row),
            error_data=self.error_data.read(row) or {},
        )

    def _readiness_status(self, health_status: RouteHealthStatus) -> ReadinessStatus:
        """The health status as readiness, which has no DEGRADED of its own."""
        if health_status is RouteHealthStatus.DEGRADED:
            return ReadinessStatus.UNHEALTHY
        return ReadinessStatus(health_status.value)

    def _activeness_status(
        self,
        traffic_status: RouteTrafficStatus,
        readiness: ReadinessStatus,
        liveness: LivenessStatus,
    ) -> ActivenessStatus:
        """ACTIVE only when traffic is enabled and both health axes are HEALTHY."""
        if traffic_status != RouteTrafficStatus.ACTIVE:
            return ActivenessStatus.INACTIVE
        if readiness != ReadinessStatus.HEALTHY:
            return ActivenessStatus.INACTIVE
        if liveness != LivenessStatus.HEALTHY:
            return ActivenessStatus.INACTIVE
        return ActivenessStatus.ACTIVE


class _ReplicaNestedColumns:
    """The revision the replica runs. The same deployment's field row."""

    revision = NestedQueryColumn(
        ModelRevisionQuerySpec.own,
        ToOneCorrelation(
            DeploymentRevisionRow,
            RoutingRow,
            DeploymentRevisionRow.id == RoutingRow.revision,
        ),
    )


class ReplicaQuerySpec:
    own = _ReplicaOwnColumns()
    nested = _ReplicaNestedColumns
