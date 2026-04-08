"""Service catalog adapter bridging DTOs and Processors."""

from __future__ import annotations

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.service_catalog.request import (
    AdminSearchServiceCatalogsInput,
    ServiceCatalogFilter,
    ServiceCatalogOrder,
)
from ai.backend.common.dto.manager.v2.service_catalog.response import (
    AdminSearchServiceCatalogsPayload,
    ServiceCatalogNode,
)
from ai.backend.common.dto.manager.v2.service_catalog.types import (
    EndpointInfo,
    ServiceCatalogStatusFilter,
)
from ai.backend.manager.data.service_catalog.types import (
    ServiceCatalogData,
)
from ai.backend.manager.models.service_catalog.conditions import ServiceCatalogConditions
from ai.backend.manager.models.service_catalog.orders import (
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
from ai.backend.manager.services.service_catalog.actions.search import (
    SearchServiceCatalogsAction,
)

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 10


class ServiceCatalogAdapter(BaseAdapter):
    """Adapter for service catalog domain operations."""

    async def admin_search(
        self,
        input: AdminSearchServiceCatalogsInput,
    ) -> AdminSearchServiceCatalogsPayload:
        """Search service catalog entries (admin, no scope) with filters, orders, and pagination.

        Args:
            input: Pydantic DTO with filter, order, and pagination parameters.

        Returns:
            Pydantic payload with items and pagination info.
        """
        querier = self.build_querier(input)

        action_result = (
            await self._processors.service_catalog.search_service_catalogs.wait_for_complete(
                SearchServiceCatalogsAction(querier=querier)
            )
        )

        return AdminSearchServiceCatalogsPayload(
            items=[self._data_to_dto(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def build_querier(self, input: AdminSearchServiceCatalogsInput) -> BatchQuerier:
        """Build a BatchQuerier from the search input DTO."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else [DEFAULT_FORWARD_ORDER]
        orders.append(TIEBREAKER_ORDER)
        pagination = self._build_pagination(input)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: ServiceCatalogFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.service_group is not None:
            condition = self._convert_string_filter(filter.service_group)
            if condition is not None:
                conditions.append(condition)
        if filter.status is not None:
            conditions.extend(self._convert_status_filter(filter.status))
        return conditions

    def _convert_string_filter(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=ServiceCatalogConditions.by_service_group_contains,
            equals_factory=ServiceCatalogConditions.by_service_group_equals,
            starts_with_factory=ServiceCatalogConditions.by_service_group_starts_with,
            ends_with_factory=ServiceCatalogConditions.by_service_group_ends_with,
            in_factory=ServiceCatalogConditions.by_service_group_in,
        )

    @staticmethod
    def _convert_status_filter(sf: ServiceCatalogStatusFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if sf.equals is not None:
            conditions.append(ServiceCatalogConditions.by_status_equals(sf.equals))
        if sf.in_ is not None:
            conditions.append(ServiceCatalogConditions.by_status_in(sf.in_))
        if sf.not_equals is not None:
            conditions.append(ServiceCatalogConditions.by_status_not_equals(sf.not_equals))
        if sf.not_in is not None:
            conditions.append(ServiceCatalogConditions.by_status_not_in(sf.not_in))
        return conditions

    @staticmethod
    def _convert_orders(order: list[ServiceCatalogOrder]) -> list[QueryOrder]:
        return [resolve_order(o.field, o.direction) for o in order]

    @staticmethod
    def _build_pagination(input: AdminSearchServiceCatalogsInput) -> OffsetPagination:
        return OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )

    @staticmethod
    def _data_to_dto(data: ServiceCatalogData) -> ServiceCatalogNode:
        """Convert data layer type to Pydantic DTO."""
        return ServiceCatalogNode(
            id=data.id,
            service_group=data.service_group,
            instance_id=data.instance_id,
            display_name=data.display_name,
            version=data.version,
            labels=data.labels,
            status=data.status,
            startup_time=data.startup_time,
            registered_at=data.registered_at,
            last_heartbeat=data.last_heartbeat,
            config_hash=data.config_hash,
            endpoints=[
                EndpointInfo(
                    id=ep.id,
                    role=ep.role,
                    scope=ep.scope,
                    address=ep.address,
                    port=ep.port,
                    protocol=ep.protocol,
                    metadata=ep.metadata,
                )
                for ep in data.endpoints
            ],
        )
