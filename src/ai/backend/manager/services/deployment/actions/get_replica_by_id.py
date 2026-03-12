from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ModelReplicaData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.deployment.actions.replica.base import (
    DeploymentReplicaSingleEntityAction,
    DeploymentReplicaSingleEntityActionResult,
)


@dataclass
class GetReplicaByIdAction(DeploymentReplicaSingleEntityAction):
    replica_id: UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def target_entity_id(self) -> str:
        return str(self.replica_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.MODEL_DEPLOYMENT, str(self.replica_id))


@dataclass
class GetReplicaByIdActionResult(DeploymentReplicaSingleEntityActionResult):
    data: ModelReplicaData | None

    @override
    def target_entity_id(self) -> str:
        return str(self.data.id) if self.data else ""
