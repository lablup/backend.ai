"""Integration tests for agent selector strategies."""

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


class TestSelectorIntegration:
    """Integration tests comparing different selector strategies."""

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

    @pytest.fixture
    def resource_priority(self) -> list[str]:
        """Standard resource priority."""
        return ["cpu", "mem", "cuda.shares"]

    def test_strategy_comparison_basic(
        self,
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
        resource_priority: list[str],
    ) -> None:
        """Test that different strategies make different choices for the same scenario."""
        agents = [
            create_agent_info(
                agent_id="agent-1",
                available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
                occupied_slots={"cpu": Decimal("14"), "mem": Decimal("28672")},
            ),
            create_agent_info(
                agent_id="agent-2",
                available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
                occupied_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            ),
            create_agent_info(
                agent_id="agent-3",
                available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
                occupied_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
            ),
        ]

        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            required_architecture="x86_64",
        )

        # Create selectors
        concentrated = ConcentratedAgentSelector(resource_priority)
        dispersed = DispersedAgentSelector(resource_priority)
        legacy = LegacyAgentSelector(resource_priority)
        roundrobin = RoundRobinAgentSelector(next_index=1)

        # Get selections
        # Convert agents to trackers
        trackers = [AgentStateTracker(original_agent=agent) for agent in agents]
        concentrated_choice = concentrated.select_tracker_by_strategy(
            trackers, resource_req, criteria, config
        )
        dispersed_choice = dispersed.select_tracker_by_strategy(
            trackers, resource_req, criteria, config
        )
        legacy_choice = legacy.select_tracker_by_strategy(trackers, resource_req, criteria, config)
        roundrobin_choice = roundrobin.select_tracker_by_strategy(
            trackers, resource_req, criteria, config
        )

        # Verify different strategies make appropriate choices
        assert concentrated_choice.original_agent.agent_id == AgentId("agent-1")  # Least resources
        assert dispersed_choice.original_agent.agent_id == AgentId("agent-3")  # Most resources
        assert legacy_choice.original_agent.agent_id == AgentId(
            "agent-3"
        )  # Most resources (no unutilized)
        assert roundrobin_choice.original_agent.agent_id == AgentId("agent-2")  # Index 1

    def test_mixed_resource_types_comparison(
        self, criteria: AgentSelectionCriteria, config: AgentSelectionConfig
    ) -> None:
        """Test strategy differences with mixed resource types."""
        agents = [
            create_agent_info(
                agent_id="gpu-specialist",
                available_slots={
                    "cpu": Decimal("8"),
                    "mem": Decimal("16384"),
                    "cuda.shares": Decimal("8"),
                },
                occupied_slots={
                    "cpu": Decimal("4"),
                    "mem": Decimal("8192"),
                    "cuda.shares": Decimal("0"),
                },
            ),
            create_agent_info(
                agent_id="tpu-specialist",
                available_slots={
                    "cpu": Decimal("8"),
                    "mem": Decimal("16384"),
                    "tpu": Decimal("4"),
                },
                occupied_slots={
                    "cpu": Decimal("4"),
                    "mem": Decimal("8192"),
                    "tpu": Decimal("0"),
                },
            ),
            create_agent_info(
                agent_id="cpu-generalist",
                available_slots={
                    "cpu": Decimal("16"),
                    "mem": Decimal("32768"),
                },
                occupied_slots={
                    "cpu": Decimal("8"),
                    "mem": Decimal("16384"),
                },
            ),
        ]

        # Request only CPU/memory (explicitly no GPU/TPU)
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

        concentrated = ConcentratedAgentSelector(["cpu", "mem"])
        dispersed = DispersedAgentSelector(["cpu", "mem"])
        legacy = LegacyAgentSelector(["cpu", "mem"])

        # All have same CPU/mem available, but different unutilized capabilities
        # Convert agents to trackers
        trackers = [AgentStateTracker(original_agent=agent) for agent in agents]
        concentrated_choice = concentrated.select_tracker_by_strategy(
            trackers, resource_req, criteria, config
        )
        dispersed_choice = dispersed.select_tracker_by_strategy(
            trackers, resource_req, criteria, config
        )
        legacy_choice = legacy.select_tracker_by_strategy(trackers, resource_req, criteria, config)

        # Concentrated prefers fewer unutilized capabilities
        assert concentrated_choice.original_agent.agent_id == AgentId("cpu-generalist")
        # Dispersed also prefers fewer unutilized capabilities when resources are equal
        assert dispersed_choice.original_agent.agent_id == AgentId("cpu-generalist")
        # Legacy also prefers fewer unutilized capabilities
        assert legacy_choice.original_agent.agent_id == AgentId("cpu-generalist")

    # @pytest.mark.asyncio
    # async def test_with_agent_selector_wrapper(self, criteria, config, resource_priority):
    #     """Test selectors through the AgentSelector wrapper."""
    #     # This test needs to be rewritten for the new batch selection API
    #     # The select_agent_for_resource_requirements method no longer exists
    #     pass

    def test_large_scale_performance(
        self,
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
        resource_priority: list[str],
    ) -> None:
        """Test selector performance with many agents."""
        # Create 100 agents with varying resource levels
        agents = []
        for i in range(100):
            occupied_cpu = Decimal(str(i % 16))
            occupied_mem = Decimal(str((i % 16) * 2048))
            agents.append(
                create_agent_info(
                    agent_id=f"agent-{i:03d}",
                    available_slots={
                        "cpu": Decimal("16"),
                        "mem": Decimal("32768"),
                        "cuda.shares": Decimal("4") if i % 3 == 0 else Decimal("0"),
                    },
                    occupied_slots={
                        "cpu": occupied_cpu,
                        "mem": occupied_mem,
                        "cuda.shares": Decimal("0"),
                    },
                )
            )

        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            required_architecture="x86_64",
        )

        # Test each selector
        selectors = {
            "concentrated": ConcentratedAgentSelector(resource_priority),
            "dispersed": DispersedAgentSelector(resource_priority),
            "legacy": LegacyAgentSelector(resource_priority),
            "roundrobin": RoundRobinAgentSelector(next_index=42),
        }

        results = {}
        # Convert agents to trackers
        trackers = [AgentStateTracker(original_agent=agent) for agent in agents]
        for name, selector in selectors.items():
            selected = selector.select_tracker_by_strategy(trackers, resource_req, criteria, config)
            results[name] = selected

        # Verify all made valid selections
        assert all(result is not None for result in results.values())

        # Concentrated should pick highly utilized agent
        assert results["concentrated"].original_agent.agent_id == AgentId(
            "agent-015"
        )  # Highest utilization (15/16)

        # Dispersed should pick least utilized agent
        assert results["dispersed"].original_agent.agent_id == AgentId(
            "agent-000"
        )  # Lowest utilization (0/16)

        # Round-robin should pick based on index
        assert results["roundrobin"].original_agent.agent_id == AgentId("agent-042")  # Index 42

    def test_inference_session_spreading(self, config: AgentSelectionConfig) -> None:
        """Test special behavior for inference sessions with endpoint replica spreading."""
        # Create criteria for inference session
        criteria = AgentSelectionCriteria(
            session_metadata=SessionMetadata(
                session_id=SessionId(uuid.uuid4()),
                session_type=SessionTypes.INFERENCE,
                scaling_group="default",
                cluster_mode=ClusterMode.SINGLE_NODE,
            ),
            kernel_requirements={},
            kernel_counts_at_endpoint={
                AgentId("agent-1"): 10,
                AgentId("agent-2"): 5,
                AgentId("agent-3"): 2,
            },
        )

        config = AgentSelectionConfig(
            max_container_count=None,
            enforce_spreading_endpoint_replica=True,
        )

        agents = [
            create_agent_info(
                agent_id="agent-1",
                available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
                occupied_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            ),
            create_agent_info(
                agent_id="agent-2",
                available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
                occupied_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            ),
            create_agent_info(
                agent_id="agent-3",
                available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
                occupied_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
            ),
        ]

        resource_req = ResourceRequirements(
            kernel_ids=[uuid.uuid4()],
            requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("2048")}),
            required_architecture="x86_64",
        )

        # Only concentrated selector considers endpoint spreading
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

        # Concentrated should pick agent-3 (least kernels at endpoint)
        assert concentrated_choice.original_agent.agent_id == AgentId("agent-3")

        # Dispersed ignores kernel counts, picks any (all have same resources)
        assert dispersed_choice.original_agent.agent_id in [
            AgentId("agent-1"),
            AgentId("agent-2"),
            AgentId("agent-3"),
        ]
