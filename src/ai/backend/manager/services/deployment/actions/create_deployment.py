"""Action for creating deployments."""

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.creator import DeploymentCreator
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class CreateDeploymentAction(DeploymentBaseAction):
    """Action to create a new deployment."""

    creator: DeploymentCreator

    @override
    def entity_id(self) -> Optional[str]:
        return None  # New deployment doesn't have an ID yet

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreateDeploymentActionResult(BaseActionResult):
    data: DeploymentInfo

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)
