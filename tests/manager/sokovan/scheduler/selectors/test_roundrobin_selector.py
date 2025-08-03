"""Test round-robin agent selector implementation."""

import uuid
from decimal import Decimal

import pytest

from ai.backend.common.types import AgentId, ClusterMode, ResourceSlot, SessionId, SessionTypes
from ai.backend.manager.sokovan.scheduler.selectors.roundrobin import RoundRobinAgentSelector
from ai.backend.manager.sokovan.scheduler.selectors.selector import (
    AgentSelectionConfig,
    AgentSelectionCriteria,
    ResourceRequirements,
    SessionMetadata,
)

from .conftest import create_agent_info


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

    def test_sequential_selection(self, basic_criteria, basic_config, resource_req):
        """Test that round-robin selects agents sequentially."""
        selector = RoundRobinAgentSelector(next_index=0)

        agents = [
            create_agent_info(agent_id="agent-a"),
            create_agent_info(agent_id="agent-b"),
            create_agent_info(agent_id="agent-c"),
        ]

        # First selection
        selected = selector.select_agent_by_strategy(
            agents, resource_req, basic_criteria, basic_config
        )
        assert selected.agent_id == AgentId("agent-a")

        # Update index manually (in real usage, caller tracks this)
        selector.next_index = 1
        selected = selector.select_agent_by_strategy(
            agents, resource_req, basic_criteria, basic_config
        )
        assert selected.agent_id == AgentId("agent-b")

        selector.next_index = 2
        selected = selector.select_agent_by_strategy(
            agents, resource_req, basic_criteria, basic_config
        )
        assert selected.agent_id == AgentId("agent-c")

    def test_index_wrapping(self, basic_criteria, basic_config, resource_req):
        """Test that index wraps around when exceeding agent count."""
        agents = [
            create_agent_info(agent_id="agent-1"),
            create_agent_info(agent_id="agent-2"),
            create_agent_info(agent_id="agent-3"),
        ]

        # Test with index equal to agent count
        selector = RoundRobinAgentSelector(next_index=3)
        selected = selector.select_agent_by_strategy(
            agents, resource_req, basic_criteria, basic_config
        )
        assert selected.agent_id == AgentId("agent-1")  # Wraps to index 0

        # Test with index greater than agent count
        selector = RoundRobinAgentSelector(next_index=7)
        selected = selector.select_agent_by_strategy(
            agents, resource_req, basic_criteria, basic_config
        )
        assert selected.agent_id == AgentId("agent-2")  # 7 % 3 = 1

    def test_consistent_ordering_by_agent_id(self, basic_criteria, basic_config, resource_req):
        """Test that agents are consistently ordered by ID."""
        # Create agents in non-alphabetical order
        agents = [
            create_agent_info(agent_id="zebra"),
            create_agent_info(agent_id="alpha"),
            create_agent_info(agent_id="beta"),
        ]

        selector = RoundRobinAgentSelector(next_index=0)

        # Should select based on sorted order: alpha, beta, zebra
        selected = selector.select_agent_by_strategy(
            agents, resource_req, basic_criteria, basic_config
        )
        assert selected.agent_id == AgentId("alpha")

        selector.next_index = 1
        selected = selector.select_agent_by_strategy(
            agents, resource_req, basic_criteria, basic_config
        )
        assert selected.agent_id == AgentId("beta")

        selector.next_index = 2
        selected = selector.select_agent_by_strategy(
            agents, resource_req, basic_criteria, basic_config
        )
        assert selected.agent_id == AgentId("zebra")

    def test_single_agent(self, basic_criteria, basic_config, resource_req):
        """Test round-robin with single agent."""
        agents = [create_agent_info(agent_id="lonely-agent")]

        # Any index should select the only agent
        for index in [0, 1, 5, 100]:
            selector = RoundRobinAgentSelector(next_index=index)
            selected = selector.select_agent_by_strategy(
                agents, resource_req, basic_criteria, basic_config
            )
            assert selected.agent_id == AgentId("lonely-agent")

    def test_ignores_resource_availability(self, basic_criteria, basic_config, resource_req):
        """Test that round-robin ignores resource availability (just uses index)."""
        agents = [
            create_agent_info(
                agent_id="agent-empty",
                available_slots={"cpu": Decimal("1"), "mem": Decimal("1024")},
                occupied_slots={"cpu": Decimal("0.9"), "mem": Decimal("1000")},
            ),
            create_agent_info(
                agent_id="agent-full",
                available_slots={"cpu": Decimal("100"), "mem": Decimal("204800")},
                occupied_slots={"cpu": Decimal("1"), "mem": Decimal("2048")},
            ),
        ]

        selector = RoundRobinAgentSelector(next_index=0)

        # Should select agent-empty even though it has less resources
        selected = selector.select_agent_by_strategy(
            agents, resource_req, basic_criteria, basic_config
        )
        assert selected.agent_id == AgentId("agent-empty")

    def test_deterministic_selection(self, basic_criteria, basic_config, resource_req):
        """Test that selection is deterministic for same index and agents."""
        agents = [create_agent_info(agent_id=f"agent-{i}") for i in range(10)]

        selector = RoundRobinAgentSelector(next_index=5)

        # Run multiple times - should always select the same agent
        results = []
        for _ in range(10):
            selected = selector.select_agent_by_strategy(
                agents, resource_req, basic_criteria, basic_config
            )
            results.append(selected)

        # All selections should be identical
        assert all(r == results[0] for r in results)
        assert results[0].agent_id == AgentId("agent-5")

    def test_handles_non_sequential_agent_ids(self, basic_criteria, basic_config, resource_req):
        """Test round-robin with non-sequential agent IDs."""
        agents = [
            create_agent_info(agent_id="agent-100"),
            create_agent_info(agent_id="agent-5"),
            create_agent_info(agent_id="agent-42"),
        ]

        selector = RoundRobinAgentSelector(next_index=0)

        # Should order by agent ID: agent-100, agent-42, agent-5
        # But lexicographic ordering puts: agent-100, agent-42, agent-5
        selected = selector.select_agent_by_strategy(
            agents, resource_req, basic_criteria, basic_config
        )
        assert selected.agent_id == AgentId("agent-100")

        selector.next_index = 1
        selected = selector.select_agent_by_strategy(
            agents, resource_req, basic_criteria, basic_config
        )
        assert selected.agent_id == AgentId("agent-42")

        selector.next_index = 2
        selected = selector.select_agent_by_strategy(
            agents, resource_req, basic_criteria, basic_config
        )
        assert selected.agent_id == AgentId("agent-5")

    def test_fairness_over_multiple_selections(self, basic_criteria, basic_config, resource_req):
        """Test that round-robin provides fair distribution over time."""
        agents = [create_agent_info(agent_id=f"agent-{i}") for i in range(5)]

        # Track selections for each agent
        selection_count = {f"agent-{i}": 0 for i in range(5)}

        # Make 50 selections (10 complete rounds)
        selector = RoundRobinAgentSelector(next_index=0)
        for i in range(50):
            selector.next_index = i
            selected = selector.select_agent_by_strategy(
                agents, resource_req, basic_criteria, basic_config
            )
            selection_count[selected.agent_id] += 1

        # Each agent should be selected exactly 10 times
        assert all(count == 10 for count in selection_count.values())
