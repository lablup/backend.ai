"""Action for updating route traffic status."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import RouteInfo, RouteTrafficStatus

from .base import RouteBaseAction


@dataclass
class UpdateRouteTrafficStatusAction(RouteBaseAction):
    """Action to update traffic status of a route."""

    route_id: UUID
    traffic_status: RouteTrafficStatus

    @override
    def entity_id(self) -> str | None:
        return str(self.route_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateRouteTrafficStatusActionResult(BaseActionResult):
    """Result of updating route traffic status."""

    route: RouteInfo

    @override
    def entity_id(self) -> str | None:
        return str(self.route.route_id)
