from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.repositories.base import Updater
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class UpdateDeploymentAction(DeploymentBaseAction):
    """Action to update an existing deployment."""

    updater: Updater[EndpointRow]

    @override
    def entity_id(self) -> str | None:
        return str(self.updater.pk_value)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateDeploymentActionResult(BaseActionResult):
    data: ModelDeploymentData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)
