"""Component tests for the Agent REST API via Client SDK v2.

Tests exercise the manager's ``POST /agents/search`` endpoint through the
:class:`AgentClient.search_agents` method.  Only ``search_agents`` is tested
because the ``get_agent`` and ``get_resource_stats`` handlers are not yet
implemented on the server side.
"""

from __future__ import annotations

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.agent import (
    SearchAgentsRequest,
    SearchAgentsResponse,
)
from ai.backend.common.dto.manager.agent.request import AgentFilter, AgentOrder
from ai.backend.common.dto.manager.agent.types import (
    AgentOrderField,
    AgentStatusEnum,
    AgentStatusEnumFilter,
    OrderDirection,
)
from ai.backend.common.dto.manager.query import StringFilter


class TestSearchAgents:
    """Tests for ``AgentClient.search_agents``."""

    async def test_admin_searches_agents(
        self,
        admin_registry: BackendAIClientRegistry,
        agent_fixture: str,
    ) -> None:
        """Admin can search all agents; the fixture agent appears in the results."""
        result = await admin_registry.agent.search_agents(
            SearchAgentsRequest(),
        )
        assert isinstance(result, SearchAgentsResponse)
        agent_ids = [item.id for item in result.items]
        assert agent_fixture in agent_ids
        assert result.pagination.total >= 1

    async def test_admin_searches_agents_with_status_filter_alive(
        self,
        admin_registry: BackendAIClientRegistry,
        agent_fixture: str,
    ) -> None:
        """Filtering by ALIVE status returns the fixture agent."""
        result = await admin_registry.agent.search_agents(
            SearchAgentsRequest(
                filter=AgentFilter(
                    status=AgentStatusEnumFilter(equals=AgentStatusEnum.ALIVE),
                ),
            ),
        )
        assert isinstance(result, SearchAgentsResponse)
        agent_ids = [item.id for item in result.items]
        assert agent_fixture in agent_ids

    async def test_admin_searches_agents_with_status_filter_terminated(
        self,
        admin_registry: BackendAIClientRegistry,
        agent_fixture: str,
    ) -> None:
        """Filtering by TERMINATED status returns empty when no terminated agents exist."""
        result = await admin_registry.agent.search_agents(
            SearchAgentsRequest(
                filter=AgentFilter(
                    status=AgentStatusEnumFilter(equals=AgentStatusEnum.TERMINATED),
                ),
            ),
        )
        assert isinstance(result, SearchAgentsResponse)
        agent_ids = [item.id for item in result.items]
        assert agent_fixture not in agent_ids

    async def test_admin_searches_agents_with_resource_group_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        agent_fixture: str,
        scaling_group_fixture: str,
    ) -> None:
        """Filtering by resource_group returns agents in that scaling group."""
        result = await admin_registry.agent.search_agents(
            SearchAgentsRequest(
                filter=AgentFilter(
                    resource_group=StringFilter(equals=scaling_group_fixture),
                ),
            ),
        )
        assert isinstance(result, SearchAgentsResponse)
        agent_ids = [item.id for item in result.items]
        assert agent_fixture in agent_ids
        for item in result.items:
            assert item.resource_group == scaling_group_fixture

    async def test_admin_searches_agents_with_ordering(
        self,
        admin_registry: BackendAIClientRegistry,
        agent_fixture: str,
    ) -> None:
        """Ordering by id ASC returns results in ascending order."""
        result = await admin_registry.agent.search_agents(
            SearchAgentsRequest(
                order=[
                    AgentOrder(
                        field=AgentOrderField.ID,
                        direction=OrderDirection.ASC,
                    ),
                ],
            ),
        )
        assert isinstance(result, SearchAgentsResponse)
        ids = [item.id for item in result.items]
        assert ids == sorted(ids)

    async def test_admin_searches_agents_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
        agent_fixture: str,
    ) -> None:
        """Pagination with limit=1, offset=0 returns exactly 1 item with correct total."""
        result = await admin_registry.agent.search_agents(
            SearchAgentsRequest(limit=1, offset=0),
        )
        assert isinstance(result, SearchAgentsResponse)
        assert len(result.items) <= 1
        assert result.pagination.total >= 1
        assert result.pagination.offset == 0
        assert result.pagination.limit == 1

    async def test_regular_user_cannot_search_agents(
        self,
        user_registry: BackendAIClientRegistry,
        agent_fixture: str,
    ) -> None:
        """Regular (non-superadmin) users receive 403 PermissionDeniedError."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.agent.search_agents(
                SearchAgentsRequest(),
            )
