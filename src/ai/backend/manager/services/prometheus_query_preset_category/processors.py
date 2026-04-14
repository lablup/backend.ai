from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.prometheus_query_preset_category.actions import (
    CreateCategoryAction,
    CreateCategoryActionResult,
    DeleteCategoryAction,
    DeleteCategoryActionResult,
    GetCategoryAction,
    GetCategoryActionResult,
    SearchCategoriesAction,
    SearchCategoriesActionResult,
)
from ai.backend.manager.services.prometheus_query_preset_category.service import (
    PrometheusQueryPresetCategoryService,
)


class PrometheusQueryPresetCategoryProcessors(AbstractProcessorPackage):
    create_category: ActionProcessor[CreateCategoryAction, CreateCategoryActionResult]
    get_category: ActionProcessor[GetCategoryAction, GetCategoryActionResult]
    search_categories: ActionProcessor[SearchCategoriesAction, SearchCategoriesActionResult]
    delete_category: ActionProcessor[DeleteCategoryAction, DeleteCategoryActionResult]

    def __init__(
        self,
        service: PrometheusQueryPresetCategoryService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.create_category = ActionProcessor(service.create_category, action_monitors)
        self.get_category = ActionProcessor(service.get_category, action_monitors)
        self.search_categories = ActionProcessor(service.search_categories, action_monitors)
        self.delete_category = ActionProcessor(service.delete_category, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateCategoryAction.spec(),
            GetCategoryAction.spec(),
            SearchCategoriesAction.spec(),
            DeleteCategoryAction.spec(),
        ]
