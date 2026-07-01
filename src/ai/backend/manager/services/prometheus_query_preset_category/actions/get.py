from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.services.prometheus_query_preset_category.actions.base import (
    PrometheusQueryPresetCategoryAction,
)


@dataclass
class GetCategoryAction(PrometheusQueryPresetCategoryAction):
    category_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.category_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetCategoryActionResult(BaseActionResult):
    category: PrometheusQueryPresetCategoryData

    @override
    def entity_id(self) -> str | None:
        return str(self.category.id)
