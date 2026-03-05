"""
Adapter to convert ResourceSlotType DTOs to repository Querier objects.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.resource_slot.request import (
    OrderDirection,
    ResourceSlotTypeFilter,
    ResourceSlotTypeOrder,
    ResourceSlotTypeOrderField,
    SearchResourceSlotTypesRequest,
)
from ai.backend.common.dto.manager.resource_slot.response import (
    NumberFormatDTO,
    ResourceSlotTypeDTO,
)
from ai.backend.manager.api.rest.adapter import BaseFilterAdapter
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.resource_slot.query import QueryConditions, QueryOrders

__all__ = ("ResourceSlotAdapter",)


class ResourceSlotAdapter(BaseFilterAdapter):
    """Adapter for converting resource slot type requests to repository queries."""

    def convert_to_dto(self, data: ResourceSlotTypeData) -> ResourceSlotTypeDTO:
        """Convert ResourceSlotTypeData to DTO."""
        return ResourceSlotTypeDTO(
            slot_name=data.slot_name,
            slot_type=data.slot_type,
            display_name=data.display_name,
            description=data.description,
            display_unit=data.display_unit,
            display_icon=data.display_icon,
            number_format=NumberFormatDTO(
                binary=data.number_format.binary,
                round_length=data.number_format.round_length,
            ),
            rank=data.rank,
        )

    def build_querier(self, request: SearchResourceSlotTypesRequest) -> BatchQuerier:
        """Build a BatchQuerier from search request."""
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders = [self._convert_order(o) for o in request.order] if request.order else []

        return BatchQuerier(
            conditions=conditions,
            orders=orders,
            pagination=OffsetPagination(limit=request.limit, offset=request.offset),
        )

    def _convert_filter(self, filter: ResourceSlotTypeFilter) -> list[QueryCondition]:
        """Convert resource slot type filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        if filter.slot_name is not None:
            condition = self.convert_string_filter(
                filter.slot_name,
                contains_factory=QueryConditions.by_slot_name_contains,
                equals_factory=QueryConditions.by_slot_name_equals,
                starts_with_factory=QueryConditions.by_slot_name_starts_with,
                ends_with_factory=QueryConditions.by_slot_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.slot_type is not None:
            condition = self.convert_string_filter(
                filter.slot_type,
                contains_factory=QueryConditions.by_slot_type_contains,
                equals_factory=QueryConditions.by_slot_type_equals,
                starts_with_factory=QueryConditions.by_slot_type_starts_with,
                ends_with_factory=QueryConditions.by_slot_type_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.display_name is not None:
            condition = self.convert_string_filter(
                filter.display_name,
                contains_factory=QueryConditions.by_display_name_contains,
                equals_factory=QueryConditions.by_display_name_equals,
                starts_with_factory=QueryConditions.by_display_name_starts_with,
                ends_with_factory=QueryConditions.by_display_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        return conditions

    def _convert_order(self, order: ResourceSlotTypeOrder) -> QueryOrder:
        """Convert resource slot type order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        if order.field == ResourceSlotTypeOrderField.SLOT_NAME:
            return QueryOrders.slot_name(ascending=ascending)
        if order.field == ResourceSlotTypeOrderField.RANK:
            return QueryOrders.rank(ascending=ascending)
        if order.field == ResourceSlotTypeOrderField.DISPLAY_NAME:
            return QueryOrders.display_name(ascending=ascending)
        raise ValueError(f"Unknown order field: {order.field}")
