from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.deployment.actions.base import DeploymentAction


@dataclass
class DeleteDeploymentAction(DeploymentAction):
    deployment_id: UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.deployment_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete"


@dataclass
class DeleteDeploymentActionResult(BaseActionResult):
    deployment_id: UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.deployment_id)
