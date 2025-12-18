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
    SearchUsersAssignedToRolePathParam,
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
            granted_by=data.granted_by,
            granted_at=data.granted_at,
        )

    def build_querier(
        self,
        param: SearchUsersAssignedToRolePathParam,
        request: SearchUsersAssignedToRoleRequest,
    ) -> BatchQuerier:
        """
        Build a Querier for assigned users from search request.

        Args:
            param: Path parameter containing role_id
            request: Search request containing filter, order, and pagination

        Returns:
            Querier object with converted conditions, orders, and pagination
        """
        conditions = [self._get_base_filter(param)]
        if request.filter is not None:
            conditions.extend(self._convert_filter(request.filter))
        orders: list[QueryOrder] = []
        if request.order is not None:
            for order in request.order:
                orders.append(self._convert_order(order))
        pagination = self._build_pagination(request.limit, request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _get_base_filter(self, param: SearchUsersAssignedToRolePathParam) -> QueryCondition:
        return AssignedUserConditions.by_role_id(param.role_id)

    def _convert_filter(self, filter: AssignedUserFilter) -> list[QueryCondition]:
        """Convert assigned user filter to list of query conditions."""
        # Always add role_id as first condition
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

        # Granted by filter
        if filter.granted_by is not None:
            condition = AssignedUserConditions.by_granted_by_equals(filter.granted_by)
            conditions.append(condition)

        return conditions

    def _convert_order(self, order: AssignedUserOrder) -> QueryOrder:
        """Convert assigned user order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        match order.field:
            case AssignedUserOrderField.USERNAME:
                return AssignedUserOrders.username(ascending=ascending)
            case AssignedUserOrderField.EMAIL:
                return AssignedUserOrders.email(ascending=ascending)
            case AssignedUserOrderField.GRANTED_AT:
                return AssignedUserOrders.granted_at(ascending=ascending)

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)
