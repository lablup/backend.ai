"""Test ConcentratedAgentSelector implementation."""

from decimal import Decimal

import pytest

from ai.backend.common.types import AgentId
from ai.backend.manager.sokovan.scheduler.selectors.concentrated import (
    ConcentratedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.selectors.selector import AgentSelector

from .conftest import create_agent_info, create_selection_criteria


class TestConcentratedAgentSelector:
    """Test concentrated agent selector behavior."""

    @pytest.mark.asyncio
    async def test_prefers_less_available_resources(self, sample_agents):
        """Test that selector prefers agents with less available resources."""
        strategy = ConcentratedAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria()

        result = await selector.select_agent(sample_agents, criteria)
        # Should select agent-2 (least available resources: 4 CPU, 8192 mem free)
        assert result == AgentId("agent-2")

    @pytest.mark.asyncio
    async def test_endpoint_kernel_count_priority(self):
        """Test that agents with fewer kernels at endpoint are preferred."""
        agents = [
            create_agent_info(
                agent_id="busy-endpoint",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
            ),
            create_agent_info(
                agent_id="free-endpoint",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
            ),
        ]

        strategy = ConcentratedAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria(
            session_type="INFERENCE",
            enforce_spreading_endpoint_replica=True,
            kernel_counts_at_endpoint={"busy-endpoint": 5, "free-endpoint": 1},
        )

        result = await selector.select_agent(agents, criteria)
        # Should prefer agent with fewer kernels at endpoint
        assert result == AgentId("free-endpoint")

    @pytest.mark.asyncio
    async def test_unutilized_capabilities_consideration(self):
        """Test that unutilized capabilities are considered in selection."""
        agents = [
            create_agent_info(
                agent_id="specialized",
                available_slots={
                    "cpu": Decimal("4"),
                    "mem": Decimal("8192"),
                },
                occupied_slots={
                    "cpu": Decimal("2"),
                    "mem": Decimal("4096"),
                },
            ),
            create_agent_info(
                agent_id="versatile",
                available_slots={
                    "cpu": Decimal("4"),
                    "mem": Decimal("8192"),
                    "cuda.shares": Decimal("2"),
                    "tpu": Decimal("1"),
                },
                occupied_slots={
                    "cpu": Decimal("2"),
                    "mem": Decimal("4096"),
                    "cuda.shares": Decimal("0"),
                    "tpu": Decimal("0"),
                },
            ),
        ]

        strategy = ConcentratedAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        # Request only CPU and memory
        criteria = create_selection_criteria(
            requested_slots={
                "cpu": Decimal("1"),
                "mem": Decimal("2048"),
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
                agent_id="high-cpu-usage",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("6"), "mem": Decimal("4096")},
            ),
            create_agent_info(
                agent_id="high-mem-usage",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("2"), "mem": Decimal("12288")},
            ),
        ]

        # CPU priority: should select high-cpu-usage (less CPU available)
        strategy = ConcentratedAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria()

        result = await selector.select_agent(agents, criteria)
        assert result == AgentId("high-cpu-usage")

        # Memory priority: should select high-mem-usage (less memory available)
        strategy = ConcentratedAgentSelector(["mem", "cpu"])
        selector = AgentSelector(strategy)

        result = await selector.select_agent(agents, criteria)
        assert result == AgentId("high-mem-usage")

    @pytest.mark.asyncio
    async def test_complex_selection_scenario(self):
        """Test selection with multiple factors."""
        agents = [
            create_agent_info(
                agent_id="agent-a",
                available_slots={
                    "cpu": Decimal("16"),
                    "mem": Decimal("32768"),
                    "cuda.shares": Decimal("4"),
                },
                occupied_slots={
                    "cpu": Decimal("8"),
                    "mem": Decimal("16384"),
                    "cuda.shares": Decimal("2"),
                },
            ),
            create_agent_info(
                agent_id="agent-b",
                available_slots={
                    "cpu": Decimal("16"),
                    "mem": Decimal("32768"),
                },
                occupied_slots={
                    "cpu": Decimal("12"),
                    "mem": Decimal("8192"),
                },
            ),
            create_agent_info(
                agent_id="agent-c",
                available_slots={
                    "cpu": Decimal("16"),
                    "mem": Decimal("32768"),
                },
                occupied_slots={
                    "cpu": Decimal("4"),
                    "mem": Decimal("24576"),
                },
            ),
        ]

        strategy = ConcentratedAgentSelector(["cpu", "mem"])
        selector = AgentSelector(strategy)
        criteria = create_selection_criteria(
            requested_slots={
                "cpu": Decimal("2"),
                "mem": Decimal("4096"),
                "cuda.shares": Decimal("0"),
            },
            session_type="INFERENCE",
            enforce_spreading_endpoint_replica=True,
            kernel_counts_at_endpoint={"agent-a": 2, "agent-b": 2, "agent-c": 1},
        )

        result = await selector.select_agent(agents, criteria)
        # Should select agent-c (lowest endpoint kernel count)
        assert result == AgentId("agent-c")
