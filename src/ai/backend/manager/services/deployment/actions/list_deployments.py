from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types_ import ModelDeploymentData
from ai.backend.manager.repositories.deployment.filtering import DeploymentFilterOptions
from ai.backend.manager.repositories.deployment.ordering import DeploymentOrderingOptions
from ai.backend.manager.repositories.types import PaginationOptions
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class ListDeploymentsAction(DeploymentBaseAction):
    pagination: PaginationOptions
    ordering: Optional[DeploymentOrderingOptions] = None
    filters: Optional[DeploymentFilterOptions] = None

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list"


@dataclass
class ListDeploymentsActionResult(BaseActionResult):
    data: list[ModelDeploymentData]
    # Note: Total number of Deployments, this is not equals to len(data)
    total_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return None
