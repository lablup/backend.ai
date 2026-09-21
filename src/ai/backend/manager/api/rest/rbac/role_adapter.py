"""
Adapters to convert RBAC DTOs to repository Querier objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.dto.manager.rbac import (
    OrderDirection,
    RoleDTO,
    RoleFilter,
    RoleOrder,
    RoleOrderField,
    SearchRolesRequest,
    UpdateRoleRequest,
)
from ai.backend.manager.data.permission.role import RoleData, RoleDetailData
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.rbac_models.role.searchable_fields import (
    RoleSearchableFields,
)
from ai.backend.manager.models.rbac_models.role.updaters import RoleUpdater
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.filter_adapter import BaseFilterAdapter
from ai.backend.manager.types import OptionalState, TriState

__all__ = ("RoleAdapter",)


class RoleAdapter(BaseFilterAdapter):
    """Adapter for converting role requests to repository queries."""

    def convert_to_dto(self, data: RoleData | RoleDetailData) -> RoleDTO:
        """Convert RoleData to DTO."""
        return RoleDTO(
            id=data.id,
            name=data.name,
            scope_type=data.scope_type,
            scope_id=data.scope_id,
            source=data.source,
            status=data.status,
            created_at=data.created_at,
            updated_at=data.updated_at,
            deleted_at=data.deleted_at,
            description=data.description,
        )

    def build_updater(self, request: UpdateRoleRequest, role_id: UUID) -> RoleUpdater:
        """Convert update request to updater."""
        return RoleUpdater(
            role_id=RoleID(role_id),
            name=OptionalState.from_unset(request.name),
            description=TriState.from_unset(request.description),
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
        orders: list[QueryOrder] = []
        if request.order is not None:
            for order in request.order:
                orders.append(self._convert_order(order))
        pagination = self._build_pagination(request.limit, request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: RoleFilter) -> list[QueryCondition]:
        """Convert role filter to list of query conditions."""
        fields = RoleSearchableFields.own
        conditions = [*self.apply_string_filter(filter.name, fields.name.filter)]
        if filter.sources:
            conditions.append(fields.source.filter.in_(filter.sources))
        if filter.statuses:
            conditions.append(fields.status.filter.in_(filter.statuses))
        return conditions

    def _convert_order(self, order: RoleOrder) -> QueryOrder:
        """Convert role order specification to query order."""
        fields = RoleSearchableFields.own
        ascending = order.direction == OrderDirection.ASC

        if order.field == RoleOrderField.NAME:
            return fields.name.order.apply(ascending)
        if order.field == RoleOrderField.CREATED_AT:
            return fields.created_at.order.apply(ascending)
        if order.field == RoleOrderField.UPDATED_AT:
            return fields.updated_at.order.apply(ascending)
        raise ValueError(f"Unknown order field: {order.field}")

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)
