"""Tests for SessionProvisioner (PENDING -> SCHEDULED pipeline)."""

from __future__ import annotations

from collections.abc import Sequence
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import AgentId, SessionId
from ai.backend.manager.sokovan.recorder import RecorderContext
from ai.backend.manager.sokovan.scheduler.provisioner.provisioner import (
    SchedulingState,
    SessionProvisioner,
    SessionProvisionerArgs,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.concentrated import (
    ConcentratedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import AgentSelector
from ai.backend.manager.sokovan.scheduler.provisioner.sequencers.fifo import FIFOSequencer
from ai.backend.manager.sokovan.scheduler.provisioner.validators.dependencies import (
    DependenciesValidator,
)
from ai.backend.manager.sokovan.scheduler.provisioner.validators.validator import (
    SchedulingValidator,
)
from ai.backend.manager.sokovan.scheduler.results import ScheduleResult
from ai.backend.manager.views.sokovan.allocation import SessionAllocation
from ai.backend.manager.views.sokovan.scheduling import SchedulingData
from ai.backend.manager.views.sokovan.workload import SessionWorkload

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
            validator=SchedulingValidator([DependenciesValidator()]),
            default_sequencer=FIFOSequencer(),
            default_agent_selector=AgentSelector(
                ConcentratedAgentSelector(agent_selection_resource_priority=["cpu", "mem"])
            ),
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
        """One session failing does not abort the other sessions of the pass."""
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
