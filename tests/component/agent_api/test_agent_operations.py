"""Component tests for agent operations covering search, resource management, and permissions.

This test file complements tests/component/agent_api/test_agent_api.py by testing
compound filters and empty result scenarios for agent search operations.
"""

from __future__ import annotations

import secrets

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.agent import SearchAgentsRequest
from ai.backend.common.dto.manager.agent.request import AgentFilter
from ai.backend.common.dto.manager.agent.types import AgentStatusEnum, AgentStatusEnumFilter
from ai.backend.common.dto.manager.query import StringFilter


class TestAgentSearchCompoundFilters:
    """Test scenarios for agent search with compound filters."""

    async def test_compound_filters_status_and_resource_group(
        self,
        admin_registry: BackendAIClientRegistry,
        agent_fixture: str,
        scaling_group_fixture: str,
    ) -> None:
        """Compound filters (status + resource_group) return intersection of conditions."""
        # Search with both status=ALIVE and resource_group filters
        result = await admin_registry.agent.search_agents(
            SearchAgentsRequest(
                filter=AgentFilter(
                    status=AgentStatusEnumFilter(equals=AgentStatusEnum.ALIVE),
                    resource_group=StringFilter(equals=scaling_group_fixture),
                ),
            ),
        )

        # All results should match both filters
        for item in result.items:
            assert item.status == AgentStatusEnum.ALIVE
            assert item.resource_group == scaling_group_fixture

        # Our fixture agent should be in the results
        agent_ids = [item.id for item in result.items]
        assert agent_fixture in agent_ids

    async def test_empty_result_nonexistent_resource_group(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Empty result returns total=0 and empty items."""
        # Search for a non-existent resource group
        nonexistent_rg = f"nonexistent-rg-{secrets.token_hex(8)}"

        result = await admin_registry.agent.search_agents(
            SearchAgentsRequest(
                filter=AgentFilter(
                    resource_group=StringFilter(equals=nonexistent_rg),
                ),
            ),
        )

        assert result.pagination.total == 0
        assert len(result.items) == 0


class TestAgentPermissionBoundaries:
    """Test scenarios for agent permission boundaries."""

    async def test_regular_user_cannot_search_agents(
        self,
        user_registry: BackendAIClientRegistry,
        agent_fixture: str,
    ) -> None:
        """Regular user cannot search agents → 403 PermissionDeniedError."""
        # Regular users should get permission denied when trying to search agents
        with pytest.raises(PermissionDeniedError):
            await user_registry.agent.search_agents(
                SearchAgentsRequest(),
            )
