"""
Adapter to convert Agent DTOs to repository Querier objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.agent import (
    AgentDTO,
    AgentFilter,
    AgentOrder,
    AgentOrderField,
    OrderDirection,
    SearchAgentsRequest,
)
from ai.backend.manager.api.adapter import BaseFilterAdapter
from ai.backend.manager.data.agent.types import AgentDetailData, AgentStatus
from ai.backend.manager.repositories.agent.query import QueryConditions, QueryOrders
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)

__all__ = ("AgentAdapter",)


class AgentAdapter(BaseFilterAdapter):
    """Adapter for converting agent requests to repository queries."""

    def convert_to_dto(self, data: AgentDetailData) -> AgentDTO:
        """Convert AgentDetailData to DTO."""
        agent = data.agent
        return AgentDTO(
            id=str(agent.id),
            status=agent.status.name,
            region=agent.region,
            resource_group=agent.scaling_group,
            schedulable=agent.schedulable,
            available_slots=dict(agent.available_slots.to_json()),
            occupied_slots=dict(agent.cached_occupied_slots.to_json()),
            addr=agent.addr,
            architecture=agent.architecture,
            version=agent.version,
        )

    def build_querier(self, request: SearchAgentsRequest) -> BatchQuerier:
        """
        Build a BatchQuerier for agents from search request.

        Args:
            request: Search request containing filter, order, and pagination

        Returns:
            BatchQuerier object with converted conditions, orders, and pagination
        """
        conditions = self._convert_filter(request.filter) if request.filter else []
        orders: list[QueryOrder] = []
        if request.order is not None:
            for order in request.order:
                orders.append(self._convert_order(order))
        pagination = self._build_pagination(request.limit, request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: AgentFilter) -> list[QueryCondition]:
        """Convert agent filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        if filter.status is not None:
            if filter.status.equals is not None:
                conditions.append(
                    QueryConditions.by_status_equals(AgentStatus[filter.status.equals.value])
                )
            if filter.status.in_ is not None and len(filter.status.in_) > 0:
                agent_statuses = [AgentStatus[s.value] for s in filter.status.in_]
                conditions.append(QueryConditions.by_statuses(agent_statuses))
            if filter.status.not_equals is not None:
                conditions.append(
                    QueryConditions.by_status_not_equals(
                        AgentStatus[filter.status.not_equals.value]
                    )
                )
            if filter.status.not_in is not None and len(filter.status.not_in) > 0:
                agent_statuses = [AgentStatus[s.value] for s in filter.status.not_in]
                conditions.append(QueryConditions.by_status_not_in(agent_statuses))

        if filter.resource_group is not None:
            condition = self.convert_string_filter(
                filter.resource_group,
                contains_factory=QueryConditions.by_resource_group_contains,
                equals_factory=QueryConditions.by_resource_group_equals,
                starts_with_factory=QueryConditions.by_resource_group_starts_with,
                ends_with_factory=QueryConditions.by_resource_group_ends_with,
            )
            if condition is not None:
                conditions.append(condition)

        return conditions

    def _convert_order(self, order: AgentOrder) -> QueryOrder:
        """Convert agent order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        if order.field == AgentOrderField.ID:
            return QueryOrders.id(ascending=ascending)
        if order.field == AgentOrderField.STATUS:
            return QueryOrders.status(ascending=ascending)
        if order.field == AgentOrderField.RESOURCE_GROUP:
            return QueryOrders.resource_group(ascending=ascending)
        raise ValueError(f"Unknown order field: {order.field}")

    def _build_pagination(self, limit: int, offset: int) -> OffsetPagination:
        """Build pagination from limit and offset."""
        return OffsetPagination(limit=limit, offset=offset)
