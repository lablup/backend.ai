"""CreatorSpec and BatchUpdaterSpec for route creation and updates."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Optional

from typing_extensions import override

from ai.backend.manager.data.deployment.types import RouteStatus, RouteTrafficStatus
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base import CreatorSpec
from ai.backend.manager.repositories.base.updater import BatchUpdaterSpec


@dataclass
class RouteCreatorSpec(CreatorSpec[RoutingRow]):
    """CreatorSpec for route creation.

    Routes are created for deployment endpoints to serve traffic.
    Each route can be associated with a specific revision.
    """

    endpoint_id: uuid.UUID
    session_owner_id: uuid.UUID
    domain: str
    project_id: uuid.UUID
    traffic_ratio: float = 1.0
    revision_id: Optional[uuid.UUID] = None
    traffic_status: RouteTrafficStatus = RouteTrafficStatus.ACTIVE

    @override
    def build_row(self) -> RoutingRow:
        return RoutingRow(
            id=uuid.uuid4(),
            endpoint=self.endpoint_id,
            session=None,
            session_owner=self.session_owner_id,
            domain=self.domain,
            project=self.project_id,
            status=RouteStatus.PROVISIONING,
            traffic_ratio=self.traffic_ratio,
            revision=self.revision_id,
            traffic_status=self.traffic_status,
        )


@dataclass
class RouteBatchUpdaterSpec(BatchUpdaterSpec[RoutingRow]):
    """BatchUpdaterSpec for batch updating routes.

    Accepts optional fields and only updates fields that are specified.
    This allows flexible partial updates for various route operations.
    """

    status: Optional[RouteStatus] = None
    traffic_ratio: Optional[float] = None
    traffic_status: Optional[RouteTrafficStatus] = None

    @property
    @override
    def row_class(self) -> type[RoutingRow]:
        return RoutingRow

    @override
    def build_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        if self.status is not None:
            values["status"] = self.status
        if self.traffic_ratio is not None:
            values["traffic_ratio"] = self.traffic_ratio
        if self.traffic_status is not None:
            values["traffic_status"] = self.traffic_status
        return values
