from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.prometheus_query_preset_category.actions.base import (
    PrometheusQueryPresetCategoryAction,
)


@dataclass
class CreateCategoryAction(PrometheusQueryPresetCategoryAction):
    creator: Creator[PrometheusQueryPresetCategoryRow]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateCategoryActionResult(BaseActionResult):
    category: PrometheusQueryPresetCategoryData

    @override
    def entity_id(self) -> str | None:
        return str(self.category.id)
