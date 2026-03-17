"""Object storage domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.object_storage.request import (
    AdminSearchObjectStoragesInput,
    ObjectStorageFilter,
    ObjectStorageOrder,
)
from ai.backend.common.dto.manager.v2.object_storage.response import (
    AdminSearchObjectStoragesPayload,
    ObjectStorageNode,
)
from ai.backend.common.dto.manager.v2.object_storage.types import OrderDirection
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.conditions import ObjectStorageConditions
from ai.backend.manager.models.object_storage.orders import ObjectStorageOrders
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.services.object_storage.actions.search import SearchObjectStoragesAction

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 50


class ObjectStorageAdapter(BaseAdapter):
    """Adapter for object storage domain operations."""

    async def admin_search(
        self, input: AdminSearchObjectStoragesInput
    ) -> AdminSearchObjectStoragesPayload:
        """Search object storages with admin scope.

        Args:
            input: Pydantic DTO with filter, order, and pagination parameters.

        Returns:
            Pydantic payload with items and pagination info.
        """
        querier = self.build_querier(input)

        action_result = (
            await self._processors.object_storage.search_object_storages.wait_for_complete(
                SearchObjectStoragesAction(querier=querier)
            )
        )

        return AdminSearchObjectStoragesPayload(
            items=[self._data_to_dto(item) for item in action_result.storages],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def build_querier(self, input: AdminSearchObjectStoragesInput) -> BatchQuerier:
        """Build a BatchQuerier from the search input DTO."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        pagination = self._build_pagination(input)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: ObjectStorageFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []

        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=ObjectStorageConditions.by_name_contains,
                equals_factory=ObjectStorageConditions.by_name_equals,
                starts_with_factory=ObjectStorageConditions.by_name_starts_with,
                ends_with_factory=ObjectStorageConditions.by_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.host is not None:
            condition = self.convert_string_filter(
                filter.host,
                contains_factory=ObjectStorageConditions.by_host_contains,
                equals_factory=ObjectStorageConditions.by_host_equals,
                starts_with_factory=ObjectStorageConditions.by_host_starts_with,
                ends_with_factory=ObjectStorageConditions.by_host_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        return conditions

    @staticmethod
    def _convert_orders(orders: list[ObjectStorageOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for order in orders:
            ascending = order.direction == OrderDirection.ASC
            match order.field.value:
                case "name":
                    result.append(ObjectStorageOrders.name(ascending))
                case "host":
                    result.append(ObjectStorageOrders.host(ascending))
                case "region":
                    result.append(ObjectStorageOrders.region(ascending))
        return result

    @staticmethod
    def _build_pagination(input: AdminSearchObjectStoragesInput) -> OffsetPagination:
        return OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )

    @staticmethod
    def _data_to_dto(data: ObjectStorageData) -> ObjectStorageNode:
        """Convert data layer type to Pydantic DTO."""
        return ObjectStorageNode(
            id=data.id,
            name=data.name,
            host=data.host,
            access_key=data.access_key,
            secret_key=data.secret_key,
            endpoint=data.endpoint,
            region=data.region,
        )
