from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import ModelReplicaData
from ai.backend.manager.services.deployment.actions.replica.base import DeploymentReplicaBaseAction


@dataclass
class GetReplicaByIdAction(DeploymentReplicaBaseAction):
    replica_id: UUID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_replica_by_id"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetReplicaByIdActionResult:
    data: ModelReplicaData | None
