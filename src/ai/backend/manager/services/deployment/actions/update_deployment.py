from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.repositories.base import Updater
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentSingleEntityAction,
    DeploymentSingleEntityActionResult,
)


@dataclass
class UpdateDeploymentAction(DeploymentSingleEntityAction):
    """Action to update an existing deployment."""

    updater: Updater[EndpointRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        return str(self.updater.pk_value)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.MODEL_DEPLOYMENT, str(self.updater.pk_value))


@dataclass
class UpdateDeploymentActionResult(DeploymentSingleEntityActionResult):
    data: ModelDeploymentData

    @override
    def target_entity_id(self) -> str:
        return str(self.data.id)
