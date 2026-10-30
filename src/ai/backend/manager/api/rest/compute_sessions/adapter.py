"""
Adapters to convert compute session DTOs to session and kernel searchers.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, assert_never
from uuid import UUID

from ai.backend.common.data.filter_specs import UUIDInMatchSpec
from ai.backend.common.dto.manager.compute_session import (
    ComputeSessionDTO,
    ComputeSessionFilter,
    ComputeSessionOrder,
    ComputeSessionOrderField,
    ContainerDTO,
    OrderDirection,
    SearchComputeSessionsRequest,
)
from ai.backend.common.types import SessionId
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.data.resource_slot.types import ResourceAllocationAggregate
from ai.backend.manager.data.session.types import SessionData, SessionStatus
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.kernel.searchable_fields import KernelSearchableFields
from ai.backend.manager.models.kernel.searchers import KernelSearcher
from ai.backend.manager.models.session.searchable_fields import SessionSearchableFields
from ai.backend.manager.models.session.searchers import SessionSearcher
from ai.backend.manager.models.specs.pagination import NoPagination, OffsetPagination
from ai.backend.manager.repositories.base.filter_adapter import BaseFilterAdapter


class ComputeSessionsAdapter(BaseFilterAdapter):
    """Adapter for converting compute session requests to repository queries."""

    def build_session_searcher(self, request: SearchComputeSessionsRequest) -> SessionSearcher:
        """Build a SessionSearcher for compute sessions from search request."""
        conditions = self._convert_session_filter(request.filter) if request.filter else []
        orders = [self._convert_session_order(o) for o in request.order] if request.order else []
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)

        return SessionSearcher(conditions=conditions, orders=orders, pagination=pagination)

    def build_kernel_searcher_for_sessions(self, session_ids: list[SessionId]) -> KernelSearcher:
        """Build a KernelSearcher for kernels belonging to the given sessions."""
        conditions: list[QueryCondition] = [
            KernelSearchableFields.own.session_id.filter.in_(
                UUIDInMatchSpec(values=session_ids, negated=False)
            )
        ]
        return KernelSearcher(conditions=conditions, orders=[], pagination=NoPagination())

    def group_kernels_by_session(self, kernels: list[KernelInfo]) -> dict[UUID, list[KernelInfo]]:
        """Group kernel info list by session ID."""
        grouped: dict[UUID, list[KernelInfo]] = defaultdict(list)
        for kernel in kernels:
            session_id = UUID(kernel.session.session_id)
            grouped[session_id].append(kernel)
        return grouped

    def convert_session_to_dto(
        self,
        session: SessionData,
        allocation: ResourceAllocationAggregate | None,
        kernels: list[KernelInfo] | None = None,
    ) -> ComputeSessionDTO:
        """Convert SessionData + kernels to ComputeSessionDTO."""
        containers = [self._convert_kernel_to_container(k) for k in kernels] if kernels else []

        resource_slots: dict[str, Any] | None = (
            dict(allocation.requested) if allocation is not None else None
        )
        occupied_slots: dict[str, Any] | None = (
            dict(allocation.used) if allocation is not None else None
        )

        return ComputeSessionDTO(
            id=session.id,
            name=session.name,
            type=session.session_type.value,
            status=session.status.value,
            image=session.images,
            scaling_group=session.resource_group_name,
            resource_slots=resource_slots,
            occupied_slots=occupied_slots,
            created_at=session.created_at,
            terminated_at=session.terminated_at,
            starts_at=session.starts_at,
            containers=containers,
        )

    def _convert_kernel_to_container(self, kernel: KernelInfo) -> ContainerDTO:
        """Convert KernelInfo to ContainerDTO."""
        resource_usage: dict[str, Any] | None = None
        if kernel.metrics.last_stat is not None:
            resource_usage = kernel.metrics.last_stat

        return ContainerDTO(
            id=kernel.id,
            agent_id=kernel.resource.agent,
            status=kernel.lifecycle.status.value,
            resource_usage=resource_usage,
        )

    def _convert_session_filter(self, filter: ComputeSessionFilter) -> list[QueryCondition]:
        """Convert session filter to list of query conditions."""
        fields = SessionSearchableFields.own
        conditions: list[QueryCondition] = []
        if filter.status:
            conditions.append(fields.status.filter.in_([SessionStatus(s) for s in filter.status]))
        conditions.extend(self.apply_string_filter(filter.name, fields.name.filter))
        conditions.extend(self.apply_string_filter(filter.access_key, fields.access_key.filter))
        conditions.extend(self.apply_string_filter(filter.domain_name, fields.domain_name.filter))
        conditions.extend(
            self.apply_string_filter(filter.scaling_group_name, fields.resource_group_name.filter)
        )
        return conditions

    def _convert_session_order(self, order: ComputeSessionOrder) -> QueryOrder:
        """Convert session order specification to query order."""
        fields = SessionSearchableFields.own
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case ComputeSessionOrderField.CREATED_AT:
                return fields.created_at.order.apply(ascending)
            case ComputeSessionOrderField.ID:
                return fields.id.order.apply(ascending)
            case _:
                assert_never(order.field)
