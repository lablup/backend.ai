"""Base action for deployment service."""

from typing import override

from ai.backend.manager.actions.action import BaseAction


class DeploymentBaseAction(BaseAction):
    """Base action for deployment operations."""

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "deployment"
