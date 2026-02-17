"""
Adapters to convert domain DTOs to repository BatchQuerier objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.domain import (
    DomainDTO,
    DomainFilter,
    DomainOrder,
    DomainOrderField,
    OrderDirection,
    SearchDomainsRequest,
    UpdateDomainRequest,
)
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.domain.options import (
    DomainConditions,
    DomainOrders,
)
from ai.backend.manager.repositories.domain.updaters import DomainUpdaterSpec
from ai.backend.manager.types import OptionalState, TriState

__all__ = ("DomainAdapter",)


class DomainAdapter(BaseFilterAdapter):
    """Adapter for converting domain requests to repository queries."""

    def convert_to_dto(self, data: DomainData) -> DomainDTO:
        """Convert DomainData to DTO."""
        return DomainDTO(
            name=data.name,
            description=data.description,
            is_active=data.is_active,
            created_at=data.created_at,
            modified_at=data.modified_at,
            total_resource_slots=dict(data.total_resource_slots),
            allowed_vfolder_hosts=dict(data.allowed_vfolder_hosts),
            allowed_docker_registries=data.allowed_docker_registries,
            integration_id=data.integration_id,
        )

    def build_updater(self, request: UpdateDomainRequest, domain_name: str) -> Updater[DomainRow]:
        """Convert update request to updater."""
        name = OptionalState[str].nop()
        description = TriState[str].nop()
        is_active = OptionalState[bool].nop()
        total_resource_slots: TriState[ResourceSlot] = TriState.nop()
        allowed_vfolder_hosts: OptionalState[dict[str, list[str]]] = OptionalState.nop()
        allowed_docker_registries: OptionalState[list[str]] = OptionalState.nop()
        integration_id = TriState[str].nop()

        if request.name is not None:
            name = OptionalState.update(request.name)
        if request.description is not None:
            description = TriState.update(request.description)
        if request.is_active is not None:
            is_active = OptionalState.update(request.is_active)
        if request.total_resource_slots is not None:
            total_resource_slots = TriState.update(ResourceSlot(request.total_resource_slots))
        if request.allowed_vfolder_hosts is not None:
            allowed_vfolder_hosts = OptionalState.update(request.allowed_vfolder_hosts)
        if request.allowed_docker_registries is not None:
            allowed_docker_registries = OptionalState.update(request.allowed_docker_registries)
        if request.integration_id is not None:
            integration_id = TriState.update(request.integration_id)

        updater_spec = DomainUpdaterSpec(
            name=name,
            description=description,
            is_active=is_active,
            total_resource_slots=total_resource_slots,
            allowed_vfolder_hosts=allowed_vfolder_hosts,
            allowed_docker_registries=allowed_docker_registries,
            integration_id=integration_id,
        )
        return Updater(spec=updater_spec, pk_value=domain_name)

    def build_querier(self, request: SearchDomainsRequest) -> BatchQuerier:
        """Build a BatchQuerier for domains from search request."""
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders = [self._convert_order(o) for o in request.order] if request.order else []
        pagination = self._build_pagination(request.limit, request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: DomainFilter) -> list[QueryCondition]:
        """Convert domain filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        if filter.name is not None:
            condition = self.convert_string_filter(
                filter.name,
                contains_factory=DomainConditions.by_name_contains,
                equals_factory=DomainConditions.by_name_equals,
                starts_with_factory=DomainConditions.by_name_starts_with,
                ends_with_factory=DomainConditions.by_name_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        if filter.is_active is not None:
            conditions.append(DomainConditions.by_is_active(filter.is_active))

        return conditions

    def _convert_order(self, order: DomainOrder) -> QueryOrder:
        """Convert domain order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        if order.field == DomainOrderField.NAME:
            return DomainOrders.name(ascending=ascending)
        if order.field == DomainOrderField.CREATED_AT:
            return DomainOrders.created_at(ascending=ascending)
        if order.field == DomainOrderField.MODIFIED_AT:
            return DomainOrders.modified_at(ascending=ascending)
        raise ValueError(f"Unknown order field: {order.field}")

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)
