"""Agent adapter bridging DTOs and Processors."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.agent.request import (
    AdminSearchAgentsInput,
    AgentFilter,
    AgentOrder,
    UpdateAgentResourceGroupBody,
    UpdateAgentResourceGroupInput,
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
    UpdateAgentResourceGroupPayload,
)
from ai.backend.common.dto.manager.v2.agent.types import (
    AgentStatusFilter,
    ConflictingSessionCleanupPolicyEnum,
)
from ai.backend.common.resource.types import TotalResourceData
from ai.backend.common.types import AgentId
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.agent.types import AgentDetailData, AgentStatus
from ai.backend.manager.data.permission.permission_defs import AgentPermission
from ai.backend.manager.data.resource_slot.types import AgentResourceData
from ai.backend.manager.models.agent.conditions import AgentConditions
from ai.backend.manager.models.agent.orders import (
    DEFAULT_BACKWARD_ORDER,
    DEFAULT_FORWARD_ORDER,
    TIEBREAKER_ORDER,
    resolve_order,
)
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.resource_slot.searchers import AgentResourceSearcher
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.services.agent.actions.bulk_get import BulkGetAgentsAction
from ai.backend.manager.services.agent.actions.bulk_load_container_counts import (
    BulkLoadContainerCountsAction,
)
from ai.backend.manager.services.agent.actions.bulk_load_permissions import (
    BulkLoadAgentPermissionsAction,
)
from ai.backend.manager.services.agent.actions.bulk_lookup import BulkLookupAgentsAction
from ai.backend.manager.services.agent.actions.get_total_resources import (
    GetTotalResourcesAction,
    GetTotalResourcesActionResult,
)
from ai.backend.manager.services.agent.actions.scoped_search_resources import (
    ScopedSearchAgentResourcesAction,
)
from ai.backend.manager.services.agent.actions.search_agents import SearchAgentsAction
from ai.backend.manager.services.agent.actions.update_resource_group import (
    UpdateAgentResourceGroupAction,
)
from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.agent.types import ConflictingSessionCleanupPolicy

_AGENT_PAGINATION_SPEC = PaginationSpec(
    forward_order=DEFAULT_FORWARD_ORDER,
    backward_order=DEFAULT_BACKWARD_ORDER,
    forward_condition_factory=AgentConditions.by_cursor_forward,
    backward_condition_factory=AgentConditions.by_cursor_backward,
    tiebreaker_order=TIEBREAKER_ORDER,
)


class AgentAdapter(BaseAdapter):
    """Adapter for agent domain operations."""

    _agent: AgentProcessors

    def __init__(self, agent: AgentProcessors) -> None:
        self._agent = agent

    # ------------------------------------------------------------------ batch load (DataLoader)

    async def batch_load_by_ids(
        self, agent_ids: Sequence[AgentId]
    ) -> list[AgentNode | Exception | None]:
        """Batch load agents by name for DataLoader use.

        One answer per name in the given order: the node, ``None`` for a name matching
        no agent, and the denial for one the caller may not read. The names resolve
        into uuids first, since that is what each agent is checked by; the slot rows
        and the caller's permissions are read for the agents that passed.
        """
        if not agent_ids:
            return []
        lookup = await self._agent.bulk_lookup.run(BulkLookupAgentsAction(agent_ids=agent_ids))
        uuids = [lookup.resolved[agent_id] for agent_id in agent_ids if agent_id in lookup.resolved]
        got = await self._agent.bulk_get.run(BulkGetAgentsAction(ids=uuids))
        agents = got.values()
        errors = got.errors()
        permitted = [agent.uuid for agent in agents.values()]
        resources = await self._load_resources(permitted)
        permissions = await self._load_permissions(permitted)
        nodes: list[AgentNode | Exception | None] = []
        for agent_id in agent_ids:
            uuid = lookup.resolved.get(agent_id)
            if uuid is None:
                nodes.append(None)
                continue
            agent = agents.get(uuid)
            if agent is None:
                nodes.append(self.batch_load_failure(errors.get(uuid)))
                continue
            nodes.append(
                self._data_to_dto(
                    AgentDetailData(
                        agent=agent,
                        resources=resources.get(agent.id, []),
                        permissions=permissions.get(uuid, []),
                    )
                )
            )
        return nodes

    async def batch_load_by_uuids(
        self, agent_uuids: Sequence[AgentUUID]
    ) -> list[AgentNode | Exception | None]:
        """Batch load agents by entity id for DataLoader use.

        Answers the way :meth:`batch_load_by_ids` does, taking the uuid each agent is
        checked by instead of its name.
        """
        if not agent_uuids:
            return []
        got = await self._agent.bulk_get.run(BulkGetAgentsAction(ids=list(agent_uuids)))
        agents = got.values()
        errors = got.errors()
        permitted = [agent.uuid for agent in agents.values()]
        resources = await self._load_resources(permitted)
        permissions = await self._load_permissions(permitted)
        nodes: list[AgentNode | Exception | None] = []
        for agent_uuid in agent_uuids:
            agent = agents.get(agent_uuid)
            if agent is None:
                nodes.append(self.batch_load_failure(errors.get(agent_uuid)))
                continue
            nodes.append(
                self._data_to_dto(
                    AgentDetailData(
                        agent=agent,
                        resources=resources.get(agent.id, []),
                        permissions=permissions.get(agent_uuid, []),
                    )
                )
            )
        return nodes

    async def _load_permissions(
        self, agent_uuids: Sequence[AgentUUID]
    ) -> Mapping[EntityIdentifier, list[AgentPermission]]:
        """What the caller holds on each named agent."""
        if not agent_uuids:
            return {}
        result = await self._agent.bulk_load_permissions.run(
            BulkLoadAgentPermissionsAction(agent_uuids=agent_uuids)
        )
        return result.values()

    async def _load_resources(
        self, agent_uuids: Sequence[AgentUUID]
    ) -> Mapping[AgentId, list[AgentResourceData]]:
        """The slot rows of the named agents, keyed by the agent's name column."""
        if not agent_uuids:
            return {}
        result = await self._agent.scoped_search_resources.run(
            ScopedSearchAgentResourcesAction(
                agent_uuids=agent_uuids,
                searcher=AgentResourceSearcher(pagination=NoPagination()),
            )
        )
        resources: dict[AgentId, list[AgentResourceData]] = {}
        for item in result.items:
            resources.setdefault(AgentId(item.agent_id), []).append(item)
        return resources

    async def batch_load_container_counts(
        self, agent_ids: Sequence[AgentId]
    ) -> list[int | Exception]:
        """Batch load container counts by agent name for DataLoader use.

        One answer per name in the given order: the count, ``0`` for a name matching
        no agent, and the denial for one the caller may not read. Checked the way the
        agents themselves are: through the bulk get, per agent.
        """
        if not agent_ids:
            return []
        lookup = await self._agent.bulk_lookup.run(BulkLookupAgentsAction(agent_ids=agent_ids))
        uuids = [lookup.resolved[agent_id] for agent_id in agent_ids if agent_id in lookup.resolved]
        got = await self._agent.bulk_get.run(BulkGetAgentsAction(ids=uuids))
        permitted = [uuid for uuid in uuids if uuid in got.values()]
        counts: Mapping[EntityIdentifier, int] = {}
        count_errors: Mapping[EntityIdentifier, Exception] = {}
        if permitted:
            counted = await self._agent.bulk_load_container_counts.run(
                BulkLoadContainerCountsAction(agent_uuids=permitted)
            )
            counts = counted.values()
            count_errors = counted.errors()
        answers: list[int | Exception] = []
        for agent_id in agent_ids:
            uuid = lookup.resolved.get(agent_id)
            if uuid is None:
                answers.append(0)
                continue
            error = self.batch_load_failure(got.errors().get(uuid) or count_errors.get(uuid))
            if error is not None:
                answers.append(error)
                continue
            answers.append(counts.get(uuid, 0))
        return answers

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
        action_result = await self._agent.search_agents.run(SearchAgentsAction(querier=querier))
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
            condition = self._convert_resource_group_filter(f.scaling_group)
            if condition is not None:
                conditions.append(condition)
        if f.labels is not None:
            conditions.extend(
                self._convert_entity_label_nested_filter(f.labels, AgentConditions.labels)
            )
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

    def _convert_resource_group_filter(self, sf: StringFilter) -> QueryCondition | None:
        return self.convert_string_filter(
            sf,
            contains_factory=AgentConditions.by_resource_group_contains,
            equals_factory=AgentConditions.by_resource_group_equals,
            starts_with_factory=AgentConditions.by_resource_group_starts_with,
            ends_with_factory=AgentConditions.by_resource_group_ends_with,
            in_factory=AgentConditions.by_resource_group_in,
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

    # ------------------------------------------------------------------ update

    async def update_resource_group_from_body(
        self,
        agent_id: AgentId,
        body: UpdateAgentResourceGroupBody,
    ) -> UpdateAgentResourceGroupPayload:
        """Change the resource group of an agent whose ID is carried separately.

        Used by the REST handler, where the agent ID comes from the URL path
        while the body only carries the mutable part.
        """
        return await self.update_resource_group(
            UpdateAgentResourceGroupInput(
                agent_id=agent_id,
                resource_group_id=body.resource_group_id,
                policy=body.policy,
                force=body.force,
            )
        )

    async def update_resource_group(
        self,
        input: UpdateAgentResourceGroupInput,
    ) -> UpdateAgentResourceGroupPayload:
        """Change an agent's resource group, cleaning up conflicting sessions per policy."""
        applied_policy = input.policy or ConflictingSessionCleanupPolicyEnum.TERMINATE
        action_result = await self._agent.update_resource_group.run(
            UpdateAgentResourceGroupAction(
                agent_id=input.agent_id,
                resource_group_id=input.resource_group_id,
                policy=ConflictingSessionCleanupPolicy(applied_policy.value),
                force=input.force,
            )
        )
        return UpdateAgentResourceGroupPayload(
            agent_id=action_result.agent_id,
            resource_group_id=action_result.resource_group_id,
            policy=applied_policy,
            conflicting_session_ids=[
                SessionID(sid) for sid in action_result.conflicting_session_ids
            ],
            terminating_session_ids=[
                SessionID(sid) for sid in action_result.terminating_session_ids
            ],
        )

    async def get_total_resources(self) -> TotalResourceData:
        """Retrieve aggregate resource capacity/usage across all agents."""
        action_result: GetTotalResourcesActionResult = await self._agent.get_total_resources.run(
            GetTotalResourcesAction()
        )
        return action_result.total_resources

    @staticmethod
    def _data_to_dto(detail: AgentDetailData) -> AgentNode:
        """Convert data layer type to Pydantic DTO."""
        data = detail.agent
        available_slots = detail.available_slots()
        occupied_slots = detail.occupied_slots()
        return AgentNode(
            id=str(data.id),
            uuid=data.uuid,
            resource_info=AgentResourceInfo(
                capacity=dict(available_slots.to_json()),
                used=dict(occupied_slots.to_json()),
                free=dict((available_slots - occupied_slots).to_json()),
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
            scaling_group=data.resource_group,
            permissions=[p.value for p in detail.permissions],
        )
