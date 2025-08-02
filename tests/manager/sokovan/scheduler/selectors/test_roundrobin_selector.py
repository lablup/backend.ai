"""Test RoundRobinAgentSelector implementation."""

from decimal import Decimal

import pytest

from ai.backend.common.types import AgentId
from ai.backend.manager.sokovan.scheduler.selectors.roundrobin import RoundRobinAgentSelector
from ai.backend.manager.sokovan.scheduler.selectors.selector import AgentSelector

from .conftest import create_agent_info, create_selection_criteria


class TestRoundRobinAgentSelector:
    """Test round-robin agent selector behavior."""

    @pytest.mark.asyncio
    async def test_sequential_selection(self, sample_agents):
        """Test that agents are selected sequentially."""
        # First selection with index 0
        strategy = RoundRobinAgentSelector(next_index=0)
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria()

        result = await selector.select_agent(sample_agents, criteria)
        # Agents are sorted by ID, so agent-1 should be first
        assert result == AgentId("agent-1")

        # Second selection with index 1
        strategy = RoundRobinAgentSelector(next_index=1)
        selector = AgentSelector(strategy)

        result = await selector.select_agent(sample_agents, criteria)
        assert result == AgentId("agent-2")

        # Third selection with index 2
        strategy = RoundRobinAgentSelector(next_index=2)
        selector = AgentSelector(strategy)

        result = await selector.select_agent(sample_agents, criteria)
        assert result == AgentId("agent-3")

    @pytest.mark.asyncio
    async def test_index_wraparound(self, sample_agents):
        """Test that index wraps around when exceeding agent count."""
        # Index 3 should wrap to 0 (3 % 3 = 0)
        strategy = RoundRobinAgentSelector(next_index=3)
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria()

        result = await selector.select_agent(sample_agents, criteria)
        assert result == AgentId("agent-1")

        # Large index should also wrap correctly
        strategy = RoundRobinAgentSelector(next_index=10)
        selector = AgentSelector(strategy)

        result = await selector.select_agent(sample_agents, criteria)
        # 10 % 3 = 1, so should select agent-2
        assert result == AgentId("agent-2")

    @pytest.mark.asyncio
    async def test_single_agent_always_selected(self):
        """Test that single agent is always selected regardless of index."""
        agents = [create_agent_info(agent_id="single-agent")]
        criteria = create_selection_criteria()

        for index in range(5):
            strategy = RoundRobinAgentSelector(next_index=index)
            selector = AgentSelector(strategy)

            result = await selector.select_agent(agents, criteria)
            assert result == AgentId("single-agent")

    @pytest.mark.asyncio
    async def test_consistent_ordering(self):
        """Test that agent ordering is consistent."""
        agents = [
            create_agent_info(agent_id="zebra"),
            create_agent_info(agent_id="alpha"),
            create_agent_info(agent_id="beta"),
        ]
        criteria = create_selection_criteria()

        # Index 0 should select first in sorted order (alpha)
        strategy = RoundRobinAgentSelector(next_index=0)
        selector = AgentSelector(strategy)

        result = await selector.select_agent(agents, criteria)
        assert result == AgentId("alpha")

        # Index 1 should select beta
        strategy = RoundRobinAgentSelector(next_index=1)
        selector = AgentSelector(strategy)

        result = await selector.select_agent(agents, criteria)
        assert result == AgentId("beta")

        # Index 2 should select zebra
        strategy = RoundRobinAgentSelector(next_index=2)
        selector = AgentSelector(strategy)

        result = await selector.select_agent(agents, criteria)
        assert result == AgentId("zebra")

    @pytest.mark.asyncio
    async def test_filtered_agents_round_robin(self):
        """Test round-robin works correctly after filtering."""
        agents = [
            create_agent_info(
                agent_id="small-1",
                available_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
            ),
            create_agent_info(
                agent_id="large-1",
                available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
            ),
            create_agent_info(
                agent_id="small-2",
                available_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
            ),
            create_agent_info(
                agent_id="large-2",
                available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
            ),
        ]

        # Request resources that only large agents can satisfy
        criteria = create_selection_criteria(
            requested_slots={"cpu": Decimal("8"), "mem": Decimal("16384")}
        )

        # Index 0 should select first large agent
        strategy = RoundRobinAgentSelector(next_index=0)
        selector = AgentSelector(strategy)

        result = await selector.select_agent(agents, criteria)
        assert result == AgentId("large-1")

        # Index 1 should select second large agent
        strategy = RoundRobinAgentSelector(next_index=1)
        selector = AgentSelector(strategy)

        result = await selector.select_agent(agents, criteria)
        assert result == AgentId("large-2")
