import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryRepository,
)
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

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class PrometheusQueryPresetCategoryService:
    _repository: PrometheusQueryPresetCategoryRepository

    def __init__(
        self,
        repository: PrometheusQueryPresetCategoryRepository,
    ) -> None:
        self._repository = repository

    async def create_category(self, action: CreateCategoryAction) -> CreateCategoryActionResult:
        category_data = await self._repository.create(action.creator)
        return CreateCategoryActionResult(category=category_data)

    async def get_category(self, action: GetCategoryAction) -> GetCategoryActionResult:
        category_data = await self._repository.get_by_id(action.category_id)
        return GetCategoryActionResult(category=category_data)

    async def search_categories(
        self, action: SearchCategoriesAction
    ) -> SearchCategoriesActionResult:
        result = await self._repository.search(action.querier)
        return SearchCategoriesActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def delete_category(self, action: DeleteCategoryAction) -> DeleteCategoryActionResult:
        await self._repository.delete(action.category_id)
        return DeleteCategoryActionResult(category_id=action.category_id)
