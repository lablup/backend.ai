"""
Adapter to convert assigned user DTOs to repository Querier objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec
from ai.backend.common.dto.manager.rbac import (
    AssignedUserDTO,
    AssignedUserFilter,
    AssignedUserOrder,
    AssignedUserOrderField,
    OrderDirection,
    SearchUsersAssignedToRolePathParam,
    SearchUsersAssignedToRoleRequest,
)
from ai.backend.manager.data.permission.role import AssignedUserData
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.rbac_models.user_role.searchable_fields import (
    RoleAssignmentSearchableFields,
)
from ai.backend.manager.models.rbac_models.user_role.searchers import RoleAssignmentSearcher
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.user.searchable_fields import UserSearchableFields
from ai.backend.manager.repositories.base.filter_adapter import BaseFilterAdapter

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

    def build_searcher(
        self,
        param: SearchUsersAssignedToRolePathParam,
        request: SearchUsersAssignedToRoleRequest,
    ) -> RoleAssignmentSearcher:
        """Build a searcher for the users assigned to the role in the path."""
        conditions = [self._get_base_filter(param)]
        if request.filter is not None:
            conditions.extend(self._convert_filter(request.filter))
        orders: list[QueryOrder] = []
        if request.order is not None:
            for order in request.order:
                orders.append(self._convert_order(order))
        pagination = self._build_pagination(request.limit, request.offset)

        return RoleAssignmentSearcher(conditions=conditions, orders=orders, pagination=pagination)

    def _get_base_filter(self, param: SearchUsersAssignedToRolePathParam) -> QueryCondition:
        return RoleAssignmentSearchableFields.own.role_id.filter.equals(
            UUIDEqualMatchSpec(value=param.role_id, negated=False)
        )

    def _convert_filter(self, filter: AssignedUserFilter) -> list[QueryCondition]:
        """The searcher joins the assignment row to its user, so the user's columns
        carry plain conditions rather than a subquery."""
        user_fields = UserSearchableFields.own
        conditions = [
            *self.apply_string_filter(filter.username, user_fields.username.filter),
            *self.apply_string_filter(filter.email, user_fields.email.filter),
        ]
        if filter.granted_by is not None:
            conditions.append(
                RoleAssignmentSearchableFields.own.granted_by.filter.equals(
                    UUIDEqualMatchSpec(value=filter.granted_by, negated=False)
                )
            )
        return conditions

    def _convert_order(self, order: AssignedUserOrder) -> QueryOrder:
        """Convert assigned user order specification to query order."""
        user_fields = UserSearchableFields.own
        ascending = order.direction == OrderDirection.ASC

        match order.field:
            case AssignedUserOrderField.USERNAME:
                return user_fields.username.order.apply(ascending)
            case AssignedUserOrderField.EMAIL:
                return user_fields.email.order.apply(ascending)
            case AssignedUserOrderField.GRANTED_AT:
                return RoleAssignmentSearchableFields.own.granted_at.order.apply(ascending)

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)
