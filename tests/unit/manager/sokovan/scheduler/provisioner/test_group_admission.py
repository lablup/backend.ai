"""All-or-none admission of a session group in the provisioner (BEP-1083)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import SessionId
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.sokovan.scheduler.provisioner.provisioner import (
    SessionProvisioner,
    SessionProvisionerArgs,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selection import create_agent_selector
from ai.backend.manager.sokovan.scheduler.provisioner.sequencers.fifo import FIFOSequencer
from ai.backend.manager.sokovan.scheduler.provisioner.validators.validator import (
    SchedulingValidator,
)
from ai.backend.manager.sokovan.scheduler.results import ScheduleResult
from ai.backend.manager.views.sokovan.allocation import SessionAllocation
from ai.backend.manager.views.sokovan.scheduling import SchedulingData
from ai.backend.manager.views.sokovan.workload import GroupAdmission, SessionWorkload

from .conftest import AgentMetaFactory, SchedulingDataFactory, WorkloadFactory


@pytest.fixture
def repository() -> AsyncMock:
    repo = AsyncMock()

    def _allocate(allocations: Sequence[SessionAllocation]) -> list[SessionId]:
        return [allocation.session_id for allocation in allocations]

    repo.allocate_sessions.side_effect = _allocate
    return repo


@pytest.fixture
def provisioner(repository: AsyncMock) -> SessionProvisioner:
    return SessionProvisioner(
        SessionProvisionerArgs(
            validator=SchedulingValidator([]),
            default_sequencer=FIFOSequencer(),
            agent_selector=create_agent_selector(["cpu", "mem"]),
            repository=repository,
            fair_share_repository=MagicMock(),
            config_provider=MagicMock(),
            valkey_schedule=AsyncMock(),
        )
    )


@pytest.fixture
def group_of_two() -> GroupAdmission:
    return GroupAdmission(group_id=SessionGroupID(uuid.uuid4()), member_count=2)


@pytest.fixture
def group_of_three() -> GroupAdmission:
    return GroupAdmission(group_id=SessionGroupID(uuid.uuid4()), member_count=3)


async def _schedule(provisioner: SessionProvisioner, data: SchedulingData) -> ScheduleResult:
    with RecorderContext[SessionId].scope(
        "schedule", entity_ids=[w.meta.session_id for w in data.workloads]
    ):
        return await provisioner.schedule_resource_group(data)


def _ids(workloads: Sequence[SessionWorkload]) -> list[SessionId]:
    return [w.meta.session_id for w in workloads]


class TestHold:
    async def test_members_below_the_member_count_wait(
        self,
        provisioner: SessionProvisioner,
        repository: AsyncMock,
        workload_factory: WorkloadFactory,
        scheduling_data_factory: SchedulingDataFactory,
        group_of_three: GroupAdmission,
    ) -> None:
        members = [workload_factory(group_admission=group_of_three) for _ in range(2)]

        result = await _schedule(provisioner, scheduling_data_factory(workloads=members))

        assert result.scheduled_session_ids == []
        assert result.scheduling_failures == []
        assert [(s.session_id, s.msg) for s in result.scheduling_skips] == [
            (session_id, KernelLifecycleEventReason.WAITING_FOR_GROUP_MEMBERS)
            for session_id in _ids(members)
        ]
        repository.mark_pending_sessions_status_info.assert_awaited_once_with(
            _ids(members), KernelLifecycleEventReason.WAITING_FOR_GROUP_MEMBERS
        )

    async def test_a_held_group_does_not_block_other_sessions(
        self,
        provisioner: SessionProvisioner,
        workload_factory: WorkloadFactory,
        scheduling_data_factory: SchedulingDataFactory,
        group_of_three: GroupAdmission,
    ) -> None:
        held = workload_factory(group_admission=group_of_three)
        single = workload_factory()

        result = await _schedule(provisioner, scheduling_data_factory(workloads=[held, single]))

        assert result.scheduled_session_ids == [single.meta.session_id]


class TestAdmission:
    async def test_members_that_fit_are_admitted_together(
        self,
        provisioner: SessionProvisioner,
        repository: AsyncMock,
        workload_factory: WorkloadFactory,
        scheduling_data_factory: SchedulingDataFactory,
        group_of_two: GroupAdmission,
    ) -> None:
        members = [workload_factory(group_admission=group_of_two) for _ in range(2)]

        result = await _schedule(provisioner, scheduling_data_factory(workloads=members))

        assert sorted(result.scheduled_session_ids) == sorted(_ids(members))
        repository.mark_pending_sessions_status_info.assert_not_awaited()

    async def test_a_group_takes_the_position_of_its_first_member(
        self,
        provisioner: SessionProvisioner,
        repository: AsyncMock,
        workload_factory: WorkloadFactory,
        scheduling_data_factory: SchedulingDataFactory,
        group_of_two: GroupAdmission,
    ) -> None:
        first = workload_factory(group_admission=group_of_two)
        single = workload_factory()
        last = workload_factory(group_admission=group_of_two)

        await _schedule(provisioner, scheduling_data_factory(workloads=[first, single, last]))

        allocations = repository.allocate_sessions.await_args.args[0]
        assert [a.session_id for a in allocations] == _ids([first, last, single])

    async def test_no_member_is_admitted_when_one_does_not_fit(
        self,
        provisioner: SessionProvisioner,
        workload_factory: WorkloadFactory,
        agent_meta_factory: AgentMetaFactory,
        scheduling_data_factory: SchedulingDataFactory,
        group_of_two: GroupAdmission,
    ) -> None:
        members = [
            workload_factory(group_admission=group_of_two, kernel_slots=[{"cpu": "3"}])
            for _ in range(2)
        ]

        result = await _schedule(
            provisioner,
            scheduling_data_factory(
                workloads=members, agents=[agent_meta_factory("agent-1", {"cpu": "4"})]
            ),
        )

        assert result.scheduled_session_ids == []
        assert [f.session_id for f in result.scheduling_failures] == _ids(members)
        reasons = {f.msg for f in result.scheduling_failures}
        assert len(reasons) == 1
        assert str(group_of_two.group_id) in reasons.pop()

    async def test_a_failed_group_releases_what_its_first_member_took(
        self,
        provisioner: SessionProvisioner,
        workload_factory: WorkloadFactory,
        agent_meta_factory: AgentMetaFactory,
        scheduling_data_factory: SchedulingDataFactory,
        group_of_two: GroupAdmission,
    ) -> None:
        # The second member fits no agent's architecture, which does not stall the
        # queue; the session behind needs the whole agent the first member took.
        members = [
            workload_factory(group_admission=group_of_two, kernel_slots=[{"cpu": "2"}]),
            workload_factory(
                group_admission=group_of_two, kernel_slots=[{"cpu": "2"}], architecture="aarch64"
            ),
        ]
        whole_agent = workload_factory(kernel_slots=[{"cpu": "4"}])

        result = await _schedule(
            provisioner,
            scheduling_data_factory(
                workloads=[*members, whole_agent],
                agents=[agent_meta_factory("agent-1", {"cpu": "4"})],
            ),
        )

        assert result.scheduled_session_ids == [whole_agent.meta.session_id]
        assert [f.session_id for f in result.scheduling_failures] == _ids(members)
