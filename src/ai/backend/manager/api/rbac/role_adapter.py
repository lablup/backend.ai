"""
Adapters to convert RBAC DTOs to repository Querier objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.api_handlers import SENTINEL
from ai.backend.common.dto.manager.rbac import (
    OrderDirection,
    RoleDTO,
    RoleFilter,
    RoleOrder,
    RoleOrderField,
    RoleSource,
    RoleStatus,
    SearchRolesRequest,
    UpdateRoleRequest,
)
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.data.permission.role import RoleData, RoleDetailData
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    Purger,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.permission_controller.options import (
    RoleConditions,
    RoleOrders,
)
from ai.backend.manager.repositories.permission_controller.updaters import RoleUpdaterSpec
from ai.backend.manager.types import OptionalState, TriState

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

    def build_deleter(self, role_id: UUID) -> Updater[RoleRow]:
        """Build a deleter updater for the given role ID."""
        spec = RoleUpdaterSpec(
            status=OptionalState.update(RoleStatus.DELETED),
        )
        return Updater(spec=spec, pk_value=role_id)

    def build_purger(self, role_id: UUID) -> Purger[RoleRow]:
        """Build a purger for the given role ID."""
        return Purger(
            row_class=RoleRow,
            pk_value=role_id,
        )

    def build_updater(self, request: UpdateRoleRequest, role_id: UUID) -> Updater[RoleRow]:
        """Convert update request to updater."""
        name = OptionalState[str].nop()
        source = OptionalState[RoleSource].nop()
        status = OptionalState[RoleStatus].nop()
        description = TriState[str].nop()

        if request.name is not None:
            name = OptionalState.update(request.name)
        if request.source is not None:
            source = OptionalState.update(request.source)
        if request.status is not None:
            status = OptionalState.update(request.status)
        if request.description is not SENTINEL:
            if request.description is None:
                description = TriState.nullify()
            else:
                description = TriState.update(request.description)

        spec = RoleUpdaterSpec(
            name=name,
            source=source,
            status=status,
            description=description,
        )
        return Updater(spec=spec, pk_value=role_id)

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
