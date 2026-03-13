"""Action for destroying deployments."""

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import OperationType, RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.deployment.actions.base import (
    DeploymentSingleEntityAction,
    DeploymentSingleEntityActionResult,
)


@dataclass
class DestroyDeploymentAction(DeploymentSingleEntityAction):
    """Action to destroy an existing deployment."""

    endpoint_id: UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def target_entity_id(self) -> str:
        return str(self.endpoint_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.DEPLOYMENT, str(self.endpoint_id))


@dataclass
class DestroyDeploymentActionResult(DeploymentSingleEntityActionResult):
    success: bool
    _endpoint_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self._endpoint_id)

    @override
    def target_entity_id(self) -> str:
        return str(self._endpoint_id)
