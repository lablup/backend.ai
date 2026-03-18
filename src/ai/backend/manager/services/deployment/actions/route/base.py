"""Base action class for route operations."""

from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction


class RouteBaseAction(BaseAction):
    """Base action for route operations."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.DEPLOYMENT_ROUTE
