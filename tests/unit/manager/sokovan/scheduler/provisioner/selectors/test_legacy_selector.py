"""Test legacy agent selector implementation."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from ai.backend.common.types import AgentId, ClusterMode, ResourceSlot, SessionId, SessionTypes
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.legacy import LegacyAgentSelector
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentInfo,
    AgentSelectionConfig,
    AgentSelectionCriteria,
    AgentStateTracker,
    ResourceRequirements,
    SessionMetadata,
)


class TestLegacyAgentSelector:
    """Test legacy agent selector behavior."""

    @pytest.fixture
    def selector(self) -> LegacyAgentSelector:
        """Create a legacy selector with default priority."""
        return LegacyAgentSelector(agent_selection_resource_priority=["cpu", "mem"])

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

    def test_prefers_fewer_unutilized_capabilities_first(
        self,
        selector: LegacyAgentSelector,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        agents_for_unutilized_capability_test: list[AgentInfo],
    ) -> None:
        """Test that legacy selector prioritizes fewer unutilized capabilities."""
        # Request only CPU and memory (explicitly no GPU/TPU)
        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({
                "cpu": Decimal("2"),
                "mem": Decimal("4096"),
                "cuda.shares": Decimal("0"),  # Explicitly not needed
                "tpu": Decimal("0"),  # Explicitly not needed
            }),
            required_architecture="x86_64",
        )

        trackers = [
            AgentStateTracker(original_agent=agent)
            for agent in agents_for_unutilized_capability_test
        ]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )

        # Should select agent-minimal (0 unutilized capabilities vs 2)
        assert selected.original_agent.agent_id == AgentId("agent-minimal")

    def test_breaks_ties_with_resource_availability(
        self,
        selector: LegacyAgentSelector,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        agents_for_resource_tie_breaking: list[AgentInfo],
    ) -> None:
        """Test that ties in unutilized capabilities are broken by resource availability."""
        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            required_architecture="x86_64",
        )

        # Both have 0 unutilized capabilities
        # Available resources:
        # agent-low-resources: 2 CPU, 4096 memory
        # agent-high-resources: 12 CPU, 24576 memory

        trackers = [
            AgentStateTracker(original_agent=agent) for agent in agents_for_resource_tie_breaking
        ]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )

        # Should select agent-high-resources (more available resources)
        assert selected.original_agent.agent_id == AgentId("agent-high-resources")

    def test_respects_resource_priority_order(
        self,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        agents_for_memory_priority: list[AgentInfo],
    ) -> None:
        """Test that resource priorities are used for tie-breaking."""
        # Create selector with memory prioritized over CPU
        selector = LegacyAgentSelector(agent_selection_resource_priority=["mem", "cpu"])

        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
            required_architecture="x86_64",
        )

        # Both have same unutilized capabilities (0)
        # Available resources:
        # low-mem-high-cpu: 14 CPU, 2048 memory
        # high-mem-low-cpu: 2 CPU, 12288 memory

        trackers = [AgentStateTracker(original_agent=agent) for agent in agents_for_memory_priority]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )

        # Should select high-mem-low-cpu (more memory, which is higher priority)
        assert selected.original_agent.agent_id == AgentId("high-mem-low-cpu")

    def test_handles_partially_utilized_resources(
        self,
        selector: LegacyAgentSelector,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        agents_gpu_partially_used: list[AgentInfo],
    ) -> None:
        """Test selection when agents have partially utilized special resources."""
        # Request includes GPU
        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({
                "cpu": Decimal("2"),
                "mem": Decimal("4096"),
                "cuda.shares": Decimal("1"),
            }),
            required_architecture="x86_64",
        )

        trackers = [AgentStateTracker(original_agent=agent) for agent in agents_gpu_partially_used]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )

        # Both have same unutilized capabilities (0 - all resources are requested)
        # Both have same available CPU and memory
        # They should be equivalent choices
        assert selected.original_agent.agent_id in [
            AgentId("gpu-partially-used"),
            AgentId("gpu-unused"),
        ]

    def test_legacy_behavior_differs_from_concentrated_and_dispersed(
        self,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        agents_specialized_vs_general: list[AgentInfo],
    ) -> None:
        """Test that legacy selector has distinct behavior from other strategies."""
        from ai.backend.manager.sokovan.scheduler.provisioner.selectors.concentrated import (
            ConcentratedAgentSelector,
        )
        from ai.backend.manager.sokovan.scheduler.provisioner.selectors.dispersed import (
            DispersedAgentSelector,
        )

        legacy = LegacyAgentSelector(agent_selection_resource_priority=["cpu", "mem"])
        concentrated = ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])
        dispersed = DispersedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])

        # Request only CPU and memory
        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            required_architecture="x86_64",
        )

        trackers = [
            AgentStateTracker(original_agent=agent) for agent in agents_specialized_vs_general
        ]

        legacy_choice = legacy.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )
        concentrated_choice = concentrated.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )
        dispersed_choice = dispersed.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )

        # Legacy should choose agent-general (fewer unutilized capabilities)
        assert legacy_choice.original_agent.agent_id == AgentId("agent-general")
        # Concentrated should choose agent-specialized (less available resources)
        assert concentrated_choice.original_agent.agent_id == AgentId("agent-specialized")
        # Dispersed should choose agent-general (more available resources AND fewer unutilized)
        assert dispersed_choice.original_agent.agent_id == AgentId("agent-general")

    def test_handles_custom_resource_types(
        self,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        agents_with_custom_accelerator: list[AgentInfo],
    ) -> None:
        """Test selection with custom resource types in priority."""
        selector = LegacyAgentSelector(
            agent_selection_resource_priority=["custom.accelerator", "cpu", "mem"]
        )

        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({
                "cpu": Decimal("2"),
                "mem": Decimal("4096"),
                "custom.accelerator": Decimal("1"),
            }),
            required_architecture="x86_64",
        )

        # Available resources:
        # custom-rich: 4 CPU, 8192 memory, 8 custom.accelerator
        # custom-poor: 12 CPU, 24576 memory, 1 custom.accelerator

        trackers = [
            AgentStateTracker(original_agent=agent) for agent in agents_with_custom_accelerator
        ]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )

        # Should select custom-rich (more custom.accelerator, which is highest priority)
        assert selected.original_agent.agent_id == AgentId("custom-rich")
