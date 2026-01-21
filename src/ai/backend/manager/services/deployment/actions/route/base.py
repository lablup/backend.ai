"""Base action class for route operations."""

from typing import override

from ai.backend.manager.actions.action import BaseAction


class RouteBaseAction(BaseAction):
    """Base action for route operations."""

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "deployment_route"
