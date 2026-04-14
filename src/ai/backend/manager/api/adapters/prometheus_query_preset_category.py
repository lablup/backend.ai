"""Prometheus query preset category domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.request import (
    CategoryFilter,
    CategoryOrder,
    CreateCategoryInput,
    DeleteCategoryInput,
    SearchCategoriesInput,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.response import (
    CategoryNode,
    CreateCategoryPayload,
    DeleteCategoryPayload,
    GetCategoryPayload,
    SearchCategoriesPayload,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.types import (
    OrderDirection,
)
from ai.backend.manager.data.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.models.prometheus_query_preset_category.conditions import (
    PrometheusQueryPresetCategoryConditions,
)
from ai.backend.manager.models.prometheus_query_preset_category.orders import (
    PrometheusQueryPresetCategoryOrders,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.prometheus_query_preset_category.creators import (
    PrometheusQueryPresetCategoryCreatorSpec,
)
from ai.backend.manager.services.prometheus_query_preset_category.actions import (
    CreateCategoryAction,
    DeleteCategoryAction,
    GetCategoryAction,
    SearchCategoriesAction,
)

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 50


class PrometheusQueryPresetCategoryAdapter(BaseAdapter):
    """Adapter for prometheus query preset category domain operations."""

    async def create(self, input: CreateCategoryInput) -> CreateCategoryPayload:
        """Create a new prometheus query preset category."""
        creator: Creator[PrometheusQueryPresetCategoryRow] = Creator(
            spec=PrometheusQueryPresetCategoryCreatorSpec(
                name=input.name,
                description=input.description,
            )
        )

        action_result = await self._processors.prometheus_query_preset_category.create_category.wait_for_complete(
            CreateCategoryAction(creator=creator)
        )

        return CreateCategoryPayload(item=self._data_to_dto(action_result.category))

    async def search(self, input: SearchCategoriesInput) -> SearchCategoriesPayload:
        """Search prometheus query preset categories.

        Available to any authenticated user via REST/GQL — categories are a
        shared catalog for organizing metric query templates.
        """
        querier = self.build_querier(input)

        action_result = await self._processors.prometheus_query_preset_category.search_categories.wait_for_complete(
            SearchCategoriesAction(querier=querier)
        )

        return SearchCategoriesPayload(
            items=[self._data_to_dto(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def get(self, category_id: UUID) -> GetCategoryPayload:
        """Get a single category by ID."""
        action_result = (
            await self._processors.prometheus_query_preset_category.get_category.wait_for_complete(
                GetCategoryAction(category_id=category_id)
            )
        )

        return GetCategoryPayload(item=self._data_to_dto(action_result.category))

    async def delete(self, input: DeleteCategoryInput) -> DeleteCategoryPayload:
        """Delete a category by ID."""
        action_result = await self._processors.prometheus_query_preset_category.delete_category.wait_for_complete(
            DeleteCategoryAction(category_id=input.id)
        )

        return DeleteCategoryPayload(id=action_result.category_id)

    def build_querier(self, input: SearchCategoriesInput) -> BatchQuerier:
        """Build a BatchQuerier from the search input DTO."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        pagination = self._build_pagination(input)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: CategoryFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=PrometheusQueryPresetCategoryConditions.by_name_contains,
                equals_factory=PrometheusQueryPresetCategoryConditions.by_name_equals,
                starts_with_factory=PrometheusQueryPresetCategoryConditions.by_name_starts_with,
                ends_with_factory=PrometheusQueryPresetCategoryConditions.by_name_ends_with,
                in_factory=PrometheusQueryPresetCategoryConditions.by_name_in,
            )
            if condition is not None:
                conditions.append(condition)

        return conditions

    @staticmethod
    def _convert_orders(orders: list[CategoryOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field.value:
                case "name":
                    result.append(PrometheusQueryPresetCategoryOrders.name(ascending))
                case "created_at":
                    result.append(PrometheusQueryPresetCategoryOrders.created_at(ascending))
        return result

    @staticmethod
    def _build_pagination(input: SearchCategoriesInput) -> OffsetPagination:
        return OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )

    @staticmethod
    def _data_to_dto(data: PrometheusQueryPresetCategoryData) -> CategoryNode:
        """Convert data layer type to Pydantic DTO."""
        return CategoryNode(
            id=data.id,
            name=data.name,
            description=data.description,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
