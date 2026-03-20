"""Container registry adapter bridging DTOs and Processors."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.container_registry.request import (
    AdminSearchContainerRegistriesInput,
    ContainerRegistryFilter,
    ContainerRegistryOrder,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    AdminSearchContainerRegistriesPayload,
    ContainerRegistryNode,
)
from ai.backend.common.dto.manager.v2.container_registry.types import ContainerRegistryTypeFilter
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.container_registry.conditions import ContainerRegistryConditions
from ai.backend.manager.models.container_registry.orders import (
    DEFAULT_FORWARD_ORDER,
    TIEBREAKER_ORDER,
    resolve_order,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.services.container_registry.actions.search_container_registries import (
    SearchContainerRegistriesAction,
)

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 10


class ContainerRegistryAdapter(BaseAdapter):
    """Adapter for container registry domain operations."""

    async def admin_search(
        self,
        input: AdminSearchContainerRegistriesInput,
    ) -> AdminSearchContainerRegistriesPayload:
        """Search container registries (admin, no scope) with filters, orders, and pagination.

        Args:
            input: Pydantic DTO with filter, order, and pagination parameters.

        Returns:
            Pydantic payload with items and pagination info.
        """
        querier = self.build_querier(input)

        action_result = (
            await self._processors.container_registry.search_container_registries.wait_for_complete(
                SearchContainerRegistriesAction(querier=querier)
            )
        )

        return AdminSearchContainerRegistriesPayload(
            items=[self._data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def build_querier(self, input: AdminSearchContainerRegistriesInput) -> BatchQuerier:
        """Build a BatchQuerier from the search input DTO."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else [DEFAULT_FORWARD_ORDER]
        orders.append(TIEBREAKER_ORDER)
        pagination = self._build_pagination(input)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: ContainerRegistryFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.registry_name is not None:
            condition = self._convert_string_filter(filter.registry_name)
            if condition is not None:
                conditions.append(condition)
        if filter.type is not None:
            conditions.extend(self._convert_type_filter(filter.type))
        if filter.is_global is not None:
            conditions.append(ContainerRegistryConditions.by_is_global(filter.is_global))
        return conditions

    def _convert_string_filter(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=ContainerRegistryConditions.by_registry_name_contains,
            equals_factory=ContainerRegistryConditions.by_registry_name_equals,
            starts_with_factory=ContainerRegistryConditions.by_registry_name_starts_with,
            ends_with_factory=ContainerRegistryConditions.by_registry_name_ends_with,
        )

    @staticmethod
    def _convert_type_filter(tf: ContainerRegistryTypeFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if tf.equals is not None:
            conditions.append(ContainerRegistryConditions.by_type_equals(tf.equals))
        if tf.in_ is not None:
            conditions.append(ContainerRegistryConditions.by_type_in(tf.in_))
        if tf.not_equals is not None:
            conditions.append(ContainerRegistryConditions.by_type_not_equals(tf.not_equals))
        if tf.not_in is not None:
            conditions.append(ContainerRegistryConditions.by_type_not_in(tf.not_in))
        return conditions

    @staticmethod
    def _convert_orders(order: list[ContainerRegistryOrder]) -> list[QueryOrder]:
        return [resolve_order(o.field, o.direction) for o in order]

    @staticmethod
    def _build_pagination(input: AdminSearchContainerRegistriesInput) -> OffsetPagination:
        return OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )

    async def batch_load_by_ids(
        self, ids: Sequence[uuid.UUID]
    ) -> list[ContainerRegistryNode | None]:
        """Batch load container registries by IDs for DataLoader use.

        Returns ContainerRegistryNode DTOs in the same order as the input ids list.
        """
        if not ids:
            return []
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=len(ids)),
            conditions=[ContainerRegistryConditions.by_ids(ids)],
        )
        action_result = (
            await self._processors.container_registry.search_container_registries.wait_for_complete(
                SearchContainerRegistriesAction(querier=querier)
            )
        )
        registry_map = {item.id: self._data_to_dto(item) for item in action_result.data}
        return [registry_map.get(registry_id) for registry_id in ids]

    @staticmethod
    def _data_to_dto(data: ContainerRegistryData) -> ContainerRegistryNode:
        """Convert data layer type to Pydantic DTO."""
        return ContainerRegistryNode(
            id=data.id,
            url=data.url,
            registry_name=data.registry_name,
            type=data.type,
            project=data.project,
            username=data.username,
            ssl_verify=data.ssl_verify,
            is_global=data.is_global,
            extra=data.extra,
        )
