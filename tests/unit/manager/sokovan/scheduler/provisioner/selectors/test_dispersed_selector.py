"""Test dispersed agent selector implementation."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from ai.backend.common.types import AgentId, ClusterMode, ResourceSlot, SessionId, SessionTypes
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.dispersed import (
    DispersedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentInfo,
    AgentSelectionConfig,
    AgentSelectionCriteria,
    AgentStateTracker,
    ResourceRequirements,
    SessionMetadata,
)


class TestDispersedAgentSelector:
    """Test dispersed agent selector behavior."""

    @pytest.fixture
    def selector(self) -> DispersedAgentSelector:
        """Create a dispersed selector with default priority."""
        return DispersedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])

    @pytest.fixture
    def basic_criteria(self) -> AgentSelectionCriteria:
        """Create basic selection criteria."""
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
    def basic_config(self) -> AgentSelectionConfig:
        """Create basic selection config."""
        return AgentSelectionConfig(
            max_container_count=None,
            enforce_spreading_endpoint_replica=False,
        )

    def test_selects_agent_with_most_resources(
        self,
        selector: DispersedAgentSelector,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        agents_with_varied_occupancy: list[AgentInfo],
    ) -> None:
        """Test that dispersed selector prefers agents with more available resources."""
        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            required_architecture="x86_64",
        )

        # Available resources:
        # agent-low: 2 CPU, 4096 memory
        # agent-medium: 4 CPU, 8192 memory
        # agent-high: 6 CPU, 12288 memory

        trackers = [
            AgentStateTracker(original_agent=agent) for agent in agents_with_varied_occupancy
        ]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )

        # Should select agent-high (most available resources)
        assert selected.original_agent.agent_id == AgentId("agent-high")

    def test_prefers_fewer_unutilized_capabilities(
        self,
        selector: DispersedAgentSelector,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        agents_dispersed_gpu_vs_cpu: list[AgentInfo],
    ) -> None:
        """Test preference for agents with fewer unutilized resource types."""
        # Request only CPU and memory (explicitly no GPU)
        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({
                "cpu": Decimal("2"),
                "mem": Decimal("4096"),
                "cuda.shares": Decimal("0"),  # Explicitly not needed
            }),
            required_architecture="x86_64",
        )

        trackers = [
            AgentStateTracker(original_agent=agent) for agent in agents_dispersed_gpu_vs_cpu
        ]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )

        # Should select agent-cpu-only (no unutilized GPU capability)
        # even though both have same available CPU/mem
        assert selected.original_agent.agent_id == AgentId("agent-cpu-only")

    def test_respects_resource_priority_order(
        self,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        agents_for_memory_priority: list[AgentInfo],
    ) -> None:
        """Test that resource priorities are respected in order."""
        # Create selector with memory prioritized over CPU
        selector = DispersedAgentSelector(agent_selection_resource_priority=["mem", "cpu"])

        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
            required_architecture="x86_64",
        )

        # Available resources:
        # low-mem-high-cpu: 14 CPU, 2048 memory
        # high-mem-low-cpu: 2 CPU, 12288 memory

        trackers = [AgentStateTracker(original_agent=agent) for agent in agents_for_memory_priority]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )

        # Should select high-mem-low-cpu (more memory available, which is higher priority)
        assert selected.original_agent.agent_id == AgentId("high-mem-low-cpu")

    def test_handles_agents_with_no_available_slots(
        self,
        selector: DispersedAgentSelector,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        agents_full_vs_available: list[AgentInfo],
    ) -> None:
        """Test behavior when some agents have zero available resources."""
        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            required_architecture="x86_64",
        )

        # agent-full has 0 available resources
        # agent-available has 4 CPU, 8192 memory

        trackers = [AgentStateTracker(original_agent=agent) for agent in agents_full_vs_available]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )

        # Should select agent-available
        assert selected.original_agent.agent_id == AgentId("agent-available")

    def test_tie_breaking_with_identical_resources(
        self,
        selector: DispersedAgentSelector,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        agents_with_identical_resources: list[AgentInfo],
    ) -> None:
        """Test consistent tie-breaking when agents have identical resources."""
        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            required_architecture="x86_64",
        )

        # All agents have identical resources
        trackers = [
            AgentStateTracker(original_agent=agent) for agent in agents_with_identical_resources
        ]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )

        # Should consistently select the same agent
        assert selected.original_agent.agent_id in [
            AgentId("agent-a"),
            AgentId("agent-b"),
            AgentId("agent-c"),
        ]

        # Run multiple times to ensure consistency
        for _ in range(10):
            result = selector.select_tracker_by_strategy(
                trackers, resource_req, basic_criteria, basic_config
            )
            assert result == selected

    def test_handles_mixed_resource_types(
        self,
        selector: DispersedAgentSelector,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        agents_mixed_resource_types: list[AgentInfo],
    ) -> None:
        """Test selection with heterogeneous resource types."""
        # Request only CPU and memory
        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("4"), "mem": Decimal("8192")}),
            required_architecture="x86_64",
        )

        # Available resources:
        # gpu-agent: 8 CPU, 16384 memory (has unutilized GPU)
        # tpu-agent: 12 CPU, 24576 memory (has unutilized TPU)
        # cpu-agent: 16 CPU, 32768 memory (no unutilized resources)

        trackers = [
            AgentStateTracker(original_agent=agent) for agent in agents_mixed_resource_types
        ]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )

        # Should select cpu-agent (no unutilized capabilities and most resources)
        assert selected.original_agent.agent_id == AgentId("cpu-agent")

    def test_dispersed_opposite_of_concentrated(
        self,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        agents_concentrated_vs_dispersed: list[AgentInfo],
    ) -> None:
        """Test that dispersed selector makes opposite choices from concentrated."""
        from ai.backend.manager.sokovan.scheduler.provisioner.selectors.concentrated import (
            ConcentratedAgentSelector,
        )

        dispersed = DispersedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])
        concentrated = ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])

        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("0.5"), "mem": Decimal("1024")}),
            required_architecture="x86_64",
        )

        # Convert agents to trackers for dispersed
        trackers = [
            AgentStateTracker(original_agent=agent) for agent in agents_concentrated_vs_dispersed
        ]
        dispersed_choice = dispersed.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )
        concentrated_choice = concentrated.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )

        # Dispersed should choose agent-2 (more available)
        # Concentrated should choose agent-1 (less available)
        assert dispersed_choice.original_agent.agent_id == AgentId("agent-2")
        assert concentrated_choice.original_agent.agent_id == AgentId("agent-1")
        assert (
            dispersed_choice.original_agent.agent_id != concentrated_choice.original_agent.agent_id
        )
