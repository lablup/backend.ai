"""Action for updating route traffic status."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import RouteInfo, RouteTrafficStatus

from .base import RouteBaseAction


@dataclass
class UpdateRouteTrafficStatusAction(RouteBaseAction):
    """Action to update traffic status of a route."""

    route_id: UUID
    traffic_status: RouteTrafficStatus

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_route_traffic_status"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateRouteTrafficStatusActionResult:
    """Result of updating route traffic status."""

    route: RouteInfo
