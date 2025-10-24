from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types import (
    ModelReplicaData,
)
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class BatchLoadReplicasByDeploymentIdsAction(DeploymentBaseAction):
    deployment_ids: list[UUID]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "batch_load_replicas_by_deployment_ids"


@dataclass
class BatchLoadReplicasByDeploymentIdsActionResult(BaseActionResult):
    data: dict[UUID, list[ModelReplicaData]]

    @override
    def entity_id(self) -> Optional[str]:
        return None
