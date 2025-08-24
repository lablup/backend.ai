from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.creator import DeploymentCreator
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.services.deployment.actions.base import DeploymentAction


@dataclass
class CreateDeploymentAction(DeploymentAction):
    creator: DeploymentCreator

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreateDeploymentActionResult(BaseActionResult):
    deployment: DeploymentInfo

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.deployment.id)
