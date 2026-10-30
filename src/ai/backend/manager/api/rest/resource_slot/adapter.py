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
from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.resource_slot.searchable_fields import (
    ResourceSlotTypeSearchableFields,
)
from ai.backend.manager.models.resource_slot.searchers import ResourceSlotTypeSearcher
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.repositories.base.filter_adapter import BaseFilterAdapter

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

    def build_searcher(self, request: SearchResourceSlotTypesRequest) -> ResourceSlotTypeSearcher:
        """Build a Searcher from search request."""
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders = [self._convert_order(o) for o in request.order] if request.order else []

        return ResourceSlotTypeSearcher(
            conditions=conditions,
            orders=orders,
            pagination=OffsetPagination(limit=request.limit, offset=request.offset),
        )

    def _convert_filter(self, filter: ResourceSlotTypeFilter) -> list[QueryCondition]:
        """Convert resource slot type filter to list of query conditions."""
        fields = ResourceSlotTypeSearchableFields.own
        return [
            *self.apply_string_filter(filter.slot_name, fields.slot_name.filter),
            *self.apply_string_filter(filter.slot_type, fields.slot_type.filter),
            *self.apply_string_filter(filter.display_name, fields.display_name.filter),
        ]

    def _convert_order(self, order: ResourceSlotTypeOrder) -> QueryOrder:
        """Convert resource slot type order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        fields = ResourceSlotTypeSearchableFields.own
        if order.field == ResourceSlotTypeOrderField.SLOT_NAME:
            return fields.slot_name.order.apply(ascending)
        if order.field == ResourceSlotTypeOrderField.RANK:
            return fields.rank.order.apply(ascending)
        if order.field == ResourceSlotTypeOrderField.DISPLAY_NAME:
            return fields.display_name.order.apply(ascending)
        raise ValueError(f"Unknown order field: {order.field}")
