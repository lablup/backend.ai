"""Agent handler class using constructor dependency injection."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from http import HTTPStatus
from typing import Final

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.dto.manager.agent.request import SearchAgentsRequest
from ai.backend.common.dto.manager.agent.response import SearchAgentsResponse
from ai.backend.common.dto.manager.pagination import PaginationInfo
from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.agent.types import AgentDetailData
from ai.backend.manager.data.resource_slot.types import AgentResourceData
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.models.agent.searchers import AgentSearcher
from ai.backend.manager.models.resource_slot.searchers import AgentResourceSearcher
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.specs.searcher import GlobalSearcher
from ai.backend.manager.services.agent.actions.scoped_search_resources import (
    ScopedSearchAgentResourcesAction,
)
from ai.backend.manager.services.agent.actions.search_agents import SearchAgentsAction
from ai.backend.manager.services.agent.processors import AgentProcessors

from .adapter import AgentAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AgentHandler:
    """Agent API handler with constructor-injected dependencies."""

    def __init__(self, *, agent: AgentProcessors) -> None:
        self._agent = agent
        self._adapter = AgentAdapter()

    async def search_agents(
        self,
        body: BodyParam[SearchAgentsRequest],
        ctx: UserContext,
    ) -> APIResponse:
        """Search agents with filters, orders, and pagination."""

        querier = self._adapter.build_querier(body.parsed)

        action_result = await self._agent.search_agents.run(
            SearchAgentsAction(
                searcher=GlobalSearcher(
                    used_by=(),
                    searcher=AgentSearcher(
                        pagination=querier.pagination,
                        conditions=querier.conditions,
                        orders=querier.orders,
                    ),
                )
            )
        )
        resources = await self._load_resources([agent.uuid for agent in action_result.items])

        resp = SearchAgentsResponse(
            items=[
                self._adapter.convert_to_dto(
                    AgentDetailData(
                        agent=agent, resources=resources.get(agent.id, []), permissions=[]
                    )
                )
                for agent in action_result.items
            ],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

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
