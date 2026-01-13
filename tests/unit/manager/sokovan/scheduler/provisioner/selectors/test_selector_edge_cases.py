"""Edge case tests for agent selectors."""

from __future__ import annotations

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
    AgentInfo,
    AgentSelectionConfig,
    AgentSelectionCriteria,
    AgentStateTracker,
    ResourceRequirements,
    SessionMetadata,
)


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

    def test_empty_resource_requirements(
        self,
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
        agents_for_edge_case_empty_request: list[AgentInfo],
    ) -> None:
        """Test handling of empty resource requirements."""
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
            trackers = [
                AgentStateTracker(original_agent=agent)
                for agent in agents_for_edge_case_empty_request
            ]
            result = selector.select_tracker_by_strategy(trackers, resource_req, criteria, config)
            assert result is not None
            assert result.original_agent.agent_id in [AgentId("agent-1"), AgentId("agent-2")]

    def test_zero_resource_values(
        self,
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
        single_agent: list[AgentInfo],
    ) -> None:
        """Test handling of zero resource values in requests."""
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
        trackers = [AgentStateTracker(original_agent=agent) for agent in single_agent]
        result = selector.select_tracker_by_strategy(trackers, resource_req, criteria, config)

        # Should still select an agent
        assert result.original_agent.agent_id == AgentId("lonely-agent")

    def test_missing_resource_types_in_request(
        self,
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
        agents_cpu_only_vs_gpu: list[AgentInfo],
    ) -> None:
        """Test when requested resource type doesn't exist on any agent."""
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
        trackers = [AgentStateTracker(original_agent=agent) for agent in agents_cpu_only_vs_gpu]
        result = selector.select_tracker_by_strategy(trackers, resource_req, criteria, config)
        assert result is not None

    def test_extremely_large_resource_values(
        self,
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
        agents_normal_vs_huge: list[AgentInfo],
    ) -> None:
        """Test handling of very large resource values."""
        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            required_architecture="x86_64",
        )

        # Test with different selectors
        concentrated = ConcentratedAgentSelector(["cpu", "mem"])
        dispersed = DispersedAgentSelector(["cpu", "mem"])

        trackers = [AgentStateTracker(original_agent=agent) for agent in agents_normal_vs_huge]
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

    def test_decimal_precision_edge_cases(
        self,
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
        agents_decimal_precision: list[AgentInfo],
    ) -> None:
        """Test handling of decimal precision edge cases."""
        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({
                "cpu": Decimal("0.000000000000000000000001"),
                "mem": Decimal("0.000000000000000000000001"),
            }),
            required_architecture="x86_64",
        )

        selector = ConcentratedAgentSelector(["cpu", "mem"])
        trackers = [AgentStateTracker(original_agent=agent) for agent in agents_decimal_precision]
        result = selector.select_tracker_by_strategy(trackers, resource_req, criteria, config)

        # Should handle decimal precision correctly
        assert result.original_agent.agent_id in [AgentId("agent-1"), AgentId("agent-2")]

    def test_single_agent_all_strategies(
        self,
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
        single_agent: list[AgentInfo],
    ) -> None:
        """Test all strategies with only one agent available."""
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
            trackers = [AgentStateTracker(original_agent=agent) for agent in single_agent]
            result = selector.select_tracker_by_strategy(trackers, resource_req, criteria, config)
            assert result.original_agent.agent_id == AgentId("lonely-agent")

    def test_all_agents_fully_occupied(
        self,
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
        agents_all_fully_occupied: list[AgentInfo],
    ) -> None:
        """Test when all agents have zero available resources."""
        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            required_architecture="x86_64",
        )

        # Selectors will still pick an agent (filtering happens in wrapper)
        selector = ConcentratedAgentSelector(["cpu", "mem"])
        trackers = [AgentStateTracker(original_agent=agent) for agent in agents_all_fully_occupied]
        result = selector.select_tracker_by_strategy(trackers, resource_req, criteria, config)

        # Should still return an agent (they're all equal)
        assert result.original_agent.agent_id in [AgentId(f"full-{i}") for i in range(3)]

    def test_priority_with_nonexistent_resources(
        self,
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
        agents_with_varied_occupancy: list[AgentInfo],
    ) -> None:
        """Test resource priority list containing non-existent resource types."""
        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            required_architecture="x86_64",
        )

        # Priority includes non-existent resources
        selector = ConcentratedAgentSelector(["quantum.bits", "neural.cores", "cpu", "mem"])
        trackers = [
            AgentStateTracker(original_agent=agent) for agent in agents_with_varied_occupancy
        ]
        result = selector.select_tracker_by_strategy(trackers, resource_req, criteria, config)

        # Should ignore non-existent resources and use cpu/mem
        assert result.original_agent.agent_id == AgentId("agent-low")  # Less available resources

    def test_special_resource_names(
        self,
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
        agents_with_special_resource_names: list[AgentInfo],
    ) -> None:
        """Test handling of special characters in resource names."""
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
        trackers = [
            AgentStateTracker(original_agent=agent) for agent in agents_with_special_resource_names
        ]
        result = selector.select_tracker_by_strategy(trackers, resource_req, criteria, config)

        # Should handle special resource names correctly
        assert result.original_agent.agent_id == AgentId("special")
