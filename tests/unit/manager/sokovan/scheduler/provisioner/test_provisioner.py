"""Tests for SessionProvisioner (PENDING -> SCHEDULED pipeline)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import AgentId, SessionId, SessionResult, SessionTypes
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.sokovan.recorder import RecorderContext
from ai.backend.manager.sokovan.scheduler.provisioner.provisioner import (
    SchedulingState,
    SessionProvisioner,
    SessionProvisionerArgs,
)
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
)


def _make_provisioner(
    repository: AsyncMock,
    valkey_schedule: AsyncMock,
) -> SessionProvisioner:
    config_provider = MagicMock()
    config_provider.config.manager.agent_selection_resource_priority = ["cpu", "mem"]
    return SessionProvisioner(
        SessionProvisionerArgs(
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
            valkey_schedule=valkey_schedule,
        )
    )


@pytest.fixture
def repository() -> AsyncMock:
    repo = AsyncMock()

    def _allocate(allocations: Sequence[SessionAllocation]) -> list[SessionId]:
        return [allocation.session_id for allocation in allocations]

    repo.allocate_sessions.side_effect = _allocate
    return repo


@pytest.fixture
def valkey_schedule() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def provisioner(repository: AsyncMock, valkey_schedule: AsyncMock) -> SessionProvisioner:
    return _make_provisioner(repository, valkey_schedule)


async def _schedule(
    provisioner: SessionProvisioner,
    scheduling_data: SchedulingData,
    workloads: list[SessionWorkload],
) -> ScheduleResult:
    with RecorderContext[SessionId].scope(
        "schedule", entity_ids=[w.meta.session_id for w in workloads]
    ):
        return await provisioner.schedule_resource_group(scheduling_data)


class TestSchedulingState:
    def test_from_scheduling_data_builds_trackers(
        self,
        workload_factory: WorkloadFactory,
        agent_meta_factory: AgentMetaFactory,
        scheduling_data_factory: SchedulingDataFactory,
    ) -> None:
        data = scheduling_data_factory(
            workloads=[workload_factory()],
            agents=[agent_meta_factory("agent-1"), agent_meta_factory("agent-2")],
        )

        state = SchedulingState.from_scheduling_data(data)

        assert state.snapshot is data.system_snapshot
        assert state.resource_group is data.resource_group
        assert len(state.trackers) == 2
        assert {t.original_agent.agent_id for t in state.trackers} == {
            AgentId("agent-1"),
            AgentId("agent-2"),
        }


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
