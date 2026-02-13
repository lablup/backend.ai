"""
Adapters to convert compute session DTOs to repository BatchQuerier objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any
from uuid import UUID

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
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.data.session.types import SessionData, SessionStatus
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    NoPagination,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.scheduler.options import (
    KernelConditions,
    SessionConditions,
    SessionOrders,
)

__all__ = ("ComputeSessionsAdapter",)


class ComputeSessionsAdapter(BaseFilterAdapter):
    """Adapter for converting compute session requests to repository queries."""

    def build_session_querier(self, request: SearchComputeSessionsRequest) -> BatchQuerier:
        """Build a BatchQuerier for compute sessions from search request."""
        conditions = self._convert_session_filter(request.filter) if request.filter else []
        orders = [self._convert_session_order(o) for o in request.order] if request.order else []
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def build_kernel_querier_for_sessions(self, session_ids: list[SessionId]) -> BatchQuerier:
        """Build a BatchQuerier for kernels belonging to the given sessions."""
        conditions: list[QueryCondition] = [KernelConditions.by_session_ids(session_ids)]
        return BatchQuerier(conditions=conditions, orders=[], pagination=NoPagination())

    def group_kernels_by_session(self, kernels: list[KernelInfo]) -> dict[UUID, list[KernelInfo]]:
        """Group kernel info list by session ID."""
        grouped: dict[UUID, list[KernelInfo]] = defaultdict(list)
        for kernel in kernels:
            session_id = UUID(kernel.session.session_id)
            grouped[session_id].append(kernel)
        return grouped

    def convert_session_to_dto(
        self, session: SessionData, kernels: list[KernelInfo] | None = None
    ) -> ComputeSessionDTO:
        """Convert SessionData + kernels to ComputeSessionDTO."""
        containers = [self._convert_kernel_to_container(k) for k in kernels] if kernels else []

        resource_slots: dict[str, Any] | None = None
        if session.requested_slots is not None:
            resource_slots = dict(session.requested_slots)

        occupied_slots: dict[str, Any] | None = None
        if session.occupying_slots is not None:
            occupied_slots = dict(session.occupying_slots)

        return ComputeSessionDTO(
            id=session.id,
            name=session.name,
            type=session.session_type.value,
            status=session.status.value,
            image=session.images,
            scaling_group=session.scaling_group_name,
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
        conditions: list[QueryCondition] = []

        if filter.status is not None and len(filter.status) > 0:
            statuses = [SessionStatus(s) for s in filter.status]
            conditions.append(SessionConditions.by_statuses(statuses))

        if filter.scaling_group_name is not None:
            condition = self.convert_string_filter(
                filter.scaling_group_name,
                contains_factory=SessionConditions.by_scaling_group_contains,
                equals_factory=SessionConditions.by_scaling_group_equals,
                starts_with_factory=SessionConditions.by_scaling_group_starts_with,
                ends_with_factory=SessionConditions.by_scaling_group_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        return conditions

    def _convert_session_order(self, order: ComputeSessionOrder) -> QueryOrder:
        """Convert session order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        match order.field:
            case ComputeSessionOrderField.CREATED_AT:
                return SessionOrders.created_at(ascending=ascending)
            case ComputeSessionOrderField.ID:
                return SessionOrders.id(ascending=ascending)

        raise ValueError(f"Unknown order field: {order.field}")
