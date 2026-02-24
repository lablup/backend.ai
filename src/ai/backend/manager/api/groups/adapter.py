"""
Adapters to convert group DTOs to repository query objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.deployment.types import OrderDirection
from ai.backend.common.dto.manager.group import (
    GroupDTO,
    GroupFilter,
    GroupOrder,
    GroupOrderField,
    SearchGroupsRequest,
    UpdateGroupRequest,
)
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.group.options import (
    GroupConditions,
    GroupOrders,
)
from ai.backend.manager.repositories.group.updaters import GroupUpdaterSpec
from ai.backend.manager.types import OptionalState, TriState

__all__ = ("GroupAdapter",)


class GroupAdapter(BaseFilterAdapter):
    """Adapter for converting group requests to repository queries."""

    def convert_to_dto(self, data: GroupData) -> GroupDTO:
        """Convert GroupData to DTO."""
        return GroupDTO(
            id=data.id,
            name=data.name,
            description=data.description,
            is_active=data.is_active if data.is_active is not None else True,
            created_at=data.created_at,
            modified_at=data.modified_at,
            domain_name=data.domain_name,
            integration_id=data.integration_id,
            total_resource_slots=dict(data.total_resource_slots),
            allowed_vfolder_hosts=dict(data.allowed_vfolder_hosts),
            resource_policy=data.resource_policy,
            container_registry=data.container_registry,
        )

    def build_updater(self, request: UpdateGroupRequest, group_id: UUID) -> Updater[GroupRow]:
        """Convert update request to updater."""
        name = OptionalState[str].nop()
        description = TriState[str].nop()
        is_active = OptionalState[bool].nop()
        total_resource_slots = OptionalState.nop()
        allowed_vfolder_hosts = OptionalState.nop()
        integration_id = OptionalState[str].nop()
        resource_policy = OptionalState[str].nop()

        if request.name is not None:
            name = OptionalState.update(request.name)
        if request.description is not None:
            description = TriState.update(request.description)
        if request.is_active is not None:
            is_active = OptionalState.update(request.is_active)
        if request.total_resource_slots is not None:
            total_resource_slots = OptionalState.update(request.total_resource_slots)
        if request.allowed_vfolder_hosts is not None:
            allowed_vfolder_hosts = OptionalState.update(request.allowed_vfolder_hosts)
        if request.integration_id is not None:
            integration_id = OptionalState.update(request.integration_id)
        if request.resource_policy is not None:
            resource_policy = OptionalState.update(request.resource_policy)

        updater_spec = GroupUpdaterSpec(
            name=name,
            description=description,
            is_active=is_active,
            total_resource_slots=total_resource_slots,
            allowed_vfolder_hosts=allowed_vfolder_hosts,
            integration_id=integration_id,
            resource_policy=resource_policy,
        )
        return Updater(spec=updater_spec, pk_value=group_id)

    def build_querier(self, request: SearchGroupsRequest) -> BatchQuerier:
        """Build a BatchQuerier for groups from search request."""
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders = [self._convert_order(o) for o in request.order] if request.order else []
        pagination = self._build_pagination(request.limit, request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: GroupFilter) -> list[QueryCondition]:
        """Convert group filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=GroupConditions.by_name_contains,
                equals_factory=GroupConditions.by_name_equals,
                starts_with_factory=GroupConditions.by_name_starts_with,
                ends_with_factory=GroupConditions.by_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.domain_name is not None:
            condition = self.convert_string_filter(
                filter.domain_name,
                contains_factory=GroupConditions.by_domain_name_contains,
                equals_factory=GroupConditions.by_domain_name_equals,
                starts_with_factory=GroupConditions.by_domain_name_starts_with,
                ends_with_factory=GroupConditions.by_domain_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.is_active is not None:
            conditions.append(GroupConditions.by_is_active(filter.is_active))

        return conditions

    def _convert_order(self, order: GroupOrder) -> QueryOrder:
        """Convert group order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        if order.field == GroupOrderField.NAME:
            return GroupOrders.name(ascending=ascending)
        if order.field == GroupOrderField.CREATED_AT:
            return GroupOrders.created_at(ascending=ascending)
        if order.field == GroupOrderField.MODIFIED_AT:
            return GroupOrders.modified_at(ascending=ascending)
        raise ValueError(f"Unknown order field: {order.field}")

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)
