from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.prometheus_query_preset_category.actions.base import (
    PrometheusQueryPresetCategoryAction,
)


@dataclass
class SearchCategoriesAction(PrometheusQueryPresetCategoryAction):
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchCategoriesActionResult(BaseActionResult):
    items: list[PrometheusQueryPresetCategoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
