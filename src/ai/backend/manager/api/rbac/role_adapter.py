"""
Adapters to convert RBAC DTOs to repository Querier objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.rbac import (
    OrderDirection,
    RoleDTO,
    RoleFilter,
    RoleOrder,
    RoleOrderField,
    SearchRolesRequest,
)
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.data.permission.role import RoleData, RoleDetailData
from ai.backend.manager.errors.permission import InvalidOrderField
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.permission_controller.options import (
    RoleConditions,
    RoleOrders,
)

__all__ = ("RoleAdapter",)


class RoleAdapter(BaseFilterAdapter):
    """Adapter for converting role requests to repository queries."""

    def convert_to_dto(self, data: RoleData | RoleDetailData) -> RoleDTO:
        """Convert RoleData to DTO."""
        return RoleDTO(
            id=data.id,
            name=data.name,
            source=data.source,
            status=data.status,
            created_at=data.created_at,
            updated_at=data.updated_at,
            deleted_at=data.deleted_at,
            description=data.description,
        )

    def build_querier(self, request: SearchRolesRequest) -> BatchQuerier:
        """
        Build a Querier for roles from search request.

        Args:
            request: Search request containing filter, order, and pagination

        Returns:
            Querier object with converted conditions, orders, and pagination
        """
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders = [self._convert_order(request.order)] if request.order else []
        pagination = self._build_pagination(request.limit, request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: RoleFilter) -> list[QueryCondition]:
        """Convert role filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        # Name filter
        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                equals_fn=RoleConditions.by_name_equals,
                contains_fn=RoleConditions.by_name_contains,
            )
            if condition is not None:
                conditions.append(condition)

        # Sources filter
        if filter.sources is not None and len(filter.sources) > 0:
            conditions.append(RoleConditions.by_sources(filter.sources))

        # Statuses filter
        if filter.statuses is not None and len(filter.statuses) > 0:
            conditions.append(RoleConditions.by_statuses(filter.statuses))

        return conditions

    def _convert_order(self, order: RoleOrder) -> QueryOrder:
        """Convert role order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        if order.field == RoleOrderField.NAME:
            return RoleOrders.name(ascending=ascending)
        elif order.field == RoleOrderField.CREATED_AT:
            return RoleOrders.created_at(ascending=ascending)
        elif order.field == RoleOrderField.UPDATED_AT:
            return RoleOrders.updated_at(ascending=ascending)
        else:
            raise InvalidOrderField(f"Unknown order field: {order.field}")

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)
