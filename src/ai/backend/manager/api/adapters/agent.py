"""Agent adapter bridging DTOs and Processors."""

from __future__ import annotations

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.agent.request import (
    AdminSearchAgentsInput,
    AgentFilter,
    AgentOrder,
)
from ai.backend.common.dto.manager.v2.agent.response import (
    AdminSearchAgentsPayload,
    AgentNetworkInfo,
    AgentNode,
    AgentResourceInfo,
    AgentStatusInfo,
    AgentSystemInfo,
)
from ai.backend.common.dto.manager.v2.agent.types import AgentStatusFilter
from ai.backend.manager.data.agent.types import AgentDetailData, AgentStatus
from ai.backend.manager.models.agent.conditions import AgentConditions
from ai.backend.manager.models.agent.orders import (
    DEFAULT_FORWARD_ORDER,
    TIEBREAKER_ORDER,
    resolve_order,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.services.agent.actions.search_agents import SearchAgentsAction

from .base import BaseAdapter

DEFAULT_PAGINATION_LIMIT = 10


class AgentAdapter(BaseAdapter):
    """Adapter for agent domain operations."""

    async def admin_search(
        self,
        input: AdminSearchAgentsInput,
    ) -> AdminSearchAgentsPayload:
        """Search agents (admin, no scope) with filters, orders, and pagination.

        Args:
            input: Pydantic DTO with filter, order, and pagination parameters.

        Returns:
            Pydantic payload with items and pagination info.
        """
        querier = self.build_querier(input)

        action_result = await self._processors.agent.search_agents.wait_for_complete(
            SearchAgentsAction(querier=querier)
        )

        return AdminSearchAgentsPayload(
            items=[self._data_to_dto(item) for item in action_result.agents],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def build_querier(self, input: AdminSearchAgentsInput) -> BatchQuerier:
        """Build a BatchQuerier from the search input DTO."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else [DEFAULT_FORWARD_ORDER]
        orders.append(TIEBREAKER_ORDER)
        pagination = self._build_pagination(input)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_filter(self, filter: AgentFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.status is not None:
            conditions.extend(self._convert_status_filter(filter.status))
        if filter.resource_group is not None:
            condition = self._convert_resource_group_filter(filter.resource_group)
            if condition is not None:
                conditions.append(condition)
        return conditions

    def _convert_resource_group_filter(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=AgentConditions.by_scaling_group_contains,
            equals_factory=AgentConditions.by_scaling_group_equals,
            starts_with_factory=AgentConditions.by_scaling_group_starts_with,
            ends_with_factory=AgentConditions.by_scaling_group_ends_with,
        )

    @staticmethod
    def _convert_status_filter(sf: AgentStatusFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if sf.equals is not None:
            conditions.append(AgentConditions.by_status_equals(AgentStatus(sf.equals.value)))
        if sf.in_ is not None:
            conditions.append(
                AgentConditions.by_status_contains([AgentStatus(s.value) for s in sf.in_])
            )
        if sf.not_equals is not None:
            conditions.append(
                AgentConditions.by_status_not_equals(AgentStatus(sf.not_equals.value))
            )
        if sf.not_in is not None:
            conditions.append(
                AgentConditions.by_status_not_in([AgentStatus(s.value) for s in sf.not_in])
            )
        return conditions

    @staticmethod
    def _convert_orders(order: list[AgentOrder]) -> list[QueryOrder]:
        return [resolve_order(o.field, o.direction) for o in order]

    @staticmethod
    def _build_pagination(input: AdminSearchAgentsInput) -> OffsetPagination:
        return OffsetPagination(
            limit=input.limit if input.limit is not None else DEFAULT_PAGINATION_LIMIT,
            offset=input.offset if input.offset is not None else 0,
        )

    @staticmethod
    def _data_to_dto(detail: AgentDetailData) -> AgentNode:
        """Convert data layer type to Pydantic DTO."""
        data = detail.agent
        return AgentNode(
            id=str(data.id),
            resource_info=AgentResourceInfo(
                capacity=dict(data.available_slots.to_json()),
                used=dict(data.actual_occupied_slots.to_json()),
                free=dict((data.available_slots - data.actual_occupied_slots).to_json()),
            ),
            status_info=AgentStatusInfo(
                status=data.status.name,
                status_changed=data.status_changed,
                first_contact=data.first_contact,
                lost_at=data.lost_at,
                schedulable=data.schedulable,
            ),
            system_info=AgentSystemInfo(
                architecture=data.architecture,
                version=data.version,
                compute_plugins=dict(data.compute_plugins) if data.compute_plugins else None,
            ),
            network_info=AgentNetworkInfo(
                region=data.region,
                addr=data.addr,
            ),
        )
