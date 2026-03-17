"""Domain adapter bridging DTOs and Processors."""

from __future__ import annotations

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.domain.request import (
    AdminSearchDomainsInput,
    DomainFilter,
    DomainOrder,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    AdminSearchDomainsPayload,
    DomainBasicInfo,
    DomainLifecycleInfo,
    DomainNode,
    DomainRegistryInfo,
)
from ai.backend.common.dto.manager.v2.domain.types import DomainOrderField, OrderDirection
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.conditions import DomainConditions
from ai.backend.manager.models.domain.orders import DomainOrders
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.services.domain.actions.search_domains import SearchDomainsAction

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 10


class DomainAdapter(BaseAdapter):
    """Adapter for domain operations."""

    async def admin_search(
        self,
        input: AdminSearchDomainsInput,
    ) -> AdminSearchDomainsPayload:
        """Search domains (admin, no scope) with filters, orders, and pagination.

        Args:
            input: Pydantic DTO with filter, order, and pagination parameters.

        Returns:
            Pydantic payload with items and pagination info.
        """
        querier = self.build_querier(input)

        action_result = await self._processors.domain.search_domains.wait_for_complete(
            SearchDomainsAction(querier=querier)
        )

        return AdminSearchDomainsPayload(
            items=[self._domain_data_to_node(item) for item in action_result.items],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def build_querier(self, input: AdminSearchDomainsInput) -> BatchQuerier:
        """Build a BatchQuerier from the search input DTO."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        pagination = self._build_pagination(input)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: DomainFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.name is not None:
            condition = self._convert_name_filter(filter.name)
            if condition is not None:
                conditions.append(condition)
        if filter.is_active is not None:
            conditions.append(DomainConditions.by_is_active(filter.is_active))
        return conditions

    def _convert_name_filter(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=DomainConditions.by_name_contains,
            equals_factory=DomainConditions.by_name_equals,
            starts_with_factory=DomainConditions.by_name_starts_with,
            ends_with_factory=DomainConditions.by_name_ends_with,
        )

    @staticmethod
    def _convert_orders(order: list[DomainOrder]) -> list[QueryOrder]:
        return [_resolve_order(o.field, o.direction) for o in order]

    @staticmethod
    def _build_pagination(input: AdminSearchDomainsInput) -> OffsetPagination:
        return OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )

    @staticmethod
    def _domain_data_to_node(data: DomainData) -> DomainNode:
        """Convert data layer type to Pydantic DTO."""
        return DomainNode(
            id=data.name,
            basic_info=DomainBasicInfo(
                name=data.name,
                description=data.description,
                integration_id=data.integration_id,
            ),
            registry=DomainRegistryInfo(
                allowed_docker_registries=data.allowed_docker_registries,
            ),
            lifecycle=DomainLifecycleInfo(
                is_active=data.is_active,
                created_at=data.created_at,
                modified_at=data.modified_at,
            ),
        )


def _resolve_order(field: DomainOrderField, direction: OrderDirection) -> QueryOrder:
    """Resolve a DomainOrderField + OrderDirection pair to a QueryOrder."""
    ascending = direction == OrderDirection.ASC
    match field:
        case DomainOrderField.NAME:
            return DomainOrders.name(ascending)
        case DomainOrderField.CREATED_AT:
            return DomainOrders.created_at(ascending)
        case DomainOrderField.MODIFIED_AT:
            return DomainOrders.modified_at(ascending)
