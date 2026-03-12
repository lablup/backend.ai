from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.deployment.actions.replica.base import (
    DeploymentReplicaSingleEntityAction,
    DeploymentReplicaSingleEntityActionResult,
)


@dataclass
class SyncReplicaAction(DeploymentReplicaSingleEntityAction):
    """Action to sync replicas for an existing deployment."""

    deployment_id: UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        return str(self.deployment_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.MODEL_DEPLOYMENT, str(self.deployment_id))


@dataclass
class SyncReplicaActionResult(DeploymentReplicaSingleEntityActionResult):
    success: bool

    @override
    def target_entity_id(self) -> str:
        return ""
