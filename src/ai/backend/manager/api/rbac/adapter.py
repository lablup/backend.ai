"""
Adapters to convert RBAC DTOs to repository Querier objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.dto.manager.rbac import (
    AssignedUserDTO,
    AssignedUserFilter,
    AssignedUserOrder,
    AssignedUserOrderField,
    OrderDirection,
    RoleDTO,
    RoleFilter,
    RoleOrder,
    RoleOrderField,
    SearchRolesRequest,
    SearchUsersAssignedToRoleRequest,
    UpdateRoleRequest,
)
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.data.permission.role import (
    AssignedUserData,
    RoleData,
    RoleDetailData,
    RoleUpdateInput,
)
from ai.backend.manager.repositories.base import (
    OffsetPagination,
    Querier,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.permission_controller.options import (
    AssignedUserConditions,
    AssignedUserOrders,
    RoleConditions,
    RoleOrders,
)
from ai.backend.manager.types import OptionalState, TriState

__all__ = (
    "RoleAdapter",
    "AssignedUserAdapter",
)


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

    def build_modifier(self, role_id: UUID, request: UpdateRoleRequest) -> RoleUpdateInput:
        """Convert update request to modifier."""

        if request.name is not None:
            name = OptionalState.update(request.name)
        else:
            name = OptionalState.nop()
        if request.source is not None:
            source = OptionalState.update(request.source)
        else:
            source = OptionalState.nop()
        if request.status is not None:
            status = OptionalState.update(request.status)
        else:
            status = OptionalState.nop()
        if request.description is not SENTINEL:
            description = TriState[str].from_graphql(request.description)
        else:
            description = TriState[str].nop()

        modifier = RoleUpdateInput(
            id=role_id,
            name=name,
            source=source,
            status=status,
            description=description,
        )
        return modifier

    def build_querier(self, request: SearchRolesRequest) -> Querier:
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

        return Querier(conditions=conditions, orders=orders, pagination=pagination)

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
            raise ValueError(f"Unknown order field: {order.field}")

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)


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

    def build_querier(self, request: SearchUsersAssignedToRoleRequest) -> Querier:
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

        return Querier(conditions=conditions, orders=orders, pagination=pagination)

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
