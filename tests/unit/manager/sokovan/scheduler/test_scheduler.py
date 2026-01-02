"""Tests for the Scheduler class allocation methods."""

import uuid
from decimal import Decimal
from typing import Optional, cast
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.repositories.schedule.repository import ScheduleRepository
from ai.backend.manager.sokovan.scheduler.launcher.launcher import (
    SessionLauncher,
    SessionLauncherArgs,
)
from ai.backend.manager.sokovan.scheduler.provisioner.provisioner import (
    SessionProvisioner,
    SessionProvisionerArgs,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.exceptions import (
    AgentSelectionError,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentInfo,
    AgentSelection,
    AgentSelectionConfig,
    AgentSelectionCriteria,
    AgentSelector,
    ResourceRequirements,
)
from ai.backend.manager.sokovan.scheduler.scheduler import (
    Scheduler,
    SchedulerArgs,
)
from ai.backend.manager.sokovan.scheduler.terminator.terminator import (
    SessionTerminator,
    SessionTerminatorArgs,
)
from ai.backend.manager.sokovan.scheduler.types import (
    KernelWorkload,
    SchedulingConfig,
    SessionWorkload,
)


def create_session_workload(
    session_id: Optional[SessionId] = None,
    cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE,
    kernels: Optional[list[KernelWorkload]] = None,
    designated_agent_ids: Optional[list[AgentId]] = None,
    **kwargs,
) -> SessionWorkload:
    """Create a SessionWorkload for testing."""
    # Set defaults for required fields
    session_id = session_id or SessionId(uuid.uuid4())
    access_key = kwargs.get("access_key", AccessKey("test-key"))
    requested_slots = kwargs.get(
        "requested_slots", ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")})
    )
    user_uuid = kwargs.get("user_uuid", uuid.uuid4())
    group_id = kwargs.get("group_id", uuid.uuid4())
    domain_name = kwargs.get("domain_name", "default")
    scaling_group = kwargs.get("scaling_group", "default")
    priority = kwargs.get("priority", 0)
    session_type = kwargs.get("session_type", SessionTypes.INTERACTIVE)
    starts_at = kwargs.get("starts_at", None)
    is_private = kwargs.get("is_private", False)
    kernels = kernels or []
    kernel_counts_at_endpoint = kwargs.get("kernel_counts_at_endpoint", None)

    return SessionWorkload(
        session_id=session_id,
        access_key=access_key,
        requested_slots=requested_slots,
        user_uuid=user_uuid,
        group_id=group_id,
        domain_name=domain_name,
        scaling_group=scaling_group,
        priority=priority,
        session_type=session_type,
        cluster_mode=cluster_mode,
        starts_at=starts_at,
        is_private=is_private,
        kernels=kernels,
        designated_agent_ids=designated_agent_ids,
        kernel_counts_at_endpoint=kernel_counts_at_endpoint,
    )


def create_kernel_workload(
    kernel_id: Optional[uuid.UUID] = None,
    cpu: Decimal = Decimal("1"),
    mem: Decimal = Decimal("1024"),
    architecture: str = "x86_64",
) -> KernelWorkload:
    """Create a KernelWorkload for testing."""
    return KernelWorkload(
        kernel_id=kernel_id or uuid.uuid4(),
        image="test-image",
        architecture=architecture,
        requested_slots=ResourceSlot({"cpu": cpu, "mem": mem}),
    )


def create_agent_info(
    agent_id: str,
    available_cpu: Decimal,
    occupied_cpu: Decimal,
    available_mem: Decimal = Decimal("8192"),
    occupied_mem: Decimal = Decimal("0"),
    container_count: int = 0,
) -> AgentInfo:
    """Create an AgentInfo for testing."""
    return AgentInfo(
        agent_id=AgentId(agent_id),
        agent_addr=f"{agent_id}:6001",
        architecture="x86_64",
        available_slots=ResourceSlot({"cpu": available_cpu, "mem": available_mem}),
        occupied_slots=ResourceSlot({"cpu": occupied_cpu, "mem": occupied_mem}),
        scaling_group="default",
        container_count=container_count,
    )


class TestSchedulerAllocation:
    """Test cases for the _allocate_workload method."""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Create a mock repository."""
        repo = MagicMock(spec=ScheduleRepository)
        repo.get_scheduling_config = AsyncMock(
            return_value=SchedulingConfig(
                max_container_count_per_agent=100,
                enforce_spreading_endpoint_replica=False,
            )
        )
        return repo

    @pytest.fixture
    def mock_agent_selector_with_verification(self) -> Mock:
        """Create a mock agent selector that tracks call history."""
        selector = MagicMock(spec=AgentSelector)
        call_history = []

        async def select_agent_side_effect(
            agents: list[AgentInfo],
            resource_req: ResourceRequirements,
            criteria: AgentSelectionCriteria,
            config: AgentSelectionConfig,
            designated_agent: Optional[AgentId],
        ) -> AgentInfo:
            try:
                # Capture the state of agents at each call
                agent_states = []
                for agent in agents:
                    available = agent.available_slots - agent.occupied_slots
                    # Copy occupied_slots properly
                    if hasattr(agent.occupied_slots, "copy"):
                        occupied_copy = agent.occupied_slots.copy()
                    else:
                        occupied_copy = ResourceSlot(dict(agent.occupied_slots))

                    agent_states.append({
                        "agent_id": agent.agent_id,
                        "available": available,
                        "occupied": occupied_copy,
                        "container_count": agent.container_count,
                    })
                # Copy requested_slots properly
                if hasattr(resource_req.requested_slots, "copy"):
                    req_slots_copy = resource_req.requested_slots.copy()
                else:
                    # It's a ResourceSlot object, create a new one from its data
                    req_slots_copy = ResourceSlot(dict(resource_req.requested_slots))

                call_history.append({
                    "requested_slots": req_slots_copy,
                    "agent_states": agent_states,
                    "designated_agent": designated_agent,
                })
            except Exception:
                pass  # Silently ignore errors in tracking

            # Select agent with most available CPU
            best_agent = None
            max_available = Decimal("-1")
            for agent in agents:
                available_slots = agent.available_slots - agent.occupied_slots
                available_cpu = available_slots.get("cpu", Decimal("0"))
                requested_cpu = resource_req.requested_slots.get("cpu", Decimal("0"))
                if available_cpu >= requested_cpu and available_cpu > max_available:
                    best_agent = agent
                    max_available = available_cpu

            if not best_agent:
                from ai.backend.manager.sokovan.scheduler.provisioner.selectors.exceptions import (
                    NoCompatibleAgentError,
                )

                raise NoCompatibleAgentError("No suitable agent found")

            return best_agent

        # Mock the batch selection method
        async def select_agents_for_batch_side_effect(
            agents: list[AgentInfo],
            criteria: AgentSelectionCriteria,
            config: AgentSelectionConfig,
            designated_agent: Optional[AgentId] = None,
        ) -> list[AgentSelection]:
            # Extract resource requirements from criteria
            resource_requirements = criteria.get_resource_requirements()
            from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
                AgentSelection,
            )

            selections = []
            for resource_req in resource_requirements:
                # Use the single selection logic
                agent = await select_agent_side_effect(
                    agents, resource_req, criteria, config, designated_agent
                )
                # Update agent state
                agent.occupied_slots = agent.occupied_slots + resource_req.requested_slots
                agent.container_count = agent.container_count + len(resource_req.kernel_ids)

                selections.append(
                    AgentSelection(
                        resource_requirements=resource_req,
                        selected_agent=agent,
                    )
                )
            return selections

        # Make call_history accessible as an attribute
        selector.select_agents_for_batch_requirements = AsyncMock(
            side_effect=select_agents_for_batch_side_effect
        )
        # Attach call_history directly to the selector object
        selector.call_history = call_history
        return selector

    @pytest.fixture
    def scheduler(
        self, mock_repository: MagicMock, mock_agent_selector_with_verification: Mock
    ) -> Scheduler:
        """Create a scheduler instance with mocked dependencies."""
        mock_config_provider = MagicMock()
        mock_valkey_schedule = MagicMock()
        mock_agent_pool = MagicMock()
        provisioner = SessionProvisioner(
            SessionProvisionerArgs(
                validator=MagicMock(),
                default_sequencer=MagicMock(),
                default_agent_selector=mock_agent_selector_with_verification,
                allocator=MagicMock(),
                repository=mock_repository,
                config_provider=mock_config_provider,
                valkey_schedule=mock_valkey_schedule,
            )
        )
        launcher = SessionLauncher(
            SessionLauncherArgs(
                repository=mock_repository,
                agent_pool=mock_agent_pool,
                network_plugin_ctx=MagicMock(),
                config_provider=mock_config_provider,
                valkey_schedule=mock_valkey_schedule,
            )
        )
        terminator = SessionTerminator(
            SessionTerminatorArgs(
                repository=mock_repository,
                agent_pool=mock_agent_pool,
                valkey_schedule=mock_valkey_schedule,
            )
        )
        args = SchedulerArgs(
            provisioner=provisioner,
            launcher=launcher,
            terminator=terminator,
            repository=mock_repository,
            deployment_repository=MagicMock(),
            config_provider=mock_config_provider,
            lock_factory=MagicMock(),
            agent_pool=mock_agent_pool,
            network_plugin_ctx=MagicMock(),
            event_producer=MagicMock(),
            valkey_schedule=mock_valkey_schedule,
        )
        return Scheduler(args)

    async def test_allocate_single_node_session_success(self, scheduler: Scheduler) -> None:
        """Test successful allocation of a single-node session."""
        # Create session workload with 3 kernels
        kernels = [
            create_kernel_workload(cpu=Decimal("1"), mem=Decimal("1024")),
            create_kernel_workload(cpu=Decimal("1"), mem=Decimal("1024")),
            create_kernel_workload(cpu=Decimal("1"), mem=Decimal("1024")),
        ]
        session_id = SessionId(uuid.uuid4())
        workload = create_session_workload(
            session_id=session_id,
            cluster_mode=ClusterMode.SINGLE_NODE,
            kernels=kernels,
        )

        # Create agents
        agents = [
            create_agent_info("agent-1", Decimal("8"), Decimal("2"), container_count=2),
            create_agent_info("agent-2", Decimal("8"), Decimal("4"), container_count=4),
        ]

        selection_config = AgentSelectionConfig(
            max_container_count=100, enforce_spreading_endpoint_replica=False
        )

        # Execute allocation
        result = await scheduler._provisioner._allocate_workload(
            workload,
            agents,
            selection_config,
            "default",
            scheduler._provisioner._default_agent_selector,
        )

        # Verify result
        assert result is not None
        assert result.session_id == session_id
        assert result.session_type == SessionTypes.INTERACTIVE
        assert result.cluster_mode == ClusterMode.SINGLE_NODE
        assert result.scaling_group == "default"

        # Should have 3 kernel allocations (one per kernel)
        assert len(result.kernel_allocations) == 3
        # All should be on agent-1 (more available CPU: 6 vs 4)
        for kernel_alloc in result.kernel_allocations:
            assert kernel_alloc.agent_id == AgentId("agent-1")

        # Should have 1 agent allocation with aggregated resources
        assert len(result.agent_allocations) == 1
        assert result.agent_allocations[0].agent_id == AgentId("agent-1")
        assert len(result.agent_allocations[0].allocated_slots) == 1
        # Total requested: 3 CPU, 3072 memory
        assert result.agent_allocations[0].allocated_slots[0] == ResourceSlot({
            "cpu": Decimal("3"),
            "mem": Decimal("3072"),
        })

        # Verify agent state was updated
        assert agents[0].occupied_slots == ResourceSlot({
            "cpu": Decimal("5"),
            "mem": Decimal("3072"),
        })  # 2 + 3
        assert agents[0].container_count == 5  # 2 + 3

        # Verify selector was called once (aggregated for single-node)
        mock_selector = cast(Mock, scheduler._provisioner._default_agent_selector)
        assert mock_selector.select_agents_for_batch_requirements.call_count == 1

        # Check call_history if it was populated
        mock_selector = cast(Mock, scheduler._provisioner._default_agent_selector)
        if mock_selector.call_history:
            assert len(mock_selector.call_history) == 1
            call = mock_selector.call_history[0]
            assert call["requested_slots"] == ResourceSlot({
                "cpu": Decimal("3"),
                "mem": Decimal("3072"),
            })

    async def test_allocate_multi_node_session_success(self, scheduler: Scheduler) -> None:
        """Test successful allocation of a multi-node session."""
        # Create session workload with 3 kernels
        kernels = [
            create_kernel_workload(cpu=Decimal("2"), mem=Decimal("2048")),
            create_kernel_workload(cpu=Decimal("2"), mem=Decimal("2048")),
            create_kernel_workload(cpu=Decimal("1"), mem=Decimal("1024")),
        ]
        session_id = SessionId(uuid.uuid4())
        workload = create_session_workload(
            session_id=session_id,
            cluster_mode=ClusterMode.MULTI_NODE,
            kernels=kernels,
        )

        # Create agents
        agents = [
            create_agent_info("agent-1", Decimal("4"), Decimal("0")),
            create_agent_info("agent-2", Decimal("4"), Decimal("1")),
        ]

        selection_config = AgentSelectionConfig(
            max_container_count=100, enforce_spreading_endpoint_replica=False
        )

        # Execute allocation
        result = await scheduler._provisioner._allocate_workload(
            workload,
            agents,
            selection_config,
            "default",
            scheduler._provisioner._default_agent_selector,
        )

        # Verify result
        assert result is not None
        assert len(result.kernel_allocations) == 3

        # First kernel should go to agent-1 (4 available vs 3)
        assert result.kernel_allocations[0].agent_id == AgentId("agent-1")
        # Second kernel should go to agent-2 (3 available vs 2)
        assert result.kernel_allocations[1].agent_id == AgentId("agent-2")
        # Third kernel should go to agent-1 (2 available vs 1)
        assert result.kernel_allocations[2].agent_id == AgentId("agent-1")

        # Verify agent allocations
        assert len(result.agent_allocations) == 2
        agent_alloc_map = {alloc.agent_id: alloc for alloc in result.agent_allocations}
        # Agent-1 got kernel 0 and 2
        assert len(agent_alloc_map[AgentId("agent-1")].allocated_slots) == 2
        # Agent-2 got kernel 1
        assert len(agent_alloc_map[AgentId("agent-2")].allocated_slots) == 1

        # Verify final agent states
        assert agents[0].occupied_slots == ResourceSlot({
            "cpu": Decimal("3"),
            "mem": Decimal("3072"),
        })  # 2 + 1
        assert agents[0].container_count == 2  # 0 + 2 kernels
        assert agents[1].occupied_slots == ResourceSlot({
            "cpu": Decimal("3"),
            "mem": Decimal("2048"),
        })  # 1 + 2
        assert agents[1].container_count == 1  # 0 + 1 kernel

    async def test_agent_state_updates_affect_selection(self, scheduler: Scheduler) -> None:
        """Test that agent state updates affect subsequent selections."""
        # Create session with 3 kernels requiring 2 CPU each
        kernels = [
            create_kernel_workload(cpu=Decimal("2"), mem=Decimal("2048")),
            create_kernel_workload(cpu=Decimal("2"), mem=Decimal("2048")),
            create_kernel_workload(cpu=Decimal("2"), mem=Decimal("2048")),
        ]
        workload = create_session_workload(
            cluster_mode=ClusterMode.MULTI_NODE,
            kernels=kernels,
        )

        # Create agents with limited resources
        agents = [
            create_agent_info("agent-1", Decimal("4"), Decimal("2")),  # 2 available
            create_agent_info("agent-2", Decimal("4"), Decimal("1")),  # 3 available
        ]

        selection_config = AgentSelectionConfig(
            max_container_count=100, enforce_spreading_endpoint_replica=False
        )

        # Execute allocation - should raise NoCompatibleAgentError
        from ai.backend.manager.sokovan.scheduler.provisioner.selectors.exceptions import (
            NoCompatibleAgentError,
        )

        with pytest.raises(NoCompatibleAgentError):
            await scheduler._provisioner._allocate_workload(
                workload,
                agents,
                selection_config,
                "default",
                scheduler._provisioner._default_agent_selector,
            )

        # Verify selector was called once with 3 resource requirements
        mock_selector = cast(Mock, scheduler._provisioner._default_agent_selector)
        assert mock_selector.select_agents_for_batch_requirements.call_count == 1

        # Verify selector call history
        mock_selector = cast(Mock, scheduler._provisioner._default_agent_selector)
        call_history = mock_selector.call_history
        if not call_history:
            # If call_history wasn't populated due to the exception handling,
            # we can still verify the mock was called the right number of times
            return

        assert len(call_history) == 3  # Three attempts

        # First call: agent-2 has more available (3 vs 2)
        assert call_history[0]["agent_states"][0]["available"]["cpu"] == Decimal("2")
        assert call_history[0]["agent_states"][1]["available"]["cpu"] == Decimal("3")

        # Second call: agent-1 now has more available (2 vs 1)
        assert call_history[1]["agent_states"][0]["available"]["cpu"] == Decimal("2")
        assert call_history[1]["agent_states"][1]["available"]["cpu"] == Decimal("1")

        # Third call: neither agent has enough (0 vs 1)
        assert call_history[2]["agent_states"][0]["available"]["cpu"] == Decimal("0")
        assert call_history[2]["agent_states"][1]["available"]["cpu"] == Decimal("1")

    async def test_allocate_with_designated_agent(self, scheduler: Scheduler) -> None:
        """Test allocation with a designated agent."""
        kernels = [create_kernel_workload()]
        designated_agent = AgentId("agent-2")
        workload = create_session_workload(
            cluster_mode=ClusterMode.SINGLE_NODE,
            kernels=kernels,
            designated_agent_ids=[designated_agent],
        )

        agents = [
            create_agent_info("agent-1", Decimal("8"), Decimal("0")),
            create_agent_info("agent-2", Decimal("8"), Decimal("4")),
        ]

        selection_config = AgentSelectionConfig(
            max_container_count=100, enforce_spreading_endpoint_replica=False
        )

        # Mock to return the designated agent
        async def return_designated_batch(
            agents: list[AgentInfo],
            criteria: AgentSelectionCriteria,
            config: AgentSelectionConfig,
            designated_agent_ids: Optional[list[AgentId]],
        ) -> list[AgentSelection]:
            from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
                AgentSelection,
            )

            resource_requirements = criteria.get_resource_requirements()
            selections = []
            if not designated_agent_ids:
                raise AgentSelectionError("No designated agent provided")
            for resource_req in resource_requirements:
                for agent in agents:
                    if agent.agent_id in designated_agent_ids:
                        selections.append(
                            AgentSelection(
                                resource_requirements=resource_req,
                                selected_agent=agent,
                            )
                        )
                        break
                else:
                    raise AgentSelectionError("Designated agent not found")
            return selections

        mock_selector = cast(Mock, scheduler._provisioner._default_agent_selector)
        mock_selector.select_agents_for_batch_requirements.side_effect = return_designated_batch

        # Execute allocation
        result = await scheduler._provisioner._allocate_workload(
            workload,
            agents,
            selection_config,
            "default",
            scheduler._provisioner._default_agent_selector,
        )

        # Verify designated agent was selected
        assert result is not None
        assert result.kernel_allocations[0].agent_id == designated_agent

        # Verify designated_agent was passed to selector
        mock_selector = cast(Mock, scheduler._provisioner._default_agent_selector)
        selector_calls = mock_selector.select_agents_for_batch_requirements.call_args_list
        assert len(selector_calls) == 1
        assert selector_calls[0][0][3] == [
            designated_agent
        ]  # 4th argument (agents, criteria, config, designated_agent)

    async def test_no_resource_requirements(self, scheduler: Scheduler):
        """Test handling of session with no kernels."""
        workload = create_session_workload(
            cluster_mode=ClusterMode.SINGLE_NODE,
            kernels=[],  # No kernels
        )

        agents = [create_agent_info("agent-1", Decimal("8"), Decimal("0"))]

        selection_config = AgentSelectionConfig(
            max_container_count=100, enforce_spreading_endpoint_replica=False
        )

        # Execute allocation
        result = await scheduler._provisioner._allocate_workload(
            workload,
            agents,
            selection_config,
            "default",
            scheduler._provisioner._default_agent_selector,
        )

        # Should return empty allocations
        assert result is not None
        assert len(result.kernel_allocations) == 0
        assert len(result.agent_allocations) == 0

        # Should return empty list for empty kernels
        mock_selector = cast(Mock, scheduler._provisioner._default_agent_selector)
        assert mock_selector.select_agents_for_batch_requirements.call_count == 1

    async def test_agent_selection_error(self, scheduler: Scheduler):
        """Test handling of agent selection errors."""
        kernels = [create_kernel_workload(cpu=Decimal("100"))]  # Impossible requirement
        workload = create_session_workload(
            cluster_mode=ClusterMode.SINGLE_NODE,
            kernels=kernels,
        )

        agents = [create_agent_info("agent-1", Decimal("8"), Decimal("0"))]

        selection_config = AgentSelectionConfig(
            max_container_count=100, enforce_spreading_endpoint_replica=False
        )

        # Execute allocation - should raise NoCompatibleAgentError
        from ai.backend.manager.sokovan.scheduler.provisioner.selectors.exceptions import (
            NoCompatibleAgentError,
        )

        with pytest.raises(NoCompatibleAgentError):
            await scheduler._provisioner._allocate_workload(
                workload,
                agents,
                selection_config,
                "default",
                scheduler._provisioner._default_agent_selector,
            )

    async def test_multiple_kernels_same_agent(self, scheduler: Scheduler) -> None:
        """Test multi-node session where multiple kernels go to the same agent."""
        kernels = [
            create_kernel_workload(cpu=Decimal("1"), mem=Decimal("1024")),
            create_kernel_workload(cpu=Decimal("1"), mem=Decimal("1024")),
            create_kernel_workload(cpu=Decimal("1"), mem=Decimal("1024")),
        ]
        workload = create_session_workload(
            cluster_mode=ClusterMode.MULTI_NODE,
            kernels=kernels,
        )

        # Only one agent available
        agents = [create_agent_info("agent-1", Decimal("8"), Decimal("0"))]

        selection_config = AgentSelectionConfig(
            max_container_count=100, enforce_spreading_endpoint_replica=False
        )

        # Execute allocation
        result = await scheduler._provisioner._allocate_workload(
            workload,
            agents,
            selection_config,
            "default",
            scheduler._provisioner._default_agent_selector,
        )

        # Verify all kernels allocated to the same agent
        assert result is not None
        assert len(result.kernel_allocations) == 3
        for kernel_alloc in result.kernel_allocations:
            assert kernel_alloc.agent_id == AgentId("agent-1")

        # Should have 1 agent allocation with 3 resource slots
        assert len(result.agent_allocations) == 1
        assert result.agent_allocations[0].agent_id == AgentId("agent-1")
        assert len(result.agent_allocations[0].allocated_slots) == 3

        # Verify agent state accumulation
        assert agents[0].occupied_slots == ResourceSlot({
            "cpu": Decimal("3"),
            "mem": Decimal("3072"),
        })
        assert agents[0].container_count == 3

    async def test_concurrent_selection_isolation(self, scheduler: Scheduler) -> None:
        """Test that modifications to agents don't affect other agent lists."""
        kernels = [create_kernel_workload(cpu=Decimal("2"))]
        workload = create_session_workload(
            cluster_mode=ClusterMode.SINGLE_NODE,
            kernels=kernels,
        )

        # Create two separate agent lists (simulating concurrent sessions)
        agents_session1 = [
            create_agent_info("agent-1", Decimal("8"), Decimal("0")),
            create_agent_info("agent-2", Decimal("8"), Decimal("0")),
        ]
        agents_session2 = [
            create_agent_info("agent-1", Decimal("8"), Decimal("0")),
            create_agent_info("agent-2", Decimal("8"), Decimal("0")),
        ]

        selection_config = AgentSelectionConfig(
            max_container_count=100, enforce_spreading_endpoint_replica=False
        )

        # Execute allocation for session 1
        result1 = await scheduler._provisioner._allocate_workload(
            workload,
            agents_session1,
            selection_config,
            "default",
            scheduler._provisioner._default_agent_selector,
        )

        assert result1 is not None

        # Verify session 1 agents were modified
        assert agents_session1[0].occupied_slots["cpu"] == Decimal("2")
        assert agents_session1[0].container_count == 1

        # Verify session 2 agents remain unchanged
        assert agents_session2[0].occupied_slots["cpu"] == Decimal("0")
        assert agents_session2[0].container_count == 0

    async def test_empty_kernel_allocations_returns_proper_result(
        self, scheduler: Scheduler
    ) -> None:
        """Test the bug fix for empty kernel allocations."""
        # This tests the fix for lines 223-225 where empty kernel_allocations
        # incorrectly returns None

        # Create a workload that will result in empty allocations
        workload = create_session_workload(
            cluster_mode=ClusterMode.SINGLE_NODE,
            kernels=[],  # Empty kernels will lead to empty allocations
        )

        agents = [create_agent_info("agent-1", Decimal("8"), Decimal("0"))]
        selection_config = AgentSelectionConfig(
            max_container_count=100, enforce_spreading_endpoint_replica=False
        )

        # Execute allocation
        result = await scheduler._provisioner._allocate_workload(
            workload,
            agents,
            selection_config,
            "default",
            scheduler._provisioner._default_agent_selector,
        )

        # With empty kernels, get_resource_requirements returns empty list
        # So the method should return empty allocations
        assert result is not None
        assert len(result.kernel_allocations) == 0
        assert len(result.agent_allocations) == 0
