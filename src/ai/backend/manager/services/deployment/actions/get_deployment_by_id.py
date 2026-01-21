from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class GetDeploymentByIdAction(DeploymentBaseAction):
    deployment_id: UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.deployment_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get"


@dataclass
class GetDeploymentByIdActionResult(BaseActionResult):
    data: ModelDeploymentData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)
