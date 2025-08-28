from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types import ModelRevisionData
from ai.backend.manager.repositories.deployment.filtering import (
    ModelRevisionFilterOptions,
)
from ai.backend.manager.repositories.deployment.ordering import (
    ModelRevisionOrderingOptions,
)
from ai.backend.manager.repositories.types import PaginationOptions
from ai.backend.manager.services.deployment.actions.base import DeploymentBaseAction


@dataclass
class ListModelRevisionsAction(DeploymentBaseAction):
    pagination: PaginationOptions
    ordering: Optional[ModelRevisionOrderingOptions] = None
    filters: Optional[ModelRevisionFilterOptions] = None

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list"


@dataclass
class ListModelRevisionsActionResult(BaseActionResult):
    data: list[ModelRevisionData]
    # Note: Total number of ModelRevisions, this is not equals to len(data)
    total_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return None
