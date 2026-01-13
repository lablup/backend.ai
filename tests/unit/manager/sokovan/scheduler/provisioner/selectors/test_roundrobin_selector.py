"""Test round-robin agent selector implementation."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from ai.backend.common.types import AgentId, ClusterMode, ResourceSlot, SessionId, SessionTypes
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


class TestRoundRobinAgentSelector:
    """Test round-robin agent selector behavior."""

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

    @pytest.fixture
    def resource_req(self) -> ResourceRequirements:
        """Create basic resource requirements."""
        return ResourceRequirements(
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            required_architecture="x86_64",
            kernel_ids=[uuid.uuid4()],
        )

    def test_sequential_selection(
        self,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        resource_req: ResourceRequirements,
        agents_for_roundrobin_sequential: list[AgentInfo],
    ) -> None:
        """Test that round-robin selects agents sequentially."""
        selector = RoundRobinAgentSelector(next_index=0)

        # First selection
        trackers = [
            AgentStateTracker(original_agent=agent) for agent in agents_for_roundrobin_sequential
        ]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )
        assert selected.original_agent.agent_id == AgentId("agent-a")

        # Update index manually (in real usage, caller tracks this)
        selector.next_index = 1
        trackers = [
            AgentStateTracker(original_agent=agent) for agent in agents_for_roundrobin_sequential
        ]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )
        assert selected.original_agent.agent_id == AgentId("agent-b")

        selector.next_index = 2
        trackers = [
            AgentStateTracker(original_agent=agent) for agent in agents_for_roundrobin_sequential
        ]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )
        assert selected.original_agent.agent_id == AgentId("agent-c")

    def test_index_wrapping(
        self,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        resource_req: ResourceRequirements,
        agents_for_roundrobin_sequential: list[AgentInfo],
    ) -> None:
        """Test that index wraps around when exceeding agent count."""
        # Test with index equal to agent count
        selector = RoundRobinAgentSelector(next_index=3)
        trackers = [
            AgentStateTracker(original_agent=agent) for agent in agents_for_roundrobin_sequential
        ]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )
        assert selected.original_agent.agent_id == AgentId("agent-a")  # Wraps to index 0

        # Test with index greater than agent count
        selector = RoundRobinAgentSelector(next_index=7)
        trackers = [
            AgentStateTracker(original_agent=agent) for agent in agents_for_roundrobin_sequential
        ]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )
        assert selected.original_agent.agent_id == AgentId("agent-b")  # 7 % 3 = 1

    def test_consistent_ordering_by_agent_id(
        self,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        resource_req: ResourceRequirements,
        agents_for_roundrobin_unsorted: list[AgentInfo],
    ) -> None:
        """Test that agents are consistently ordered by ID."""
        selector = RoundRobinAgentSelector(next_index=0)

        # Should select based on sorted order: alpha, beta, zebra
        trackers = [
            AgentStateTracker(original_agent=agent) for agent in agents_for_roundrobin_unsorted
        ]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )
        assert selected.original_agent.agent_id == AgentId("alpha")

        selector.next_index = 1
        trackers = [
            AgentStateTracker(original_agent=agent) for agent in agents_for_roundrobin_unsorted
        ]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )
        assert selected.original_agent.agent_id == AgentId("beta")

        selector.next_index = 2
        trackers = [
            AgentStateTracker(original_agent=agent) for agent in agents_for_roundrobin_unsorted
        ]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )
        assert selected.original_agent.agent_id == AgentId("zebra")

    def test_single_agent(
        self,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        resource_req: ResourceRequirements,
        single_agent: list[AgentInfo],
    ) -> None:
        """Test round-robin with single agent."""
        # Any index should select the only agent
        for index in [0, 1, 5, 100]:
            selector = RoundRobinAgentSelector(next_index=index)
            trackers = [AgentStateTracker(original_agent=agent) for agent in single_agent]

            selected = selector.select_tracker_by_strategy(
                trackers, resource_req, basic_criteria, basic_config
            )
            assert selected.original_agent.agent_id == AgentId("lonely-agent")

    def test_ignores_resource_availability(
        self,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        resource_req: ResourceRequirements,
        agents_for_roundrobin_varied_resources: list[AgentInfo],
    ) -> None:
        """Test that round-robin ignores resource availability (just uses index)."""
        selector = RoundRobinAgentSelector(next_index=0)

        # Should select agent-empty even though it has less resources
        trackers = [
            AgentStateTracker(original_agent=agent)
            for agent in agents_for_roundrobin_varied_resources
        ]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )
        assert selected.original_agent.agent_id == AgentId("agent-empty")

    def test_deterministic_selection(
        self,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        resource_req: ResourceRequirements,
        agents_for_roundrobin_large_scale: list[AgentInfo],
    ) -> None:
        """Test that selection is deterministic for same index and agents."""
        selector = RoundRobinAgentSelector(next_index=5)

        # Run multiple times - should always select the same agent
        results = []
        for _ in range(10):
            trackers = [
                AgentStateTracker(original_agent=agent)
                for agent in agents_for_roundrobin_large_scale
            ]

            selected = selector.select_tracker_by_strategy(
                trackers, resource_req, basic_criteria, basic_config
            )
            results.append(selected)

        # All selections should be identical
        assert all(r == results[0] for r in results)
        assert results[0].original_agent.agent_id == AgentId("agent-5")

    def test_handles_non_sequential_agent_ids(
        self,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        resource_req: ResourceRequirements,
        agents_for_roundrobin_non_sequential_ids: list[AgentInfo],
    ) -> None:
        """Test round-robin with non-sequential agent IDs."""
        selector = RoundRobinAgentSelector(next_index=0)

        # Should order by agent ID lexicographically: agent-100, agent-42, agent-5
        trackers = [
            AgentStateTracker(original_agent=agent)
            for agent in agents_for_roundrobin_non_sequential_ids
        ]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )
        assert selected.original_agent.agent_id == AgentId("agent-100")

        selector.next_index = 1
        trackers = [
            AgentStateTracker(original_agent=agent)
            for agent in agents_for_roundrobin_non_sequential_ids
        ]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )
        assert selected.original_agent.agent_id == AgentId("agent-42")

        selector.next_index = 2
        trackers = [
            AgentStateTracker(original_agent=agent)
            for agent in agents_for_roundrobin_non_sequential_ids
        ]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )
        assert selected.original_agent.agent_id == AgentId("agent-5")

    def test_fairness_over_multiple_selections(
        self,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
        resource_req: ResourceRequirements,
        agents_for_roundrobin_fairness: list[AgentInfo],
    ) -> None:
        """Test that round-robin provides fair distribution over time."""
        # Track selections for each agent
        selection_count = {f"agent-{i}": 0 for i in range(5)}

        # Make 50 selections (10 complete rounds)
        selector = RoundRobinAgentSelector(next_index=0)
        for i in range(50):
            selector.next_index = i
            trackers = [
                AgentStateTracker(original_agent=agent) for agent in agents_for_roundrobin_fairness
            ]

            selected = selector.select_tracker_by_strategy(
                trackers, resource_req, basic_criteria, basic_config
            )
            selection_count[selected.original_agent.agent_id] += 1

        # Each agent should be selected exactly 10 times
        assert all(count == 10 for count in selection_count.values())
