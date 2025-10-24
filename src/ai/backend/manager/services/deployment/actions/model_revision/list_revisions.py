from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types import ModelRevisionData
from ai.backend.manager.repositories.deployment.types.types import (
    ModelRevisionFilterOptions,
    ModelRevisionOrderingOptions,
)
from ai.backend.manager.services.deployment.actions.model_revision.base import (
    ModelRevisionBaseAction,
)
from ai.backend.manager.types import PaginationOptions


@dataclass
class ListRevisionsAction(ModelRevisionBaseAction):
    pagination: PaginationOptions
    ordering: Optional[ModelRevisionOrderingOptions] = None
    filters: Optional[ModelRevisionFilterOptions] = None

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list_revisions"


@dataclass
class ListRevisionsActionResult(BaseActionResult):
    data: list[ModelRevisionData]
    total_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return None
