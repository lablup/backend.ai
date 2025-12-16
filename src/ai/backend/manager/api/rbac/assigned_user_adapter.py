"""
Adapter to convert assigned user DTOs to repository Querier objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.rbac import (
    AssignedUserDTO,
    AssignedUserFilter,
    AssignedUserOrder,
    AssignedUserOrderField,
    OrderDirection,
    SearchUsersAssignedToRoleRequest,
)
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.data.permission.role import AssignedUserData
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.permission_controller.options import (
    AssignedUserConditions,
    AssignedUserOrders,
)

__all__ = ("AssignedUserAdapter",)


class AssignedUserAdapter(BaseFilterAdapter):
    """Adapter for converting assigned user requests to repository queries."""

    def convert_to_dto(self, data: AssignedUserData) -> AssignedUserDTO:
        """Convert AssignedUserData to DTO."""
        return AssignedUserDTO(
            user_id=data.user_id,
            username=data.username,
            email=data.email,
            granted_by=data.granted_by,
            granted_at=data.granted_at,
        )

    def build_querier(self, request: SearchUsersAssignedToRoleRequest) -> BatchQuerier:
        """
        Build a Querier for assigned users from search request.

        Args:
            request: Search request containing filter, order, and pagination

        Returns:
            Querier object with converted conditions, orders, and pagination
        """
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders = [self._convert_order(request.order)] if request.order else []
        pagination = self._build_pagination(request.limit, request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: AssignedUserFilter) -> list[QueryCondition]:
        """Convert assigned user filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        # Username filter
        if filter.username is not None:
            condition = self.convert_string_filter(
                filter.username,
                equals_fn=AssignedUserConditions.by_username_equals,
                contains_fn=AssignedUserConditions.by_username_contains,
            )
            if condition is not None:
                conditions.append(condition)

        # Email filter
        if filter.email is not None:
            condition = self.convert_string_filter(
                filter.email,
                equals_fn=AssignedUserConditions.by_email_equals,
                contains_fn=AssignedUserConditions.by_email_contains,
            )
            if condition is not None:
                conditions.append(condition)

        return conditions

    def _convert_order(self, order: AssignedUserOrder) -> QueryOrder:
        """Convert assigned user order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        if order.field == AssignedUserOrderField.USERNAME:
            return AssignedUserOrders.username(ascending=ascending)
        elif order.field == AssignedUserOrderField.EMAIL:
            return AssignedUserOrders.email(ascending=ascending)
        elif order.field == AssignedUserOrderField.GRANTED_AT:
            return AssignedUserOrders.granted_at(ascending=ascending)
        else:
            raise ValueError(f"Unknown order field: {order.field}")

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)
