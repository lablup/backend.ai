"""Prometheus query preset category domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

from collections.abc import Sequence
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
from ai.backend.common.identifier.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryData,
)
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.models.prometheus_query_preset_category.conditions import (
    PrometheusQueryPresetCategoryConditions,
)
from ai.backend.manager.models.prometheus_query_preset_category.creators import (
    PrometheusQueryPresetCategoryCreator,
)
from ai.backend.manager.models.prometheus_query_preset_category.orders import (
    PrometheusQueryPresetCategoryOrders,
)
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.repositories.base import (
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.prometheus_query_preset_category.searchers import (
    PrometheusQueryPresetCategorySearcher,
)
from ai.backend.manager.services.prometheus_query_preset_category.actions import (
    CreateCategoryAction,
    GetCategoryAction,
    PurgeCategoryAction,
    SearchCategoriesAction,
)


class PrometheusQueryPresetCategoryAdapter(BaseAdapter):
    """Adapter for prometheus query preset category domain operations."""

    async def batch_load_by_ids(self, ids: Sequence[UUID]) -> list[CategoryNode | None]:
        if not ids:
            return []
        searcher = PrometheusQueryPresetCategorySearcher(
            pagination=OffsetPagination(limit=len(ids)),
            conditions=[PrometheusQueryPresetCategoryConditions.by_ids(ids)],
        )
        action_result = (
            await self._processors.prometheus_query_preset_category.global_search_categories.run(
                SearchCategoriesAction(searcher=searcher)
            )
        )
        category_map = {item.id: self._data_to_dto(item) for item in action_result.items}
        return [
            category_map.get(PrometheusQueryPresetCategoryID(category_id)) for category_id in ids
        ]

    async def create(self, input: CreateCategoryInput) -> CreateCategoryPayload:
        """Create a new prometheus query preset category."""
        creator = PrometheusQueryPresetCategoryCreator(
            name=input.name,
            description=input.description,
        )

        action_result = (
            await self._processors.prometheus_query_preset_category.global_create_category.run(
                CreateCategoryAction(creator=creator)
            )
        )

        return CreateCategoryPayload(item=self._data_to_dto(action_result.data))

    async def search(self, input: SearchCategoriesInput) -> SearchCategoriesPayload:
        """Search prometheus query preset categories.

        Available to any authenticated user via REST/GQL — categories are a
        shared catalog for organizing metric query templates.
        """
        searcher = self.build_searcher(input)

        action_result = (
            await self._processors.prometheus_query_preset_category.global_search_categories.run(
                SearchCategoriesAction(searcher=searcher)
            )
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
            await self._processors.prometheus_query_preset_category.global_get_category.run(
                GetCategoryAction(category_id=PrometheusQueryPresetCategoryID(category_id))
            )
        )

        return GetCategoryPayload(item=self._data_to_dto(action_result.data))

    async def delete(self, input: DeleteCategoryInput) -> DeleteCategoryPayload:
        """Remove a category by ID."""
        action_result = await self._processors.prometheus_query_preset_category.purge_category.run(
            PurgeCategoryAction(category_id=PrometheusQueryPresetCategoryID(input.id))
        )

        return DeleteCategoryPayload(id=action_result.data.id)

    _PAGINATION_SPEC = PaginationSpec(
        forward_order=PrometheusQueryPresetCategoryOrders.created_at(ascending=False),
        backward_order=PrometheusQueryPresetCategoryOrders.created_at(ascending=True),
        forward_condition_factory=PrometheusQueryPresetCategoryConditions.by_cursor_forward,
        backward_condition_factory=PrometheusQueryPresetCategoryConditions.by_cursor_backward,
        tiebreaker_order=PrometheusQueryPresetCategoryRow.id.asc(),
    )

    def build_searcher(self, input: SearchCategoriesInput) -> PrometheusQueryPresetCategorySearcher:
        """Build the searcher from the search input DTO."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        return self._build_searcher(
            PrometheusQueryPresetCategorySearcher,
            conditions=conditions,
            orders=orders,
            pagination_spec=self._PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

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

        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_filter(sub_filter))
        if filter.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_conditions.extend(self._convert_filter(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if filter.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_conditions.extend(self._convert_filter(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))

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
    def _data_to_dto(data: PrometheusQueryPresetCategoryData) -> CategoryNode:
        """Convert data layer type to Pydantic DTO."""
        return CategoryNode(
            id=data.id,
            name=data.name,
            description=data.description,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )
