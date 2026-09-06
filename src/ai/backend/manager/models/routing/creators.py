"""Creator specs for the routings table."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    RouteStatus,
    RouteSubStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.model_serving.types import RoutingData
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class ReplicaCreator(FieldCreator[DeploymentID, RoutingRow, RoutingData]):
    """Adds one replica to the deployment it serves traffic for."""

    session_owner_id: uuid.UUID
    domain: str
    project_id: uuid.UUID
    revision_id: DeploymentRevisionID
    health_check: ModelHealthCheck | None
    termination_grace_period: float
    replica_group_id: ReplicaGroupID
    traffic_ratio: float = 1.0
    traffic_status: RouteTrafficStatus = RouteTrafficStatus.INACTIVE

    @override
    def field_id(self, row: RoutingRow) -> ReplicaID:
        return ReplicaID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: DeploymentID) -> RoutingRow:
        return RoutingRow(
            endpoint=owner_id,
            session=None,
            session_owner=self.session_owner_id,
            domain=self.domain,
            project=self.project_id,
            status=RouteStatus.PROVISIONING,
            sub_status=RouteSubStatus.PENDING,
            traffic_ratio=self.traffic_ratio,
            revision=self.revision_id,
            traffic_status=self.traffic_status,
            health_check=self.health_check,
            termination_grace_period=self.termination_grace_period,
            replica_group_id=self.replica_group_id,
        )

    @override
    def to_data(self, row: RoutingRow) -> RoutingData:
        return row.to_data()
