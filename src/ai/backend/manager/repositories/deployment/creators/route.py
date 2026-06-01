"""CreatorSpec and BatchUpdaterSpec for route creation and updates."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus,
    RouteStatus,
    RouteSubStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base import CreatorSpec
from ai.backend.manager.repositories.base.updater import BatchUpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class RouteCreatorSpec(CreatorSpec[RoutingRow]):
    """CreatorSpec for route creation.

    Routes are created for deployments to serve traffic.
    Each route can be associated with a specific revision.
    """

    deployment_id: DeploymentID
    session_owner_id: uuid.UUID
    domain: str
    project_id: uuid.UUID
    revision_id: DeploymentRevisionID
    health_check: ModelHealthCheck | None
    traffic_ratio: float = 1.0
    traffic_status: RouteTrafficStatus = RouteTrafficStatus.INACTIVE

    @override
    def build_row(self) -> RoutingRow:
        return RoutingRow(
            endpoint=self.deployment_id,
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
        )


@dataclass
class RouteBatchUpdaterSpec(BatchUpdaterSpec[RoutingRow]):
    """BatchUpdaterSpec for batch updating routes.

    Each axis uses the appropriate optional type:
    - :class:`OptionalState` for status fields that cannot be nullified
    - :class:`TriState` for ``sub_status`` which must support explicit ``None``
      (NULLIFY) when a route exits the PROVISIONING stage
    """

    status: OptionalState[RouteStatus] = field(default_factory=OptionalState.nop)
    health_status: OptionalState[RouteHealthStatus] = field(default_factory=OptionalState.nop)
    traffic_status: OptionalState[RouteTrafficStatus] = field(default_factory=OptionalState.nop)
    sub_status: TriState[RouteSubStatus] = field(default_factory=TriState.nop)

    @property
    @override
    def row_class(self) -> type[RoutingRow]:
        return RoutingRow

    @override
    def build_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        self.status.update_dict(values, "status")
        self.health_status.update_dict(values, "health_status")
        self.traffic_status.update_dict(values, "traffic_status")
        self.sub_status.update_dict(values, "sub_status")
        return values
