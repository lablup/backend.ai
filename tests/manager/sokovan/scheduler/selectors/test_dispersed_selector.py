"""Test DispersedAgentSelector implementation."""

from decimal import Decimal

import pytest

from ai.backend.common.types import AgentId
from ai.backend.manager.sokovan.scheduler.selectors.dispersed import DispersedAgentSelector
from ai.backend.manager.sokovan.scheduler.selectors.selector import AgentSelector

from .conftest import create_agent_info, create_selection_criteria


class TestDispersedAgentSelector:
    """Test dispersed agent selector behavior."""

    @pytest.mark.asyncio
    async def test_prefers_more_available_resources(self, sample_agents):
        """Test that selector prefers agents with more available resources."""
        strategy = DispersedAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria()

        result = await selector.select_agent(sample_agents, criteria)
        # Should select agent-3 (most available resources: 8 CPU, 16384 mem free)
        assert result == AgentId("agent-3")

    @pytest.mark.asyncio
    async def test_unutilized_capabilities_preference(self):
        """Test that agents with fewer unutilized capabilities are preferred."""
        agents = [
            create_agent_info(
                agent_id="specialized",
                available_slots={
                    "cpu": Decimal("16"),
                    "mem": Decimal("32768"),
                },
            ),
            create_agent_info(
                agent_id="versatile",
                available_slots={
                    "cpu": Decimal("16"),
                    "mem": Decimal("32768"),
                    "cuda.shares": Decimal("4"),
                    "tpu": Decimal("2"),
                },
            ),
        ]

        strategy = DispersedAgentSelector(["cpu", "mem"])
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
        # Should prefer specialized agent (fewer unutilized capabilities)
        assert result == AgentId("specialized")

    @pytest.mark.asyncio
    async def test_resource_priority_order(self):
        """Test that resource priority order affects selection."""
        agents = [
            create_agent_info(
                agent_id="more-cpu",
                available_slots={"cpu": Decimal("16"), "mem": Decimal("8192")},
                occupied_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
            ),
            create_agent_info(
                agent_id="more-mem",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("32768")},
                occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
            ),
        ]

        # CPU priority: should select more-cpu (14 CPU available)
        strategy = DispersedAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria()

        result = await selector.select_agent(agents, criteria)
        assert result == AgentId("more-cpu")

        # Memory priority: should select more-mem (24576 mem available)
        strategy = DispersedAgentSelector(["mem", "cpu"])
        selector = AgentSelector(strategy)

        result = await selector.select_agent(agents, criteria)
        assert result == AgentId("more-mem")

    @pytest.mark.asyncio
    async def test_balanced_distribution(self):
        """Test that selector distributes load across agents."""
        # Start with three equally free agents
        agents = [
            create_agent_info(
                agent_id=f"agent-{i}",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("0"), "mem": Decimal("0")},
            )
            for i in range(3)
        ]

        strategy = DispersedAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria()

        # All agents are equal, so any can be selected
        result = await selector.select_agent(agents, criteria)
        assert result in [AgentId(f"agent-{i}") for i in range(3)]

        # Simulate allocation on agent-0
        agents[0] = create_agent_info(
            agent_id="agent-0",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            occupied_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
        )

        # Should now prefer agent-1 or agent-2
        result = await selector.select_agent(agents, criteria)
        assert result in [AgentId("agent-1"), AgentId("agent-2")]

    @pytest.mark.asyncio
    async def test_gpu_workload_distribution(self, gpu_agents):
        """Test distribution of GPU workloads."""
        strategy = DispersedAgentSelector(["cuda.shares", "cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria(
            requested_slots={
                "cpu": Decimal("4"),
                "mem": Decimal("8192"),
                "cuda.shares": Decimal("1"),
            }
        )

        result = await selector.select_agent(gpu_agents, criteria)
        # Should select gpu-agent-1 (more GPU shares available: 3 vs 2)
        assert result == AgentId("gpu-agent-1")

    @pytest.mark.asyncio
    async def test_extreme_resource_difference(self):
        """Test selection with extreme resource differences."""
        agents = [
            create_agent_info(
                agent_id="tiny",
                available_slots={"cpu": Decimal("2"), "mem": Decimal("1024")},
                occupied_slots={"cpu": Decimal("1.5"), "mem": Decimal("768")},
            ),
            create_agent_info(
                agent_id="huge",
                available_slots={"cpu": Decimal("128"), "mem": Decimal("524288")},
                occupied_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            ),
        ]

        strategy = DispersedAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria(
            requested_slots={"cpu": Decimal("0.5"), "mem": Decimal("256")}
        )

        result = await selector.select_agent(agents, criteria)
        # Should strongly prefer huge agent
        assert result == AgentId("huge")
