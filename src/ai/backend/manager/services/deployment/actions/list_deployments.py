from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types import ModelDeploymentData
from ai.backend.manager.repositories.deployment.types.types import (
    DeploymentFilterOptions,
    DeploymentOrderingOptions,
)
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction
from ai.backend.manager.types import PaginationOptions


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
        return "list_deployments"


@dataclass
class ListDeploymentsActionResult(BaseActionResult):
    data: list[ModelDeploymentData]
    # Note: Total number of deployments, this is not equals to len(data)
    total_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return None
