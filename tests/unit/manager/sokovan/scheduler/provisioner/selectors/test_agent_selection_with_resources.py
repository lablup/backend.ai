"""Test agent selection with ResourceRequirements."""

from __future__ import annotations

import uuid
from decimal import Decimal

from ai.backend.common.types import AgentId, ClusterMode, ResourceSlot, SessionId, SessionTypes
from ai.backend.manager.data.sokovan import AgentInfo
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.concentrated import (
    ConcentratedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.dispersed import (
    DispersedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.exceptions import (
    NoAvailableAgentError,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentSelectionConfig,
    AgentSelectionCriteria,
    AgentSelector,
    KernelResourceSpec,
    SessionMetadata,
)


class TestAgentSelectionWithResources:
    """Test agent selection using ResourceRequirements."""

    async def test_single_node_selection_with_aggregated_resources(
        self,
        agents_for_resource_requirements_test: list[AgentInfo],
    ) -> None:
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

        # Total requested: 6 CPU, 12288 memory
        # Available resources:
        # - agent-low: 1 CPU, 2048 memory (insufficient)
        # - agent-medium: 4 CPU, 8192 memory (insufficient)
        # - agent-high: 14 CPU, 28672 memory (sufficient)

        # Use batch selection API
        result = await selector.select_agents_for_batch_requirements(
            agents_for_resource_requirements_test,
            criteria,
            config,
            designated_agent_ids=None,
        )

        # For single-node, there should be one selection with aggregated resources
        assert len(result.selections) == 1
        assert not result.failures
        selected_agent = result.selections[0].selected_agent

        # Only agent-high has enough resources for aggregated requirements
        assert selected_agent.agent_id == AgentId("agent-high")

    async def test_multi_node_selection_individual_resources(
        self,
        agents_for_resource_requirements_test: list[AgentInfo],
    ) -> None:
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

        # Use batch selection API
        result = await selector.select_agents_for_batch_requirements(
            agents_for_resource_requirements_test,
            criteria,
            config,
            designated_agent_ids=None,
        )

        # For multi-node, should have 2 selections (one per kernel)
        assert len(result.selections) == 2
        assert not result.failures

        # Both requirements can be satisfied by any agent
        # Dispersed selector should prefer agents with more available resources
        selected_agents = [sel.selected_agent.agent_id for sel in result.selections]
        assert all(agent_id is not None for agent_id in selected_agents)

    async def test_designated_agent_with_resource_requirements(
        self,
        agents_for_designated_agent_test: list[AgentInfo],
    ) -> None:
        """Test designated agent selection respects resource requirements."""
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

        config = AgentSelectionConfig(max_container_count=None)

        strategy = ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])
        selector = AgentSelector(strategy)

        # Try to select designated agent
        result = await selector.select_agents_for_batch_requirements(
            agents_for_designated_agent_test,
            criteria,
            config,
            designated_agent_ids=[AgentId("designated")],
        )

        # Should report a failure because designated agent lacks resources
        assert not result.selections
        assert len(result.failures) == 1
        error = result.failures[0].error
        assert isinstance(error, NoAvailableAgentError)
        message = str(error)
        assert "no designated agent is compatible" in message
        assert "designated agent 'designated'" in message
        assert "insufficient resources" in message
        # Aggregated detail lines must be split with newlines, not "; ".
        assert "; " not in message
        assert "\n" in message

    async def test_container_limit_with_resource_requirements(
        self,
        agents_for_container_limit_test: list[AgentInfo],
    ) -> None:
        """Test that container limits are respected with resource requirements."""
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

        config = AgentSelectionConfig(
            max_container_count=10,  # Set limit
            enforce_spreading_endpoint_replica=False,
        )

        strategy = ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])
        selector = AgentSelector(strategy)

        result = await selector.select_agents_for_batch_requirements(
            agents_for_container_limit_test,
            criteria,
            config,
            designated_agent_ids=None,
        )

        # Should select "available" agent since "busy" is at container limit
        assert len(result.selections) == 1
        assert not result.failures
        assert result.selections[0].selected_agent.agent_id == AgentId("available")

    async def test_architecture_mismatch_with_resource_requirements(
        self,
        agents_for_architecture_test: list[AgentInfo],
    ) -> None:
        """Test that architecture requirements are enforced."""
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

        config = AgentSelectionConfig(max_container_count=None)

        strategy = ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])
        selector = AgentSelector(strategy)

        result = await selector.select_agents_for_batch_requirements(
            agents_for_architecture_test,
            criteria,
            config,
            designated_agent_ids=None,
        )

        # Should select ARM agent
        assert len(result.selections) == 1
        assert not result.failures
        assert result.selections[0].selected_agent.agent_id == AgentId("arm")
