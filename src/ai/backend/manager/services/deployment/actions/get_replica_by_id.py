from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ModelReplicaData
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class GetReplicaByIdAction(DeploymentBaseAction):
    replica_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.replica_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetReplicaByIdActionResult(BaseActionResult):
    data: ModelReplicaData | None

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id) if self.data else None
