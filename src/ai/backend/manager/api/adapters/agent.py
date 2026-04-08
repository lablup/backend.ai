"""Agent adapter bridging DTOs and Processors."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

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
    ComputePluginEntryDTO,
    ComputePluginsGQLDTO,
)
from ai.backend.common.dto.manager.v2.agent.types import AgentStatusFilter
from ai.backend.common.resource.types import TotalResourceData
from ai.backend.common.types import AgentId
from ai.backend.manager.data.agent.types import AgentDetailData, AgentStatus
from ai.backend.manager.models.agent.conditions import AgentConditions
from ai.backend.manager.models.agent.orders import (
    DEFAULT_BACKWARD_ORDER,
    DEFAULT_FORWARD_ORDER,
    TIEBREAKER_ORDER,
    resolve_order,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    NoPagination,
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.services.agent.actions.get_total_resources import (
    GetTotalResourcesAction,
    GetTotalResourcesActionResult,
)
from ai.backend.manager.services.agent.actions.load_container_counts import (
    LoadContainerCountsAction,
)
from ai.backend.manager.services.agent.actions.search_agents import SearchAgentsAction

from .base import BaseAdapter
from .pagination import PaginationSpec

_AGENT_PAGINATION_SPEC = PaginationSpec(
    forward_order=DEFAULT_FORWARD_ORDER,
    backward_order=DEFAULT_BACKWARD_ORDER,
    forward_condition_factory=AgentConditions.by_cursor_forward,
    backward_condition_factory=AgentConditions.by_cursor_backward,
    tiebreaker_order=TIEBREAKER_ORDER,
)


class AgentAdapter(BaseAdapter):
    """Adapter for agent domain operations."""

    # ------------------------------------------------------------------ batch load (DataLoader)

    async def batch_load_by_ids(self, agent_ids: Sequence[AgentId]) -> list[AgentNode | None]:
        """Batch load agents by ID for DataLoader use.

        Returns AgentNode DTOs in the same order as the input agent_ids list.
        """
        if not agent_ids:
            return []
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[AgentConditions.by_ids(agent_ids)],
        )
        action_result = await self._processors.agent.search_agents.wait_for_complete(
            SearchAgentsAction(querier=querier)
        )
        agent_map = {detail.agent.id: self._data_to_dto(detail) for detail in action_result.agents}
        return [agent_map.get(agent_id) for agent_id in agent_ids]

    async def batch_load_container_counts(self, agent_ids: Sequence[AgentId]) -> list[int]:
        """Batch load container counts for agents by ID for DataLoader use.

        Returns container counts in the same order as the input agent_ids list.
        Returns 0 for agents not found.
        """
        if not agent_ids:
            return []
        action_result = await self._processors.agent.load_container_counts.wait_for_complete(
            LoadContainerCountsAction(agent_ids=agent_ids)
        )
        return list(action_result.container_counts)

    # ------------------------------------------------------------------ search

    async def admin_search(
        self,
        input: AdminSearchAgentsInput,
    ) -> AdminSearchAgentsPayload:
        """Search agents (admin, no scope) with filters, orders, and pagination."""
        conditions = self._convert_filter(input.filter) if input.filter else []
        orders = self._convert_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_AGENT_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._processors.agent.search_agents.wait_for_complete(
            SearchAgentsAction(querier=querier)
        )
        return AdminSearchAgentsPayload(
            items=[self._data_to_dto(item) for item in action_result.agents],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    def _convert_filter(self, f: AgentFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if f.id is not None:
            condition = self._convert_id_filter(f.id)
            if condition is not None:
                conditions.append(condition)
        if f.status is not None:
            conditions.extend(self._convert_status_filter(f.status))
        if f.schedulable is not None:
            conditions.append(AgentConditions.by_schedulable(f.schedulable))
        if f.scaling_group is not None:
            condition = self._convert_scaling_group_filter(f.scaling_group)
            if condition is not None:
                conditions.append(condition)
        if f.AND:
            for sub_filter in f.AND:
                conditions.extend(self._convert_filter(sub_filter))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in f.OR:
                or_conditions.extend(self._convert_filter(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in f.NOT:
                not_conditions.extend(self._convert_filter(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_id_filter(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=AgentConditions.by_id_contains,
            equals_factory=AgentConditions.by_id_equals,
            starts_with_factory=AgentConditions.by_id_starts_with,
            ends_with_factory=AgentConditions.by_id_ends_with,
            in_factory=AgentConditions.by_id_in,
        )

    def _convert_scaling_group_filter(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=AgentConditions.by_scaling_group_contains,
            equals_factory=AgentConditions.by_scaling_group_equals,
            starts_with_factory=AgentConditions.by_scaling_group_starts_with,
            ends_with_factory=AgentConditions.by_scaling_group_ends_with,
            in_factory=AgentConditions.by_scaling_group_in,
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

    async def get_total_resources(self) -> TotalResourceData:
        """Retrieve aggregate resource capacity/usage across all agents."""
        action_result: GetTotalResourcesActionResult = (
            await self._processors.agent.get_total_resources.wait_for_complete(
                GetTotalResourcesAction()
            )
        )
        return action_result.total_resources

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
                auto_terminate_abusing_kernel=False,
                compute_plugins=(
                    ComputePluginsGQLDTO(
                        entries=[
                            ComputePluginEntryDTO(
                                plugin_name=k,
                                value=json.dumps(v) if isinstance(v, Mapping) else str(v),
                            )
                            for k, v in data.compute_plugins.items()
                        ]
                    )
                    if data.compute_plugins
                    else None
                ),
            ),
            network_info=AgentNetworkInfo(
                region=data.region,
                addr=data.addr,
            ),
            scaling_group=data.scaling_group,
            permissions=[p.value for p in detail.permissions],
        )
