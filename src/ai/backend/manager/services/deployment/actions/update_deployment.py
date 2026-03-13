from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import PermissionOperationType
from ai.backend.manager.data.deployment.types import ModelDeploymentData
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
    def target_entity_id(self) -> UUID:
        return UUID(str(self.updater.pk_value))

    @override
    @classmethod
    def permission_operation_type(cls) -> PermissionOperationType:
        return PermissionOperationType.UPDATE


@dataclass
class UpdateDeploymentActionResult(DeploymentSingleEntityActionResult):
    data: ModelDeploymentData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)

    @override
    def target_entity_id(self) -> str:
        return str(self.data.id)
