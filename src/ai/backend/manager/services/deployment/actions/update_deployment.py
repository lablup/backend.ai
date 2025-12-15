from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.repositories.deployment.updaters import NewDeploymentUpdaterSpec
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class UpdateDeploymentAction(DeploymentBaseAction):
    """Action to update an existing deployment."""

    deployment_id: UUID
    updater_spec: NewDeploymentUpdaterSpec

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.deployment_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update"


@dataclass
class UpdateDeploymentActionResult(BaseActionResult):
    data: ModelDeploymentData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)
