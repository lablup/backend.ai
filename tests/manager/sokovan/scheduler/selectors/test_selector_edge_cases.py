"""Edge case tests for agent selectors."""

import sys
import uuid
from decimal import Decimal

import pytest

from ai.backend.common.types import AgentId, ClusterMode, ResourceSlot, SessionId, SessionTypes
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.concentrated import (
    ConcentratedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.dispersed import (
    DispersedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.legacy import LegacyAgentSelector
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.roundrobin import (
    RoundRobinAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentSelectionConfig,
    AgentSelectionCriteria,
    AgentStateTracker,
    ResourceRequirements,
    SessionMetadata,
)

from .conftest import create_agent_info


class TestSelectorEdgeCases:
    """Test edge cases and error conditions for selectors."""

    @pytest.fixture
    def criteria(self) -> AgentSelectionCriteria:
        """Create standard selection criteria."""
        return AgentSelectionCriteria(
            session_metadata=SessionMetadata(
                session_id=SessionId(uuid.uuid4()),
                session_type=SessionTypes.INTERACTIVE,
                scaling_group="default",
                cluster_mode=ClusterMode.SINGLE_NODE,
            ),
            kernel_requirements={},
        )

    @pytest.fixture
    def config(self) -> AgentSelectionConfig:
        """Create standard selection config."""
        return AgentSelectionConfig(
            max_container_count=None,
            enforce_spreading_endpoint_replica=False,
        )

    def test_empty_resource_requirements(self, criteria, config):
        """Test handling of empty resource requirements."""
        agents = [
            create_agent_info(
                agent_id="agent-1",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
            ),
            create_agent_info(
                agent_id="agent-2",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
            ),
        ]

        # Empty resource request
        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({}),  # No resources requested
            required_architecture="x86_64",
        )

        selectors = [
            ConcentratedAgentSelector(["cpu", "mem"]),
            DispersedAgentSelector(["cpu", "mem"]),
            LegacyAgentSelector(["cpu", "mem"]),
            RoundRobinAgentSelector(next_index=0),
        ]

        # All selectors should handle empty requests
        for selector in selectors:
            # Convert agents to trackers
            trackers = [AgentStateTracker(original_agent=agent) for agent in agents]
            result = selector.select_tracker_by_strategy(trackers, resource_req, criteria, config)
            assert result is not None
            assert result.original_agent.agent_id in [AgentId("agent-1"), AgentId("agent-2")]

    def test_zero_resource_values(self, criteria, config):
        """Test handling of zero resource values in requests."""
        agents = [
            create_agent_info(
                agent_id="agent-1",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            )
        ]

        # Request with zero values
        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({
                "cpu": Decimal("0"),
                "mem": Decimal("0"),
                "cuda.shares": Decimal("0"),
            }),
            required_architecture="x86_64",
        )

        selector = ConcentratedAgentSelector(["cpu", "mem"])
        # Convert agents to trackers
        trackers = [AgentStateTracker(original_agent=agent) for agent in agents]
        result = selector.select_tracker_by_strategy(trackers, resource_req, criteria, config)

        # Should still select an agent
        assert result.original_agent.agent_id == AgentId("agent-1")

    def test_missing_resource_types_in_request(self, criteria, config):
        """Test when requested resource type doesn't exist on any agent."""
        agents = [
            create_agent_info(
                agent_id="cpu-only",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            ),
            create_agent_info(
                agent_id="gpu-agent",
                available_slots={
                    "cpu": Decimal("8"),
                    "mem": Decimal("16384"),
                    "cuda.shares": Decimal("4"),
                },
            ),
        ]

        # Request TPU which no agent has
        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({
                "cpu": Decimal("2"),
                "mem": Decimal("4096"),
                "tpu": Decimal("1"),
            }),
            required_architecture="x86_64",
        )

        # Agents should be filtered out by AgentSelector wrapper
        # But if passed to strategy directly, they should handle gracefully
        selector = DispersedAgentSelector(["cpu", "mem", "tpu"])

        # Both agents lack TPU, so selector should use other criteria
        # Convert agents to trackers
        trackers = [AgentStateTracker(original_agent=agent) for agent in agents]
        result = selector.select_tracker_by_strategy(trackers, resource_req, criteria, config)
        assert result is not None

    def test_extremely_large_resource_values(self, criteria, config):
        """Test handling of very large resource values."""
        agents = [
            create_agent_info(
                agent_id="normal",
                available_slots={
                    "cpu": Decimal("16"),
                    "mem": Decimal("32768"),
                },
                occupied_slots={
                    "cpu": Decimal("8"),
                    "mem": Decimal("16384"),
                },
            ),
            create_agent_info(
                agent_id="huge",
                available_slots={
                    "cpu": Decimal(str(sys.maxsize)),
                    "mem": Decimal(str(sys.maxsize)),
                },
                occupied_slots={
                    "cpu": Decimal("0"),
                    "mem": Decimal("0"),
                },
            ),
        ]

        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            required_architecture="x86_64",
        )

        # Test with different selectors
        concentrated = ConcentratedAgentSelector(["cpu", "mem"])
        dispersed = DispersedAgentSelector(["cpu", "mem"])

        # Convert agents to trackers
        trackers = [AgentStateTracker(original_agent=agent) for agent in agents]
        concentrated_choice = concentrated.select_tracker_by_strategy(
            trackers, resource_req, criteria, config
        )
        dispersed_choice = dispersed.select_tracker_by_strategy(
            trackers, resource_req, criteria, config
        )

        # Concentrated should pick normal (less available)
        assert concentrated_choice.original_agent.agent_id == AgentId("normal")
        # Dispersed should pick huge (more available)
        assert dispersed_choice.original_agent.agent_id == AgentId("huge")

    def test_decimal_precision_edge_cases(self, criteria, config):
        """Test handling of decimal precision edge cases."""
        agents = [
            create_agent_info(
                agent_id="agent-1",
                available_slots={
                    "cpu": Decimal("8.123456789012345678901234567890"),
                    "mem": Decimal("16384.99999999999999999999"),
                },
                occupied_slots={
                    "cpu": Decimal("4.000000000000000000000001"),
                    "mem": Decimal("8192.000000000000000000001"),
                },
            ),
            create_agent_info(
                agent_id="agent-2",
                available_slots={
                    "cpu": Decimal("8.123456789012345678901234567891"),  # Slightly different
                    "mem": Decimal("16385.00000000000000000001"),
                },
                occupied_slots={
                    "cpu": Decimal("4.0"),
                    "mem": Decimal("8192.0"),
                },
            ),
        ]

        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({
                "cpu": Decimal("0.000000000000000000000001"),
                "mem": Decimal("0.000000000000000000000001"),
            }),
            required_architecture="x86_64",
        )

        selector = ConcentratedAgentSelector(["cpu", "mem"])
        # Convert agents to trackers
        trackers = [AgentStateTracker(original_agent=agent) for agent in agents]
        result = selector.select_tracker_by_strategy(trackers, resource_req, criteria, config)

        # Should handle decimal precision correctly
        assert result.original_agent.agent_id in [AgentId("agent-1"), AgentId("agent-2")]

    def test_single_agent_all_strategies(self, criteria, config):
        """Test all strategies with only one agent available."""
        agent = create_agent_info(
            agent_id="lonely",
            available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
        )
        agents = [agent]

        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            required_architecture="x86_64",
        )

        selectors = [
            ConcentratedAgentSelector(["cpu", "mem"]),
            DispersedAgentSelector(["cpu", "mem"]),
            LegacyAgentSelector(["cpu", "mem"]),
            RoundRobinAgentSelector(next_index=999),  # Index way out of bounds
        ]

        # All should select the only agent
        for selector in selectors:
            # Convert agents to trackers
            trackers = [AgentStateTracker(original_agent=agent) for agent in agents]
            result = selector.select_tracker_by_strategy(trackers, resource_req, criteria, config)
            assert result.original_agent.agent_id == AgentId("lonely")

    def test_all_agents_fully_occupied(self, criteria, config):
        """Test when all agents have zero available resources."""
        agents = [
            create_agent_info(
                agent_id=f"full-{i}",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            )
            for i in range(3)
        ]

        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            required_architecture="x86_64",
        )

        # Selectors will still pick an agent (filtering happens in wrapper)
        selector = ConcentratedAgentSelector(["cpu", "mem"])
        # Convert agents to trackers
        trackers = [AgentStateTracker(original_agent=agent) for agent in agents]
        result = selector.select_tracker_by_strategy(trackers, resource_req, criteria, config)

        # Should still return an agent (they're all equal)
        assert result.original_agent.agent_id in [AgentId(f"full-{i}") for i in range(3)]

    def test_priority_with_nonexistent_resources(self, criteria, config):
        """Test resource priority list containing non-existent resource types."""
        agents = [
            create_agent_info(
                agent_id="agent-1",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("6"), "mem": Decimal("12288")},
            ),
            create_agent_info(
                agent_id="agent-2",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
            ),
        ]

        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            required_architecture="x86_64",
        )

        # Priority includes non-existent resources
        selector = ConcentratedAgentSelector(["quantum.bits", "neural.cores", "cpu", "mem"])
        # Convert agents to trackers
        trackers = [AgentStateTracker(original_agent=agent) for agent in agents]
        result = selector.select_tracker_by_strategy(trackers, resource_req, criteria, config)

        # Should ignore non-existent resources and use cpu/mem
        assert result.original_agent.agent_id == AgentId("agent-1")  # Less available resources

    # @pytest.mark.asyncio
    # async def test_empty_agent_list(self, criteria, config):
    #     """Test handling of empty agent list."""
    #     # This test needs to be rewritten for the new batch selection API
    #     # The select_agent_for_resource_requirements method no longer exists
    #     pass

    def test_special_resource_names(self, criteria, config):
        """Test handling of special characters in resource names."""
        agents = [
            create_agent_info(
                agent_id="special",
                available_slots={
                    "cpu": Decimal("8"),
                    "mem": Decimal("16384"),
                    "custom.resource-name_123": Decimal("100"),
                    "another/special@resource": Decimal("50"),
                },
                occupied_slots={
                    "cpu": Decimal("4"),
                    "mem": Decimal("8192"),
                    "custom.resource-name_123": Decimal("20"),
                    "another/special@resource": Decimal("10"),
                },
            )
        ]

        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({
                "cpu": Decimal("1"),
                "mem": Decimal("2048"),
                "custom.resource-name_123": Decimal("10"),
                "another/special@resource": Decimal("5"),
            }),
            required_architecture="x86_64",
        )

        selector = LegacyAgentSelector([
            "custom.resource-name_123",
            "another/special@resource",
            "cpu",
            "mem",
        ])
        # Convert agents to trackers
        trackers = [AgentStateTracker(original_agent=agent) for agent in agents]
        result = selector.select_tracker_by_strategy(trackers, resource_req, criteria, config)

        # Should handle special resource names correctly
        assert result.original_agent.agent_id == AgentId("special")
