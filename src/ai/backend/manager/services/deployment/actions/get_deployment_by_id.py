from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import PermissionOperationType
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentSingleEntityAction,
    DeploymentSingleEntityActionResult,
)


@dataclass
class GetDeploymentByIdAction(DeploymentSingleEntityAction):
    deployment_id: UUID

    @override
    def target_entity_id(self) -> UUID:
        return self.deployment_id

    @override
    @classmethod
    def permission_operation_type(cls) -> PermissionOperationType:
        return PermissionOperationType.READ


@dataclass
class GetDeploymentByIdActionResult(DeploymentSingleEntityActionResult):
    data: ModelDeploymentData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)
