"""Base action class for deployment policy operations."""

from typing import override

from ai.backend.manager.actions.action import BaseAction


class DeploymentPolicyBaseAction(BaseAction):
    """Base action for deployment policy operations."""

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "deployment_policy"
