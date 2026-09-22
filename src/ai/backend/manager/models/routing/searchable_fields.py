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
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision.searchable_fields import (
    ModelRevisionSearchableFields,
)
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
from ai.backend.manager.models.specs.search.field import NestedSearchableField, SearchableField


class _ReplicaOwnFields(RowDataConverter[RoutingRow, ModelReplicaData]):
    """The replica's own columns.

    ``error_data`` and ``health_check`` are JSON, so neither carries a filter or an order.
    The readiness, liveness and activeness statuses are folded from ``health_status`` and
    ``traffic_status``; they have no column of their own.
    """

    field_id = SearchableField(
        RoutingRow.id, UUIDConditions(RoutingRow.id), ColumnOrder(RoutingRow.id)
    )
    deployment_id = SearchableField(
        RoutingRow.endpoint,
        UUIDConditions(RoutingRow.endpoint),
        ColumnOrder(RoutingRow.endpoint),
    )
    session = SearchableField(
        RoutingRow.session, UUIDConditions(RoutingRow.session), ColumnOrder(RoutingRow.session)
    )
    session_owner = SearchableField(
        RoutingRow.session_owner,
        UUIDConditions(RoutingRow.session_owner),
        ColumnOrder(RoutingRow.session_owner),
    )
    domain = SearchableField(
        RoutingRow.domain, StringConditions(RoutingRow.domain), ColumnOrder(RoutingRow.domain)
    )
    project = SearchableField(
        RoutingRow.project, UUIDConditions(RoutingRow.project), ColumnOrder(RoutingRow.project)
    )
    status = SearchableField(
        RoutingRow.status,
        EnumConditions(RoutingRow.status, RouteStatus),
        ColumnOrder(RoutingRow.status),
    )
    health_status = SearchableField(
        RoutingRow.health_status,
        EnumConditions(RoutingRow.health_status, RouteHealthStatus),
        ColumnOrder(RoutingRow.health_status),
    )
    traffic_status = SearchableField(
        RoutingRow.traffic_status,
        EnumConditions(RoutingRow.traffic_status, RouteTrafficStatus),
        ColumnOrder(RoutingRow.traffic_status),
    )
    sub_status = SearchableField(
        RoutingRow.sub_status,
        EnumConditions(RoutingRow.sub_status, RouteSubStatus),
        ColumnOrder(RoutingRow.sub_status),
    )
    weight = SearchableField(
        RoutingRow.weight, IntConditions(RoutingRow.weight), ColumnOrder(RoutingRow.weight)
    )
    traffic_ratio = SearchableField(
        RoutingRow.traffic_ratio,
        FloatConditions(RoutingRow.traffic_ratio),
        ColumnOrder(RoutingRow.traffic_ratio),
    )
    replica_host = SearchableField(
        RoutingRow.replica_host,
        StringConditions(RoutingRow.replica_host),
        ColumnOrder(RoutingRow.replica_host),
    )
    replica_port = SearchableField(
        RoutingRow.replica_port,
        IntConditions(RoutingRow.replica_port),
        ColumnOrder(RoutingRow.replica_port),
    )
    termination_grace_period = SearchableField(
        RoutingRow.termination_grace_period,
        FloatConditions(RoutingRow.termination_grace_period),
        ColumnOrder(RoutingRow.termination_grace_period),
    )
    revision = SearchableField(
        RoutingRow.revision,
        UUIDConditions(RoutingRow.revision),
        ColumnOrder(RoutingRow.revision),
    )
    replica_group_id = SearchableField(
        RoutingRow.replica_group_id,
        UUIDConditions(RoutingRow.replica_group_id),
        ColumnOrder(RoutingRow.replica_group_id),
    )
    created_at = SearchableField(
        RoutingRow.created_at,
        DateTimeConditions(RoutingRow.created_at),
        ColumnOrder(RoutingRow.created_at),
    )
    updated_at = SearchableField(
        RoutingRow.updated_at,
        DateTimeConditions(RoutingRow.updated_at),
        ColumnOrder(RoutingRow.updated_at),
    )
    error_data = SearchableField(RoutingRow.error_data, None, None)
    health_check = SearchableField(RoutingRow.health_check, None, None)

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


class _ReplicaNestedFields:
    """The revision the replica runs. The same deployment's field row."""

    revision = NestedSearchableField(
        ModelRevisionSearchableFields.own,
        ToOneCorrelation(
            DeploymentRevisionRow,
            RoutingRow,
            DeploymentRevisionRow.id == RoutingRow.revision,
        ),
    )


class ReplicaSearchableFields:
    own = _ReplicaOwnFields()
    nested = _ReplicaNestedFields
