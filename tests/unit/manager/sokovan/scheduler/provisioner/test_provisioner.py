"""Tests for SessionProvisioner orchestration logic.

Tests that the provisioner correctly orchestrates validator, sequencer, selector, and allocator.
Individual component logic is tested separately - here we focus on orchestration flow
and correct agent selector selection based on agent_selection_strategy.
"""

from __future__ import annotations

<<<<<<< HEAD
import uuid
from datetime import datetime
=======
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
>>>>>>> 99e8e59f (fix(BA-7328): stop scheduling past a resource-exhausted session (#13707))
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from dateutil.tz import tzutc

<<<<<<< HEAD
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    AgentSelectionStrategy,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.repositories.scheduler.types.agent import AgentMeta
from ai.backend.manager.repositories.scheduler.types.base import SchedulingSpec
from ai.backend.manager.repositories.scheduler.types.scaling_group import ScalingGroupMeta
from ai.backend.manager.repositories.scheduler.types.scheduling import SchedulingData
from ai.backend.manager.repositories.scheduler.types.session import (
    PendingSessionData,
    PendingSessions,
)
from ai.backend.manager.repositories.scheduler.types.snapshot import (
    ResourcePolicies,
    SnapshotData,
)
from ai.backend.manager.sokovan.data import (
    ResourceOccupancySnapshot,
    SessionDependencySnapshot,
)
=======
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import AgentId, SessionId, SessionResult, SessionTypes
from ai.backend.manager.data.session.types import SessionStatus
>>>>>>> 99e8e59f (fix(BA-7328): stop scheduling past a resource-exhausted session (#13707))
from ai.backend.manager.sokovan.recorder import RecorderContext
from ai.backend.manager.sokovan.scheduler.provisioner.provisioner import (
    SessionProvisioner,
    SessionProvisionerArgs,
)
<<<<<<< HEAD
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentSelector,
=======
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.pool import create_agent_selector
from ai.backend.manager.sokovan.scheduler.provisioner.sequencers.fifo import FIFOSequencer
from ai.backend.manager.sokovan.scheduler.provisioner.validators.dependencies import (
    DependenciesValidator,
)
from ai.backend.manager.sokovan.scheduler.provisioner.validators.reserved_batch import (
    ReservedBatchSessionValidator,
)
from ai.backend.manager.sokovan.scheduler.provisioner.validators.resource_policy import (
    ResourcePolicyValidator,
)
from ai.backend.manager.sokovan.scheduler.provisioner.validators.validator import (
    SchedulingValidator,
)
from ai.backend.manager.sokovan.scheduler.results import ScheduleResult
from ai.backend.manager.views.sokovan.allocation import SessionAllocation
from ai.backend.manager.views.sokovan.scheduling import SchedulingData
from ai.backend.manager.views.sokovan.snapshot import (
    ResourcePolicySnapshot,
    UserResourceLimit,
)
from ai.backend.manager.views.sokovan.workload import SessionDependencyInfo, SessionWorkload

from .conftest import (
    RESOURCE_GROUP_NAME,
    AgentMetaFactory,
    SchedulingDataFactory,
    WorkloadFactory,
>>>>>>> 99e8e59f (fix(BA-7328): stop scheduling past a resource-exhausted session (#13707))
)


def _create_scheduling_data_with_strategy(
    strategy: AgentSelectionStrategy,
) -> SchedulingData:
    """Create SchedulingData with specific agent_selection_strategy and one session."""
    scheduler_opts = ScalingGroupOpts(agent_selection_strategy=strategy)

    scaling_group_meta = ScalingGroupMeta(
        name="test-sg",
        scheduler="fifo",
        scheduler_opts=scheduler_opts,
    )

    # Create one pending session
    session = PendingSessionData(
        id=SessionId(uuid.uuid4()),
        access_key=AccessKey("test-key"),
        requested_slots=ResourceSlot({"cpu": Decimal("1"), "mem": Decimal("1024")}),
        user_uuid=uuid.uuid4(),
        group_id=uuid.uuid4(),
        domain_name="default",
        scaling_group_name="test-sg",
        session_type=SessionTypes.INTERACTIVE,
        cluster_mode=ClusterMode.SINGLE_NODE,
        priority=0,
        is_preemptible=True,
        starts_at=None,
        is_private=False,
        kernels=[],
        designated_agent_ids=None,
    )

    # Create snapshot data
    snapshot_data = SnapshotData(
        resource_occupancy=ResourceOccupancySnapshot(
            by_keypair={},
            by_user={},
            by_group={},
            by_domain={},
            by_agent={},
        ),
        resource_policies=ResourcePolicies(
            keypair_policies={},
            user_policies={},
            group_limits={},
            domain_limits={},
        ),
        session_dependencies=SessionDependencySnapshot(by_session={}),
    )

    # Create agent
    agent = AgentMeta(
        id=AgentId("agent-1"),
        addr="agent-1:6001",
        architecture="x86_64",
        available_slots=ResourceSlot({"cpu": Decimal("8"), "mem": Decimal("16384")}),
        scaling_group="test-sg",
    )

    return SchedulingData(
        scaling_group=scaling_group_meta,
        pending_sessions=PendingSessions(sessions=[session]),
        agents=[agent],
        snapshot_data=snapshot_data,
        spec=SchedulingSpec(
            known_slot_types={},
            max_container_count=None,
        ),
    )


@pytest.fixture
def minimal_scheduling_data() -> SchedulingData:
    """Create minimal SchedulingData for testing."""
    scheduler_opts = ScalingGroupOpts(agent_selection_strategy=AgentSelectionStrategy.DISPERSED)

    scaling_group_meta = ScalingGroupMeta(
        name="test-sg",
        scheduler="fifo",
        scheduler_opts=scheduler_opts,
    )

    return SchedulingData(
        scaling_group=scaling_group_meta,
        pending_sessions=PendingSessions(sessions=[]),
        agents=[],
        snapshot_data=None,
        spec=SchedulingSpec(
            known_slot_types={},
            max_container_count=None,
        ),
    )


@pytest.fixture
def mock_config_provider() -> MagicMock:
    """Create mock config provider."""
    mock_config = MagicMock()
    mock_config.config.manager.agent_selection_resource_priority = ["cpu", "mem"]
    return mock_config


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Create mock repository."""
    return AsyncMock()


@pytest.fixture
def mock_fair_share_repository() -> MagicMock:
    """Create mock fair share repository."""
    return MagicMock()


@pytest.fixture
def mock_validator() -> MagicMock:
    """Create mock validator."""
    validator = MagicMock()
    validator.validate = MagicMock(return_value=None)
    return validator


@pytest.fixture
def mock_sequencer() -> MagicMock:
    """Create mock sequencer."""
    sequencer = MagicMock()
    sequencer.sequence = MagicMock(return_value=[])
    sequencer.name = "test-sequencer"
    sequencer.success_message = MagicMock(return_value="Sequencing succeeded")
    return sequencer


@pytest.fixture
def mock_agent_selector() -> MagicMock:
    """Create mock agent selector."""
    selector = MagicMock()
    selector.select_agents_for_batch_requirements = AsyncMock(return_value=[])
    selector.strategy_name = MagicMock(return_value="test-strategy")
    selector.strategy_success_message = MagicMock(return_value="Agent selection succeeded")
    return selector


@pytest.fixture
def mock_allocator() -> MagicMock:
    """Create mock allocator."""
    allocator = MagicMock()
    allocator.allocate = AsyncMock(return_value=[])
    allocator.name = MagicMock(return_value="test-allocator")
    allocator.success_message = MagicMock(return_value="Allocation succeeded")
    return allocator


@pytest.fixture
def mock_selector_pool() -> dict[AgentSelectionStrategy, MagicMock]:
    """Create mock selector pool for all strategies."""
    mock_selectors = {s: MagicMock(spec=AgentSelector) for s in AgentSelectionStrategy}

    for mock_selector in mock_selectors.values():
        mock_selector.select_agents_for_batch_requirements = AsyncMock(return_value=[])
        mock_selector.strategy_name = MagicMock(return_value="test-strategy")
        mock_selector.strategy_success_message = MagicMock(return_value="Selection succeeded")

    return mock_selectors


@pytest.fixture
def test_provisioner(
    mock_repository: AsyncMock,
    mock_fair_share_repository: MagicMock,
    mock_validator: MagicMock,
    mock_sequencer: MagicMock,
    mock_agent_selector: MagicMock,
    mock_allocator: MagicMock,
    mock_config_provider: MagicMock,
) -> SessionProvisioner:
    """Create SessionProvisioner with mock dependencies."""
    valkey_schedule = MagicMock()
    valkey_schedule.set_pending_queue = AsyncMock(return_value=None)
    valkey_schedule.get_multiple_session_failed_agents = AsyncMock(
        side_effect=lambda session_ids: [frozenset() for _ in session_ids]
    )

    return SessionProvisioner(
        SessionProvisionerArgs(
<<<<<<< HEAD
            validator=mock_validator,
            default_sequencer=mock_sequencer,
            default_agent_selector=mock_agent_selector,
            allocator=mock_allocator,
            repository=mock_repository,
            fair_share_repository=mock_fair_share_repository,
            config_provider=mock_config_provider,
=======
            validator=SchedulingValidator([
                DependenciesValidator(),
                ReservedBatchSessionValidator(),
                ResourcePolicyValidator(),
            ]),
            default_sequencer=FIFOSequencer(),
            agent_selector=create_agent_selector(["cpu", "mem"]),
            repository=repository,
            fair_share_repository=MagicMock(),
            config_provider=config_provider,
>>>>>>> 99e8e59f (fix(BA-7328): stop scheduling past a resource-exhausted session (#13707))
            valkey_schedule=valkey_schedule,
        )
    )


class TestScheduleScalingGroup:
    """Test schedule_scaling_group method."""

    @pytest.mark.parametrize(
        "strategy",
        [
            AgentSelectionStrategy.DISPERSED,
            AgentSelectionStrategy.CONCENTRATED,
            AgentSelectionStrategy.ROUNDROBIN,
            AgentSelectionStrategy.LEGACY,
        ],
    )
    async def test_uses_correct_agent_selector(
        self,
        strategy: AgentSelectionStrategy,
        test_provisioner: SessionProvisioner,
        mock_selector_pool: dict[AgentSelectionStrategy, MagicMock],
    ) -> None:
        """
        Verify that schedule_scaling_group uses correct agent_selector.
        """
        # Given: Override provisioner's selector pool with mock selectors
        test_provisioner._agent_selector_pool = mock_selector_pool

        # Given: SchedulingData with specific strategy
        scheduling_data = _create_scheduling_data_with_strategy(strategy)
        session_ids = [s.id for s in scheduling_data.pending_sessions.sessions]

        # When: Execute schedule_scaling_group within RecorderContext scope
        # (In production, coordinator opens the scope before calling provisioner)
        provision_time = datetime.now(tzutc())
        with RecorderContext[SessionId].scope("test-provisioning", entity_ids=session_ids):
            await test_provisioner.schedule_scaling_group(
                "test-sg", scheduling_data, provision_time
            )

        # Then: The selector for the specified strategy was used
        used_selector = mock_selector_pool[strategy]
        used_selector.select_agents_for_batch_requirements.assert_called()

<<<<<<< HEAD
        # And: Other selectors were not used
        for other_strategy, other_selector in mock_selector_pool.items():
            if other_strategy != strategy:
                other_selector.select_agents_for_batch_requirements.assert_not_called()
=======
class TestScheduleResourceGroup:
    async def test_successful_scheduling(
        self,
        provisioner: SessionProvisioner,
        repository: AsyncMock,
        valkey_schedule: AsyncMock,
        workload_factory: WorkloadFactory,
        scheduling_data_factory: SchedulingDataFactory,
    ) -> None:
        workload = workload_factory()
        data = scheduling_data_factory(workloads=[workload])

        result = await _schedule(provisioner, data, [workload])

        assert result.scheduled_session_ids == [workload.meta.session_id]
        assert result.scheduling_failures == []

        repository.allocate_sessions.assert_awaited_once()
        allocations = repository.allocate_sessions.await_args_list[0].args[0]
        assert len(allocations) == 1
        allocation = allocations[0]
        assert allocation.session_id == workload.meta.session_id
        assert [ka.kernel_id for ka in allocation.kernel_allocations] == [
            workload.placement.kernels[0].kernel_id
        ]
        assert allocation.kernel_allocations[0].agent_id == AgentId("agent-1")
        assert allocation.kernel_allocations[0].agent_addr == "agent-1:6001"

        valkey_schedule.set_pending_queue.assert_awaited_once_with(RESOURCE_GROUP_NAME, [])

    async def test_single_node_multi_kernel_lands_on_one_agent(
        self,
        provisioner: SessionProvisioner,
        repository: AsyncMock,
        workload_factory: WorkloadFactory,
        scheduling_data_factory: SchedulingDataFactory,
    ) -> None:
        workload = workload_factory(
            kernel_slots=[{"cpu": "2", "mem": "2048"}, {"cpu": "1", "mem": "1024"}]
        )
        data = scheduling_data_factory(workloads=[workload])

        result = await _schedule(provisioner, data, [workload])

        assert result.scheduled_session_ids == [workload.meta.session_id]
        allocation = repository.allocate_sessions.await_args_list[0].args[0][0]
        assert len(allocation.kernel_allocations) == 2
        assert {ka.kernel_id for ka in allocation.kernel_allocations} == {
            kernel.kernel_id for kernel in workload.placement.kernels
        }
        assert allocation.unique_agent_ids() == [AgentId("agent-1")]

    async def test_insufficient_resources_reports_failure(
        self,
        provisioner: SessionProvisioner,
        repository: AsyncMock,
        valkey_schedule: AsyncMock,
        workload_factory: WorkloadFactory,
        agent_meta_factory: AgentMetaFactory,
        scheduling_data_factory: SchedulingDataFactory,
    ) -> None:
        workload = workload_factory(kernel_slots=[{"cpu": "100", "mem": "999999"}])
        data = scheduling_data_factory(
            workloads=[workload],
            agents=[agent_meta_factory("agent-1", {"cpu": "4", "mem": "8192"})],
        )

        result = await _schedule(provisioner, data, [workload])

        assert result.scheduled_session_ids == []
        assert len(result.scheduling_failures) == 1
        failure = result.scheduling_failures[0]
        assert failure.session_id == workload.meta.session_id
        assert failure.msg

        # The failed session goes to the pending queue keyed by group name
        valkey_schedule.set_pending_queue.assert_awaited_once_with(
            RESOURCE_GROUP_NAME, [workload.meta.session_id]
        )
        # The allocation write still happens (with an empty batch)
        repository.allocate_sessions.assert_awaited_once_with([])

    async def test_partial_failure_keeps_other_sessions(
        self,
        provisioner: SessionProvisioner,
        repository: AsyncMock,
        workload_factory: WorkloadFactory,
        agent_meta_factory: AgentMetaFactory,
        scheduling_data_factory: SchedulingDataFactory,
    ) -> None:
        """A failure does not undo the sessions already scheduled in the pass."""
        fitting = workload_factory(kernel_slots=[{"cpu": "2", "mem": "2048"}])
        too_big = workload_factory(kernel_slots=[{"cpu": "100", "mem": "999999"}])
        data = scheduling_data_factory(
            workloads=[fitting, too_big],
            agents=[agent_meta_factory("agent-1", {"cpu": "4", "mem": "8192"})],
        )

        result = await _schedule(provisioner, data, [fitting, too_big])

        assert result.scheduled_session_ids == [fitting.meta.session_id]
        assert [f.session_id for f in result.scheduling_failures] == [too_big.meta.session_id]

    async def test_in_batch_occupancy_blocks_later_sessions(
        self,
        provisioner: SessionProvisioner,
        workload_factory: WorkloadFactory,
        agent_meta_factory: AgentMetaFactory,
        scheduling_data_factory: SchedulingDataFactory,
    ) -> None:
        """Earlier allocations of the pass are observed by later sessions."""
        first = workload_factory(kernel_slots=[{"cpu": "3", "mem": "6144"}])
        second = workload_factory(kernel_slots=[{"cpu": "3", "mem": "6144"}])
        data = scheduling_data_factory(
            workloads=[first, second],
            agents=[agent_meta_factory("agent-1", {"cpu": "4", "mem": "8192"})],
        )

        result = await _schedule(provisioner, data, [first, second])

        assert result.scheduled_session_ids == [first.meta.session_id]
        assert [f.session_id for f in result.scheduling_failures] == [second.meta.session_id]


class TestQueueBlockingOnResourceExhaustion:
    """Only a resource-exhausted session holds the queue back.

    Every other failure belongs to the session that hit it, so the sessions
    behind it must still be attempted.
    """

    async def test_exhausted_resources_skip_lower_priority_sessions(
        self,
        provisioner: SessionProvisioner,
        valkey_schedule: AsyncMock,
        workload_factory: WorkloadFactory,
        agent_meta_factory: AgentMetaFactory,
        scheduling_data_factory: SchedulingDataFactory,
    ) -> None:
        """A small low-priority session may not take what a big high-priority
        session is waiting for."""
        big = workload_factory(kernel_slots=[{"cpu": "8", "mem": "16384"}], priority=10)
        small = workload_factory(kernel_slots=[{"cpu": "1", "mem": "1024"}], priority=1)
        data = scheduling_data_factory(
            workloads=[small, big],
            agents=[agent_meta_factory("agent-1", {"cpu": "4", "mem": "8192"})],
        )

        result = await _schedule(provisioner, data, [small, big])

        assert result.scheduled_session_ids == []
        assert [f.session_id for f in result.scheduling_failures] == [big.meta.session_id]
        assert [s.session_id for s in result.scheduling_skips] == [small.meta.session_id]
        assert result.scheduling_skips[0].msg
        # Failed and skipped sessions alike stay in the pending queue, in
        # sequencing order
        valkey_schedule.set_pending_queue.assert_awaited_once_with(
            RESOURCE_GROUP_NAME, [big.meta.session_id, small.meta.session_id]
        )

    async def test_container_limit_exhaustion_skips_later_sessions(
        self,
        provisioner: SessionProvisioner,
        workload_factory: WorkloadFactory,
        agent_meta_factory: AgentMetaFactory,
        scheduling_data_factory: SchedulingDataFactory,
    ) -> None:
        """The per-agent container cap is a resource too: it blocks the queue."""
        first = workload_factory(priority=10)
        second = workload_factory(priority=1)
        data = scheduling_data_factory(
            workloads=[first, second],
            agents=[agent_meta_factory("agent-1")],
            max_container_count=0,
        )

        result = await _schedule(provisioner, data, [first, second])

        assert result.scheduled_session_ids == []
        assert [f.session_id for f in result.scheduling_failures] == [first.meta.session_id]
        assert [s.session_id for s in result.scheduling_skips] == [second.meta.session_id]

    async def test_incompatible_architecture_does_not_block_later_sessions(
        self,
        provisioner: SessionProvisioner,
        workload_factory: WorkloadFactory,
        scheduling_data_factory: SchedulingDataFactory,
    ) -> None:
        """A session no agent can ever host would block the queue forever."""
        foreign = workload_factory(architecture="aarch64", priority=10)
        fitting = workload_factory(priority=1)
        data = scheduling_data_factory(workloads=[foreign, fitting])

        result = await _schedule(provisioner, data, [foreign, fitting])

        assert result.scheduled_session_ids == [fitting.meta.session_id]
        assert [f.session_id for f in result.scheduling_failures] == [foreign.meta.session_id]
        assert result.scheduling_skips == []

    async def test_empty_resource_group_does_not_block_later_sessions(
        self,
        provisioner: SessionProvisioner,
        workload_factory: WorkloadFactory,
        scheduling_data_factory: SchedulingDataFactory,
    ) -> None:
        """With no agents at all every session fails on its own account."""
        first = workload_factory(priority=10)
        second = workload_factory(priority=1)
        data = scheduling_data_factory(workloads=[first, second], agents=[])

        result = await _schedule(provisioner, data, [first, second])

        assert result.scheduled_session_ids == []
        assert [f.session_id for f in result.scheduling_failures] == [
            first.meta.session_id,
            second.meta.session_id,
        ]
        assert result.scheduling_skips == []

    async def test_reserved_batch_session_does_not_block_later_sessions(
        self,
        provisioner: SessionProvisioner,
        workload_factory: WorkloadFactory,
        scheduling_data_factory: SchedulingDataFactory,
    ) -> None:
        """A batch session starting in an hour must not stall the group for an hour."""
        later = workload_factory(
            priority=10,
            session_type=SessionTypes.BATCH,
            requested_starts_at=datetime.now(UTC) + timedelta(hours=1),
        )
        fitting = workload_factory(priority=1)
        data = scheduling_data_factory(workloads=[later, fitting])

        result = await _schedule(provisioner, data, [later, fitting])

        assert result.scheduled_session_ids == [fitting.meta.session_id]
        assert [f.session_id for f in result.scheduling_failures] == [later.meta.session_id]
        assert result.scheduling_skips == []

    async def test_unsatisfied_dependency_does_not_block_later_sessions(
        self,
        provisioner: SessionProvisioner,
        workload_factory: WorkloadFactory,
        scheduling_data_factory: SchedulingDataFactory,
    ) -> None:
        """The session it depends on may be the one queued behind it."""
        waiting = workload_factory(priority=10)
        fitting = workload_factory(priority=1)
        data = scheduling_data_factory(
            workloads=[waiting, fitting],
            session_dependencies={
                waiting.meta.session_id: [
                    SessionDependencyInfo(
                        depends_on=fitting.meta.session_id,
                        dependency_name="upstream",
                        dependency_status=SessionStatus.RUNNING,
                        dependency_result=SessionResult.UNDEFINED,
                    )
                ]
            },
        )

        result = await _schedule(provisioner, data, [waiting, fitting])

        assert result.scheduled_session_ids == [fitting.meta.session_id]
        assert [f.session_id for f in result.scheduling_failures] == [waiting.meta.session_id]
        assert result.scheduling_skips == []

    async def test_quota_exceeded_does_not_block_other_users(
        self,
        provisioner: SessionProvisioner,
        workload_factory: WorkloadFactory,
        scheduling_data_factory: SchedulingDataFactory,
    ) -> None:
        """One user over quota must not stall the whole resource group."""
        over_quota = workload_factory(kernel_slots=[{"cpu": "2", "mem": "2048"}], priority=10)
        fitting = workload_factory(priority=1)
        data = scheduling_data_factory(
            workloads=[over_quota, fitting],
            resource_policy=ResourcePolicySnapshot(
                by_user={
                    over_quota.meta.owner.user_uuid: UserResourceLimit(
                        slots={ResourceSlotName("cpu"): Decimal(1)},
                        max_session_count=None,
                        max_sftp_session_count=None,
                    )
                },
                by_project={},
                by_domain={},
            ),
        )

        result = await _schedule(provisioner, data, [over_quota, fitting])

        assert result.scheduled_session_ids == [fitting.meta.session_id]
        assert [f.session_id for f in result.scheduling_failures] == [over_quota.meta.session_id]
        assert result.scheduling_skips == []
>>>>>>> 99e8e59f (fix(BA-7328): stop scheduling past a resource-exhausted session (#13707))
