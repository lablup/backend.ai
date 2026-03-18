"""Base action class for deployment policy operations."""

from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction


class DeploymentPolicyBaseAction(BaseAction):
    """Base action for deployment policy operations."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.DEPLOYMENT_POLICY
