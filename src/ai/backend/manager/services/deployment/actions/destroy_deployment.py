"""Action for destroying deployments."""

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentSingleEntityAction,
    DeploymentSingleEntityActionResult,
)


@dataclass
class DestroyDeploymentAction(DeploymentSingleEntityAction):
    """Action to destroy an existing deployment."""

    endpoint_id: uuid.UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def target_entity_id(self) -> str:
        return str(self.endpoint_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.MODEL_DEPLOYMENT, str(self.endpoint_id))


@dataclass
class DestroyDeploymentActionResult(DeploymentSingleEntityActionResult):
    success: bool

    @override
    def target_entity_id(self) -> str:
        return ""
