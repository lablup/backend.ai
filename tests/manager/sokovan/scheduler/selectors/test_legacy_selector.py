"""Test LegacyAgentSelector implementation."""

from decimal import Decimal

import pytest

from ai.backend.common.types import AgentId
from ai.backend.manager.sokovan.scheduler.selectors.legacy import LegacyAgentSelector
from ai.backend.manager.sokovan.scheduler.selectors.selector import AgentSelector

from .conftest import create_agent_info, create_selection_criteria


class TestLegacyAgentSelector:
    """Test legacy agent selector behavior."""

    @pytest.mark.asyncio
    async def test_resource_priority_selection(self, sample_agents):
        """Test that agents are selected based on resource priority."""
        strategy = LegacyAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria()

        result = await selector.select_agent(sample_agents, criteria)
        # Should select agent-3 (most CPU available after agent-1 and agent-2)
        assert result == AgentId("agent-3")

    @pytest.mark.asyncio
    async def test_unutilized_capabilities_preference(self):
        """Test preference for agents with fewer unutilized capabilities."""
        agents = [
            create_agent_info(
                agent_id="gpu-capable",
                available_slots={
                    "cpu": Decimal("8"),
                    "mem": Decimal("16384"),
                    "cuda.shares": Decimal("4"),
                    "tpu": Decimal("2"),
                },
            ),
            create_agent_info(
                agent_id="cpu-only",
                available_slots={
                    "cpu": Decimal("8"),
                    "mem": Decimal("16384"),
                },
            ),
        ]

        strategy = LegacyAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        # Request only CPU and memory
        criteria = create_selection_criteria(
            requested_slots={
                "cpu": Decimal("2"),
                "mem": Decimal("4096"),
                "cuda.shares": Decimal("0"),
                "tpu": Decimal("0"),
            }
        )

        result = await selector.select_agent(agents, criteria)
        # Should prefer cpu-only agent (fewer unutilized capabilities)
        assert result == AgentId("cpu-only")

    @pytest.mark.asyncio
    async def test_multiple_resource_priorities(self):
        """Test selection with multiple resource priorities."""
        agents = [
            create_agent_info(
                agent_id="high-cpu-low-mem",
                available_slots={"cpu": Decimal("16"), "mem": Decimal("8192")},
                occupied_slots={"cpu": Decimal("2"), "mem": Decimal("6144")},
            ),
            create_agent_info(
                agent_id="low-cpu-high-mem",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("32768")},
                occupied_slots={"cpu": Decimal("6"), "mem": Decimal("4096")},
            ),
        ]

        # Test with CPU priority
        strategy = LegacyAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria()

        result = await selector.select_agent(agents, criteria)
        assert result == AgentId("high-cpu-low-mem")

        # Test with memory priority
        strategy = LegacyAgentSelector(["mem", "cpu"])
        selector = AgentSelector(strategy)

        result = await selector.select_agent(agents, criteria)
        assert result == AgentId("low-cpu-high-mem")

    @pytest.mark.asyncio
    async def test_single_agent_selection(self):
        """Test selection when only one agent is available."""
        agents = [create_agent_info(agent_id="single-agent")]

        strategy = LegacyAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria()

        result = await selector.select_agent(agents, criteria)
        assert result == AgentId("single-agent")

    @pytest.mark.asyncio
    async def test_equal_agents_deterministic_selection(self):
        """Test that selection is deterministic when agents have equal resources."""
        agents = [
            create_agent_info(
                agent_id="agent-a",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            ),
            create_agent_info(
                agent_id="agent-b",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            ),
        ]

        strategy = LegacyAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria()

        # Run multiple times to ensure deterministic behavior
        results = []
        for _ in range(5):
            result = await selector.select_agent(agents, criteria)
            results.append(result)

        # All results should be the same
        assert all(r == results[0] for r in results)
        assert results[0] in [AgentId("agent-a"), AgentId("agent-b")]
