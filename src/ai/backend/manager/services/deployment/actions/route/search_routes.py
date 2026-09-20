from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.deployment.types import RouteInfo
from ai.backend.manager.models.routing.row import RoutingRow


@dataclass(frozen=True)
class SearchRoutesAction(GlobalSearcherOpsAction[RoutingRow, RouteInfo]):
    """Page through routes across every deployment."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DeploymentEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_routes"
