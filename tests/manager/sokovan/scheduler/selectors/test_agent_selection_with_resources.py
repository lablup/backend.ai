"""Test agent selection with ResourceRequirements."""

import uuid
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from ai.backend.common.types import AgentId, ClusterMode, ResourceSlot, SessionId, SessionTypes
from ai.backend.manager.sokovan.scheduler.selectors.concentrated import ConcentratedAgentSelector
from ai.backend.manager.sokovan.scheduler.selectors.dispersed import DispersedAgentSelector
from ai.backend.manager.sokovan.scheduler.selectors.selector import (
    AgentInfo,
    AgentSelectionConfig,
    AgentSelectionCriteria,
    AgentSelector,
    DesignatedAgentIncompatibleError,
    KernelResourceSpec,
    SessionMetadata,
)

from .conftest import create_agent_info


class TestAgentSelectionWithResources:
    """Test agent selection using ResourceRequirements."""

    @pytest.fixture
    def agents_with_varied_resources(self) -> list[AgentInfo]:
        """Create agents with varied resource availability."""
        return [
            create_agent_info(
                agent_id="agent-low",
                available_slots={
                    "cpu": Decimal("4"),
                    "mem": Decimal("8192"),
                },
                occupied_slots={
                    "cpu": Decimal("3"),
                    "mem": Decimal("6144"),
                },
                container_count=3,
            ),
            create_agent_info(
                agent_id="agent-medium",
                available_slots={
                    "cpu": Decimal("8"),
                    "mem": Decimal("16384"),
                },
                occupied_slots={
                    "cpu": Decimal("4"),
                    "mem": Decimal("8192"),
                },
                container_count=2,
            ),
            create_agent_info(
                agent_id="agent-high",
                available_slots={
                    "cpu": Decimal("16"),
                    "mem": Decimal("32768"),
                },
                occupied_slots={
                    "cpu": Decimal("2"),
                    "mem": Decimal("4096"),
                },
                container_count=1,
            ),
        ]

    @pytest.mark.asyncio
    async def test_single_node_selection_with_aggregated_resources(
        self, agents_with_varied_resources
    ):
        """Test single-node selection with aggregated resources."""
        # Create session metadata
        session_metadata = SessionMetadata(
            session_id=SessionId(uuid.uuid4()),
            session_type=SessionTypes.INTERACTIVE,
            scaling_group="default",
            cluster_mode=ClusterMode.SINGLE_NODE,
        )

        # Create kernel requirements that need aggregation
        kernel_reqs = {
            uuid.uuid4(): KernelResourceSpec(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("4"),
                    "mem": Decimal("8192"),
                }),
                required_architecture="x86_64",
            ),
            uuid.uuid4(): KernelResourceSpec(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("2"),
                    "mem": Decimal("4096"),
                }),
                required_architecture="x86_64",
            ),
        }

        criteria = AgentSelectionCriteria(
            session_metadata=session_metadata,
            kernel_requirements=kernel_reqs,
        )

        config = AgentSelectionConfig(
            max_container_count=None,
            enforce_spreading_endpoint_replica=False,
        )

        # Use concentrated selector
        strategy = ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])
        selector = AgentSelector(strategy)

        # Get aggregated requirements
        resource_reqs = criteria.get_resource_requirements()
        assert len(resource_reqs) == 1
        # For single-node, there's only one aggregated requirement
        aggregated_req = resource_reqs[0]

        # Total requested: 6 CPU, 12288 memory
        # Available resources:
        # - agent-low: 1 CPU, 2048 memory (insufficient)
        # - agent-medium: 4 CPU, 8192 memory (insufficient)
        # - agent-high: 14 CPU, 28672 memory (sufficient)

        selected_agent = await selector.select_agent_for_resource_requirements(
            agents_with_varied_resources,
            aggregated_req,
            criteria,
            config,
        )

        # Only agent-high has enough resources for aggregated requirements
        assert selected_agent.agent_id == AgentId("agent-high")

    @pytest.mark.asyncio
    async def test_multi_node_selection_individual_resources(self, agents_with_varied_resources):
        """Test multi-node selection with individual kernel resources."""
        session_metadata = SessionMetadata(
            session_id=SessionId(uuid.uuid4()),
            session_type=SessionTypes.BATCH,
            scaling_group="default",
            cluster_mode=ClusterMode.MULTI_NODE,
        )

        # Create kernels with different resource needs
        kernel_reqs = {
            uuid.uuid4(): KernelResourceSpec(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("1"),
                    "mem": Decimal("2048"),
                }),
                required_architecture="x86_64",
            ),
            uuid.uuid4(): KernelResourceSpec(
                requested_slots=ResourceSlot({
                    "cpu": Decimal("3"),
                    "mem": Decimal("6144"),
                }),
                required_architecture="x86_64",
            ),
        }

        criteria = AgentSelectionCriteria(
            session_metadata=session_metadata,
            kernel_requirements=kernel_reqs,
        )

        config = AgentSelectionConfig(
            max_container_count=None,
            enforce_spreading_endpoint_replica=False,
        )

        # Use dispersed selector for spreading
        strategy = DispersedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])
        selector = AgentSelector(strategy)

        # Get individual requirements
        resource_reqs = criteria.get_resource_requirements()
        assert len(resource_reqs) == 2

        # Select agent for each requirement
        selected_agents = []
        for req in resource_reqs:
            selected_agent = await selector.select_agent_for_resource_requirements(
                agents_with_varied_resources,
                req,
                criteria,
                config,
            )
            selected_agents.append(selected_agent.agent_id)

        # Both requirements can be satisfied by any agent
        # Dispersed selector should prefer agents with more available resources
        assert all(selected_id is not None for selected_id in selected_agents)

    @pytest.mark.asyncio
    async def test_designated_agent_with_resource_requirements(self):
        """Test designated agent selection respects resource requirements."""
        agents = [
            create_agent_info(
                agent_id="designated",
                available_slots={"cpu": Decimal("2"), "mem": Decimal("4096")},
                occupied_slots={"cpu": Decimal("0"), "mem": Decimal("0")},
            ),
            create_agent_info(
                agent_id="other",
                available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
                occupied_slots={"cpu": Decimal("0"), "mem": Decimal("0")},
            ),
        ]

        session_metadata = SessionMetadata(
            session_id=SessionId(uuid.uuid4()),
            session_type=SessionTypes.INTERACTIVE,
            scaling_group="default",
            cluster_mode=ClusterMode.SINGLE_NODE,
        )

        # Request more than designated agent has
        kernel_id = uuid.uuid4()
        kernel_spec = KernelResourceSpec(
            requested_slots=ResourceSlot({
                "cpu": Decimal("4"),
                "mem": Decimal("8192"),
            }),
            required_architecture="x86_64",
        )

        criteria = AgentSelectionCriteria(
            session_metadata=session_metadata,
            kernel_requirements={kernel_id: kernel_spec},
        )

        # Get resource requirements
        resource_reqs = criteria.get_resource_requirements()
        resource_req = resource_reqs[0]

        config = AgentSelectionConfig(max_container_count=None)

        strategy = MagicMock()
        selector = AgentSelector(strategy)

        # Try to select designated agent
        with pytest.raises(DesignatedAgentIncompatibleError) as exc_info:
            await selector.select_agent_for_resource_requirements(
                agents,
                resource_req,
                criteria,
                config,
                designated_agent=AgentId("designated"),
            )

        # Should raise error because designated agent lacks resources
        assert "does not meet resource requirements" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_container_limit_with_resource_requirements(self):
        """Test that container limits are respected with resource requirements."""
        agents = [
            create_agent_info(
                agent_id="busy",
                available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
                occupied_slots={"cpu": Decimal("0"), "mem": Decimal("0")},
                container_count=10,  # At limit
            ),
            create_agent_info(
                agent_id="available",
                available_slots={"cpu": Decimal("8"), "mem": Decimal("16384")},
                occupied_slots={"cpu": Decimal("0"), "mem": Decimal("0")},
                container_count=5,
            ),
        ]

        kernel_id = uuid.uuid4()
        kernel_spec = KernelResourceSpec(
            requested_slots=ResourceSlot({
                "cpu": Decimal("2"),
                "mem": Decimal("4096"),
            }),
            required_architecture="x86_64",
        )

        session_metadata = SessionMetadata(
            session_id=SessionId(uuid.uuid4()),
            session_type=SessionTypes.BATCH,
            scaling_group="default",
            cluster_mode=ClusterMode.SINGLE_NODE,
        )

        criteria = AgentSelectionCriteria(
            session_metadata=session_metadata,
            kernel_requirements={kernel_id: kernel_spec},
        )

        # Get resource requirements
        resource_reqs = criteria.get_resource_requirements()
        resource_req = resource_reqs[0]

        config = AgentSelectionConfig(
            max_container_count=10,  # Set limit
            enforce_spreading_endpoint_replica=False,
        )

        strategy = ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])
        selector = AgentSelector(strategy)

        selected_agent = await selector.select_agent_for_resource_requirements(
            agents,
            resource_req,
            criteria,
            config,
        )

        # Should select "available" agent since "busy" is at container limit
        assert selected_agent.agent_id == AgentId("available")

    @pytest.mark.asyncio
    async def test_architecture_mismatch_with_resource_requirements(self):
        """Test that architecture requirements are enforced."""
        agents = [
            create_agent_info(
                agent_id="x86",
                architecture="x86_64",
                available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
            ),
            create_agent_info(
                agent_id="arm",
                architecture="aarch64",
                available_slots={"cpu": Decimal("16"), "mem": Decimal("32768")},
            ),
        ]

        kernel_id = uuid.uuid4()
        kernel_spec = KernelResourceSpec(
            requested_slots=ResourceSlot({
                "cpu": Decimal("2"),
                "mem": Decimal("4096"),
            }),
            required_architecture="aarch64",  # Require ARM
        )

        session_metadata = SessionMetadata(
            session_id=SessionId(uuid.uuid4()),
            session_type=SessionTypes.INTERACTIVE,
            scaling_group="default",
            cluster_mode=ClusterMode.SINGLE_NODE,
        )

        criteria = AgentSelectionCriteria(
            session_metadata=session_metadata,
            kernel_requirements={kernel_id: kernel_spec},
        )

        # Get resource requirements
        resource_reqs = criteria.get_resource_requirements()
        resource_req = resource_reqs[0]

        config = AgentSelectionConfig(max_container_count=None)

        strategy = ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])
        selector = AgentSelector(strategy)

        selected_agent = await selector.select_agent_for_resource_requirements(
            agents,
            resource_req,
            criteria,
            config,
        )

        # Should select ARM agent
        assert selected_agent.agent_id == AgentId("arm")
