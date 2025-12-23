"""Test concentrated agent selector implementation."""

import uuid
from decimal import Decimal

import pytest

from ai.backend.common.types import AgentId, ClusterMode, ResourceSlot, SessionId, SessionTypes
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.concentrated import (
    ConcentratedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentSelectionConfig,
    AgentSelectionCriteria,
    AgentStateTracker,
    ResourceRequirements,
    SessionMetadata,
)

from .conftest import create_agent_info


class TestConcentratedAgentSelector:
    """Test concentrated agent selector behavior."""

    @pytest.fixture
    def selector(self) -> ConcentratedAgentSelector:
        """Create a concentrated selector with default priority."""
        return ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])

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

    def test_selects_agent_with_least_resources(
        self,
        selector: ConcentratedAgentSelector,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
    ) -> None:
        """Test that concentrated selector prefers agents with less available resources."""
        agents = [
            create_agent_info(
                agent_id="agent-low",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("6"), "mem": Decimal("12288")},
            ),
            create_agent_info(
                agent_id="agent-medium",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
            ),
            create_agent_info(
                agent_id="agent-high",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
            ),
        ]

        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            required_architecture="x86_64",
        )

        # Available resources:
        # agent-low: 2 CPU, 4096 memory
        # agent-medium: 4 CPU, 8192 memory
        # agent-high: 6 CPU, 12288 memory

        # Convert agents to trackers
        trackers = [AgentStateTracker(original_agent=agent) for agent in agents]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )

        # Should select agent-low (least available resources)
        assert selected.original_agent.agent_id == AgentId("agent-low")

    def test_prefers_fewer_unutilized_capabilities(
        self,
        selector: ConcentratedAgentSelector,
        basic_criteria: AgentSelectionCriteria,
        basic_config: AgentSelectionConfig,
    ) -> None:
        """Test preference for agents with fewer unutilized resource types."""
        agents = [
            create_agent_info(
                agent_id="agent-gpu",
                available_slots={
                    "cpu": Decimal("8"),
                    "mem": Decimal("16384"),
                    "cuda.shares": Decimal("4"),
                },
                occupied_slots={
                    "cpu": Decimal("4"),
                    "mem": Decimal("8192"),
                    "cuda.shares": Decimal("0"),
                },
            ),
            create_agent_info(
                agent_id="agent-cpu-only",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
            ),
        ]

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

        # Convert agents to trackers
        trackers = [AgentStateTracker(original_agent=agent) for agent in agents]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )

        # Should select agent-cpu-only (no unutilized GPU capability)
        assert selected.original_agent.agent_id == AgentId("agent-cpu-only")

    def test_respects_resource_priority_order(
        self, basic_criteria: AgentSelectionCriteria, basic_config: AgentSelectionConfig
    ) -> None:
        """Test that resource priorities are respected in order."""
        # Create selector with memory prioritized over CPU
        selector = ConcentratedAgentSelector(agent_selection_resource_priority=["mem", "cpu"])

        agents = [
            create_agent_info(
                agent_id="low-mem-high-cpu",
                available_slots={"cpu": Decimal("16"), "mem": Decimal("8192")},
                occupied_slots={"cpu": Decimal("2"), "mem": Decimal("6144")},
            ),
            create_agent_info(
                agent_id="high-mem-low-cpu",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("6"), "mem": Decimal("4096")},
            ),
        ]

        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
            required_architecture="x86_64",
        )

        # Available resources:
        # low-mem-high-cpu: 14 CPU, 2048 memory
        # high-mem-low-cpu: 2 CPU, 12288 memory

        # Convert agents to trackers
        trackers = [AgentStateTracker(original_agent=agent) for agent in agents]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )

        # Should select low-mem-high-cpu (less memory available, which is higher priority)
        assert selected.original_agent.agent_id == AgentId("low-mem-high-cpu")

    def test_endpoint_replica_spreading_for_inference(self, selector):
        """Test special behavior for inference sessions with endpoint replica spreading."""
        # Create inference session criteria
        criteria = AgentSelectionCriteria(
            session_metadata=SessionMetadata(
                session_id=SessionId(uuid.uuid4()),
                session_type=SessionTypes.INFERENCE,
                scaling_group="default",
                cluster_mode=ClusterMode.SINGLE_NODE,
            ),
            kernel_requirements={},
            kernel_counts_at_endpoint={
                AgentId("agent-1"): 5,  # Already has 5 kernels
                AgentId("agent-2"): 2,  # Has 2 kernels
                AgentId("agent-3"): 0,  # No kernels
            },
        )

        config = AgentSelectionConfig(
            max_container_count=None,
            enforce_spreading_endpoint_replica=True,
        )

        agents = [
            create_agent_info(
                agent_id="agent-1",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
            ),
            create_agent_info(
                agent_id="agent-2",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
            ),
            create_agent_info(
                agent_id="agent-3",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
            ),
        ]

        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            required_architecture="x86_64",
        )

        # Convert agents to trackers
        trackers = [AgentStateTracker(original_agent=agent) for agent in agents]

        selected = selector.select_tracker_by_strategy(trackers, resource_req, criteria, config)

        # Should select agent-3 (fewest kernels at endpoint)
        assert selected.original_agent.agent_id == AgentId("agent-3")

    def test_tie_breaking_with_identical_resources(self, selector, basic_criteria, basic_config):
        """Test consistent tie-breaking when agents have identical resources."""
        agents = [
            create_agent_info(
                agent_id="agent-b",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
            ),
            create_agent_info(
                agent_id="agent-a",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
            ),
            create_agent_info(
                agent_id="agent-c",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("4"), "mem": Decimal("8192")},
            ),
        ]

        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            required_architecture="x86_64",
        )

        # Convert agents to trackers
        trackers = [AgentStateTracker(original_agent=agent) for agent in agents]

        # All agents have identical resources
        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )

        # Should consistently select the same agent (first in min comparison)
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

    def test_handles_agents_with_gpu_resources(self, selector, basic_criteria, basic_config):
        """Test selection with GPU resources."""
        agents = [
            create_agent_info(
                agent_id="gpu-busy",
                available_slots={
                    "cpu": Decimal("16"),
                    "mem": Decimal("32768"),
                    "cuda.shares": Decimal("8"),
                },
                occupied_slots={
                    "cpu": Decimal("8"),
                    "mem": Decimal("16384"),
                    "cuda.shares": Decimal("6"),
                },
            ),
            create_agent_info(
                agent_id="gpu-free",
                available_slots={
                    "cpu": Decimal("16"),
                    "mem": Decimal("32768"),
                    "cuda.shares": Decimal("8"),
                },
                occupied_slots={
                    "cpu": Decimal("4"),
                    "mem": Decimal("8192"),
                    "cuda.shares": Decimal("2"),
                },
            ),
        ]

        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({
                "cpu": Decimal("2"),
                "mem": Decimal("4096"),
                "cuda.shares": Decimal("1"),
            }),
            required_architecture="x86_64",
        )

        # Available resources:
        # gpu-busy: 8 CPU, 16384 memory, 2 GPU
        # gpu-free: 12 CPU, 24576 memory, 6 GPU

        # Convert agents to trackers
        trackers = [AgentStateTracker(original_agent=agent) for agent in agents]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )

        # Should select gpu-busy (less available resources)
        assert selected.original_agent.agent_id == AgentId("gpu-busy")

    def test_custom_resource_priority(self, basic_criteria, basic_config):
        """Test with custom resource priorities including GPU."""
        selector = ConcentratedAgentSelector(
            agent_selection_resource_priority=["cuda.shares", "cpu", "mem"]
        )

        agents = [
            create_agent_info(
                agent_id="low-gpu",
                available_slots={
                    "cpu": Decimal("16"),
                    "mem": Decimal("32768"),
                    "cuda.shares": Decimal("4"),
                },
                occupied_slots={
                    "cpu": Decimal("2"),
                    "mem": Decimal("4096"),
                    "cuda.shares": Decimal("3"),
                },
            ),
            create_agent_info(
                agent_id="high-gpu",
                available_slots={
                    "cpu": Decimal("8"),
                    "mem": Decimal("16384"),
                    "cuda.shares": Decimal("4"),
                },
                occupied_slots={
                    "cpu": Decimal("6"),
                    "mem": Decimal("12288"),
                    "cuda.shares": Decimal("1"),
                },
            ),
        ]

        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({
                "cpu": Decimal("1"),
                "mem": Decimal("2048"),
                "cuda.shares": Decimal("0.5"),
            }),
            required_architecture="x86_64",
        )

        # Available resources:
        # low-gpu: 14 CPU, 28672 memory, 1 GPU
        # high-gpu: 2 CPU, 4096 memory, 3 GPU

        # Convert agents to trackers
        trackers = [AgentStateTracker(original_agent=agent) for agent in agents]

        selected = selector.select_tracker_by_strategy(
            trackers, resource_req, basic_criteria, basic_config
        )

        # Should select low-gpu (less GPU available, which is highest priority)
        assert selected.original_agent.agent_id == AgentId("low-gpu")
