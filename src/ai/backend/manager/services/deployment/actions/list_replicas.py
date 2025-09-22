from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types import ModelReplicaData
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction
from ai.backend.manager.types import PaginationOptions


@dataclass
class ListReplicasAction(DeploymentBaseAction):
    pagination: PaginationOptions

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list_deployments"


@dataclass
class ListReplicasActionResult(BaseActionResult):
    data: list[ModelReplicaData]
    # Note: Total number of replicas, this is not equals to len(data)
    total_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return None
