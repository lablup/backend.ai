"""Action for destroying deployments."""

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import PermissionOperationType
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentSingleEntityAction,
    DeploymentSingleEntityActionResult,
)


@dataclass
class DestroyDeploymentAction(DeploymentSingleEntityAction):
    """Action to destroy an existing deployment."""

    endpoint_id: UUID

    @override
    def target_entity_id(self) -> UUID:
        return self.endpoint_id

    @override
    @classmethod
    def permission_operation_type(cls) -> PermissionOperationType:
        return PermissionOperationType.DELETE


@dataclass
class DestroyDeploymentActionResult(DeploymentSingleEntityActionResult):
    success: bool

    @override
    def entity_id(self) -> str | None:
        return None
