from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.prometheus_query_preset_category.actions.base import (
    PrometheusQueryPresetCategoryAction,
)


@dataclass
class DeleteCategoryAction(PrometheusQueryPresetCategoryAction):
    category_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.category_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteCategoryActionResult(BaseActionResult):
    category_id: UUID

    @override
    def entity_id(self) -> str | None:
        return None
