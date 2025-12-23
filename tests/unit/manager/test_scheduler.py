from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from decimal import Decimal
from pprint import pprint
from typing import Any
from unittest import mock
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import pytest_mock
import trafaret as t
from dateutil.parser import parse as dtparse
from dateutil.tz import tzutc

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    AgentSelectionStrategy,
    ResourceSlot,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.schedule.repository import ScheduleRepository
from ai.backend.manager.scheduler.agent_selector import (
    DispersedAgentSelector,
)
from ai.backend.manager.scheduler.dispatcher import (
    SchedulerDispatcher,
    load_scheduler,
)
from ai.backend.manager.scheduler.drf import DRFScheduler
from ai.backend.manager.scheduler.fifo import FIFOSlotScheduler, LIFOSlotScheduler
from ai.backend.manager.scheduler.predicates import check_reserved_batch_session
from ai.backend.manager.scheduler.types import InMemoryResourceGroupStateStore

from .scheduler_utils import (
    KernelOpt,
    agent_selection_resource_priority,
    create_mock_agent,
    create_mock_session,
    example_sgroup_name1,
    example_sgroup_name2,
    find_and_pop_picked_session,
)


def test_load_intrinsic() -> None:
    default_sgroup_opts = ScalingGroupOpts()
    assert isinstance(
        load_scheduler("fifo", default_sgroup_opts, {}),
        FIFOSlotScheduler,
    )
    assert isinstance(
        load_scheduler("lifo", default_sgroup_opts, {}),
        LIFOSlotScheduler,
    )
    assert isinstance(
        load_scheduler("drf", default_sgroup_opts, {}),
        DRFScheduler,
    )


def test_scheduler_configs() -> None:
    example_sgroup_opts = ScalingGroupOpts(  # already processed by column trafaret
        allowed_session_types=[SessionTypes.BATCH],
        pending_timeout=timedelta(seconds=86400 * 2),
        agent_selection_strategy=AgentSelectionStrategy.DISPERSED,
        config={
            "extra_config": None,
            "num_retries_to_skip": 5,
        },
    )
    scheduler = load_scheduler("fifo", example_sgroup_opts, example_sgroup_opts.config)
    assert isinstance(scheduler, FIFOSlotScheduler)
    assert scheduler.config == {
        "extra_config": None,
        "num_retries_to_skip": 5,
    }
    with pytest.raises(t.DataError):
        example_sgroup_opts.config["num_retries_to_skip"] = -1  # type: ignore
        scheduler = load_scheduler(
            "fifo",
            example_sgroup_opts,
            example_sgroup_opts.config,
        )


def create_example_agents() -> Sequence[AgentRow]:
    return [
        create_mock_agent(
            AgentId("i-001"),
            scaling_group=example_sgroup_name1,
            available_slots=ResourceSlot({
                "cpu": Decimal(4),
                "mem": Decimal(4096),
                "cuda.shares": Decimal(4),
                "rocm.devices": Decimal(2),
            }),
        ),
        create_mock_agent(
            AgentId("i-101"),
            scaling_group=example_sgroup_name2,
            available_slots=ResourceSlot({
                "cpu": Decimal(3),
                "mem": Decimal(2560),
                "cuda.shares": Decimal(1),
                "rocm.devices": Decimal(8),
            }),
        ),
    ]


def create_example_mixed_agents() -> Sequence[AgentRow]:
    return [
        create_mock_agent(
            AgentId("i-gpu"),
            scaling_group=example_sgroup_name1,
            available_slots=ResourceSlot({
                "cpu": Decimal(4),
                "mem": Decimal(4096),
                "cuda.shares": Decimal(4),
            }),
        ),
        create_mock_agent(
            AgentId("i-cpu"),
            scaling_group=example_sgroup_name2,
            available_slots=ResourceSlot({
                "cpu": Decimal(3),
                "mem": Decimal(2560),
                "cuda.shares": Decimal(0),
            }),
        ),
    ]


def create_example_pending_sessions() -> Sequence[SessionRow]:
    return [
        create_mock_session(  # rocm
            SessionId(uuid4()),
            access_key=AccessKey("user01"),
            requested_slots=ResourceSlot({
                "cpu": Decimal(2),
                "mem": Decimal(1024),
                "cuda.shares": Decimal(0),
                "rocm.devices": Decimal(1),
            }),
        ),
        create_mock_session(  # cuda
            SessionId(uuid4()),
            access_key=AccessKey("user02"),
            requested_slots=ResourceSlot({
                "cpu": Decimal(1),
                "mem": Decimal(2048),
                "cuda.shares": Decimal("0.5"),
                "rocm.devices": Decimal(0),
            }),
        ),
        create_mock_session(  # cpu-only, single-node cluster
            SessionId(uuid4()),
            access_key=AccessKey("user03"),
            requested_slots=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal(1024)}),
            kernel_opts=[
                KernelOpt(ResourceSlot({"cpu": Decimal("0.4"), "mem": Decimal(512)})),
                KernelOpt(ResourceSlot({"cpu": Decimal("0.3"), "mem": Decimal(256)})),
                KernelOpt(ResourceSlot({"cpu": Decimal("0.3"), "mem": Decimal(256)})),
            ],
        ),
    ]


def create_example_existing_sessions() -> Sequence[SessionRow]:
    return [
        create_mock_session(
            SessionId(uuid4()),
            status=SessionStatus.RUNNING,
            access_key=AccessKey("user01"),
            requested_slots=ResourceSlot({
                "cpu": Decimal(3),
                "mem": Decimal(1024),
                "cuda.shares": Decimal(0),
                "rocm.devices": Decimal(1),
            }),
            kernel_opts=[
                KernelOpt(
                    ResourceSlot({
                        "cpu": Decimal(1),
                        "mem": Decimal(512),
                        "cuda.shares": Decimal(0),
                        "rocm.devices": Decimal(0),
                    })
                ),
                KernelOpt(
                    ResourceSlot({
                        "cpu": Decimal(2),
                        "mem": Decimal(512),
                        "cuda.shares": Decimal(0),
                        "rocm.devices": Decimal(1),
                    })
                ),
            ],
        ),
        create_mock_session(
            SessionId(uuid4()),
            status=SessionStatus.RUNNING,
            access_key=AccessKey("user02"),
            requested_slots=ResourceSlot({
                "cpu": Decimal(1),
                "mem": Decimal(2048),
                "cuda.shares": Decimal("0.5"),
                "rocm.devices": Decimal(0),
            }),
        ),
        create_mock_session(
            SessionId(uuid4()),
            status=SessionStatus.RUNNING,
            access_key=AccessKey("user03"),
            requested_slots=ResourceSlot({
                "cpu": Decimal(4),
                "mem": Decimal(4096),
                "cuda.shares": Decimal(0),
                "rocm.devices": Decimal(0),
            }),
        ),
    ]


@pytest.mark.asyncio
async def test_fifo_scheduler() -> None:
    example_agents = create_example_agents()
    example_pending_sessions = create_example_pending_sessions()
    example_existing_sessions = create_example_existing_sessions()
    scheduler = FIFOSlotScheduler(ScalingGroupOpts(), {})
    agstate_cls = DispersedAgentSelector.get_state_cls()
    agselector = DispersedAgentSelector(
        ScalingGroupOpts(),
        {},
        agent_selection_resource_priority,
        state_store=InMemoryResourceGroupStateStore(agstate_cls),
    )
    picked_session_id = scheduler.pick_session(
        sum((ag.available_slots for ag in example_agents), start=ResourceSlot()),
        example_pending_sessions,
        example_existing_sessions,
    )
    assert picked_session_id == example_pending_sessions[0].id
    picked_session = find_and_pop_picked_session(
        example_pending_sessions,
        picked_session_id,
    )
    agent_id = await agselector.assign_agent_for_session(
        example_agents,
        picked_session,
    )
    assert agent_id == AgentId("i-001")


@pytest.mark.asyncio
async def test_lifo_scheduler() -> None:
    example_agents = create_example_agents()
    example_pending_sessions = create_example_pending_sessions()
    example_existing_sessions = create_example_existing_sessions()
    scheduler = LIFOSlotScheduler(ScalingGroupOpts(), {})
    agstate_cls = DispersedAgentSelector.get_state_cls()
    agselector = DispersedAgentSelector(
        ScalingGroupOpts(),
        {},
        agent_selection_resource_priority,
        state_store=InMemoryResourceGroupStateStore(agstate_cls),
    )
    picked_session_id = scheduler.pick_session(
        sum((ag.available_slots for ag in example_agents), start=ResourceSlot()),
        example_pending_sessions,
        example_existing_sessions,
    )
    assert picked_session_id == example_pending_sessions[2].id
    picked_session = find_and_pop_picked_session(
        example_pending_sessions,
        picked_session_id,
    )
    agent_id = await agselector.assign_agent_for_session(
        example_agents,
        picked_session,
    )
    assert agent_id == "i-001"


@pytest.mark.asyncio
async def test_fifo_scheduler_favor_cpu_for_requests_without_accelerators() -> None:
    example_mixed_agents = create_example_mixed_agents()
    example_pending_sessions = create_example_pending_sessions()
    scheduler = FIFOSlotScheduler(ScalingGroupOpts(), {})
    agstate_cls = DispersedAgentSelector.get_state_cls()
    agselector = DispersedAgentSelector(
        ScalingGroupOpts(),
        {},
        agent_selection_resource_priority,
        state_store=InMemoryResourceGroupStateStore(agstate_cls),
    )
    total_capacity = sum((ag.available_slots for ag in example_mixed_agents), start=ResourceSlot())
    for idx in range(3):
        picked_session_id = scheduler.pick_session(
            total_capacity,
            example_pending_sessions,
            [],
        )
        assert picked_session_id == example_pending_sessions[0].id
        picked_session = find_and_pop_picked_session(
            example_pending_sessions,
            picked_session_id,
        )
        agent_id = await agselector.assign_agent_for_session(
            example_mixed_agents,
            picked_session,
        )
        if idx == 0:
            # example_mixed_agents do not have any agent with ROCM accelerators.
            assert agent_id is None
        elif idx == 1:
            assert agent_id == AgentId("i-gpu")
        elif idx == 2:
            # It should favor the CPU-only agent if the requested slots
            # do not include accelerators.
            assert agent_id == AgentId("i-cpu")


_holb_capacity = ResourceSlot({"cpu": Decimal(4), "mem": Decimal(4096)})
_holb_session_ids = {
    "s0": SessionId(uuid4()),
    "s1": SessionId(uuid4()),
    "s2": SessionId(uuid4()),
}


def create_pending_session_holb(
    session_id: SessionId,
    status_data: dict[str, Any],
) -> SessionRow:
    return create_mock_session(
        session_id,
        status=SessionStatus.PENDING,
        status_data=status_data,
        access_key=AccessKey("ak1"),
        requested_slots=ResourceSlot({"cpu": Decimal(1), "mem": Decimal(1024)}),
    )


def test_fifo_scheduler_hol_blocking_avoidance_empty_status_data() -> None:
    """
    Without any status_data, it should just pick the first session.
    """
    scheduler = FIFOSlotScheduler(ScalingGroupOpts(), {"num_retries_to_skip": 5})
    pending_sessions = [
        create_pending_session_holb(_holb_session_ids["s0"], {}),
        create_pending_session_holb(_holb_session_ids["s1"], {}),
        create_pending_session_holb(_holb_session_ids["s2"], {}),
    ]
    picked_session_id = scheduler.pick_session(_holb_capacity, pending_sessions, [])
    assert picked_session_id == _holb_session_ids["s0"]


def test_fifo_scheduler_hol_blocking_avoidance_config() -> None:
    """
    If the upfront sessions have enough number of retries,
    it should skip them.
    """
    scheduler = FIFOSlotScheduler(ScalingGroupOpts(), {"num_retries_to_skip": 0})
    pending_sessions = [
        create_pending_session_holb(_holb_session_ids["s0"], {"scheduler": {"retries": 5}}),
        create_pending_session_holb(_holb_session_ids["s1"], {}),
        create_pending_session_holb(_holb_session_ids["s2"], {}),
    ]
    picked_session_id = scheduler.pick_session(_holb_capacity, pending_sessions, [])
    assert picked_session_id == _holb_session_ids["s0"]

    scheduler = FIFOSlotScheduler(ScalingGroupOpts(), {"num_retries_to_skip": 5})
    pending_sessions = [
        create_pending_session_holb(_holb_session_ids["s0"], {"scheduler": {"retries": 5}}),
        create_pending_session_holb(_holb_session_ids["s1"], {"scheduler": {"retries": 4}}),
        create_pending_session_holb(_holb_session_ids["s2"], {"scheduler": {"retries": 3}}),
    ]
    picked_session_id = scheduler.pick_session(_holb_capacity, pending_sessions, [])
    assert picked_session_id == _holb_session_ids["s1"]


def test_fifo_scheduler_hol_blocking_avoidance_skips() -> None:
    """
    If the upfront sessions have enough number of retries,
    it should skip them.
    """
    scheduler = FIFOSlotScheduler(ScalingGroupOpts(), {"num_retries_to_skip": 5})
    pending_sessions = [
        create_pending_session_holb(_holb_session_ids["s0"], {"scheduler": {"retries": 5}}),
        create_pending_session_holb(_holb_session_ids["s1"], {}),
        create_pending_session_holb(_holb_session_ids["s2"], {}),
    ]
    picked_session_id = scheduler.pick_session(_holb_capacity, pending_sessions, [])
    assert picked_session_id == _holb_session_ids["s1"]

    pending_sessions = [
        create_pending_session_holb(_holb_session_ids["s0"], {"scheduler": {"retries": 5}}),
        create_pending_session_holb(_holb_session_ids["s1"], {"scheduler": {"retries": 10}}),
        create_pending_session_holb(_holb_session_ids["s2"], {}),
    ]
    picked_session_id = scheduler.pick_session(_holb_capacity, pending_sessions, [])
    assert picked_session_id == _holb_session_ids["s2"]


def test_fifo_scheduler_hol_blocking_avoidance_all_skipped() -> None:
    """
    If all sessions are skipped due to excessive number of retries,
    then we go back to the normal FIFO by choosing the first of them.
    """
    scheduler = FIFOSlotScheduler(ScalingGroupOpts(), {"num_retries_to_skip": 5})
    pending_sessions = [
        create_pending_session_holb(_holb_session_ids["s0"], {"scheduler": {"retries": 5}}),
        create_pending_session_holb(_holb_session_ids["s1"], {"scheduler": {"retries": 5}}),
        create_pending_session_holb(_holb_session_ids["s2"], {"scheduler": {"retries": 5}}),
    ]
    picked_session_id = scheduler.pick_session(_holb_capacity, pending_sessions, [])
    assert picked_session_id == _holb_session_ids["s0"]


def test_fifo_scheduler_hol_blocking_avoidance_no_skip() -> None:
    """
    If non-first sessions have to be skipped, the scheduler should still
    choose the first session.
    """
    scheduler = FIFOSlotScheduler(ScalingGroupOpts(), {"num_retries_to_skip": 5})
    pending_sessions = [
        create_pending_session_holb(_holb_session_ids["s0"], {}),
        create_pending_session_holb(_holb_session_ids["s1"], {"scheduler": {"retries": 10}}),
        create_pending_session_holb(_holb_session_ids["s2"], {}),
    ]
    picked_session_id = scheduler.pick_session(_holb_capacity, pending_sessions, [])
    assert picked_session_id == _holb_session_ids["s0"]


@pytest.mark.asyncio
async def test_lifo_scheduler_favor_cpu_for_requests_without_accelerators() -> None:
    example_mixed_agents = create_example_mixed_agents()
    example_pending_sessions = create_example_pending_sessions()
    # Check the reverse with the LIFO scheduler.
    # The result must be same.
    sgroup_opts = ScalingGroupOpts(agent_selection_strategy=AgentSelectionStrategy.DISPERSED)
    scheduler = LIFOSlotScheduler(sgroup_opts, {})
    agstate_cls = DispersedAgentSelector.get_state_cls()
    agselector = DispersedAgentSelector(
        sgroup_opts,
        {},
        agent_selection_resource_priority,
        state_store=InMemoryResourceGroupStateStore(agstate_cls),
    )
    total_capacity = sum((ag.available_slots for ag in example_mixed_agents), start=ResourceSlot())
    for idx in range(3):
        picked_session_id = scheduler.pick_session(total_capacity, example_pending_sessions, [])
        assert picked_session_id == example_pending_sessions[-1].id
        picked_session = find_and_pop_picked_session(example_pending_sessions, picked_session_id)
        agent_id = await agselector.assign_agent_for_session(
            example_mixed_agents,
            picked_session,
        )
        if idx == 2:
            # example_mixed_agents do not have any agent with ROCM accelerators.
            assert agent_id is None
        elif idx == 1:
            assert agent_id == AgentId("i-gpu")
        elif idx == 0:
            # It should favor the CPU-only agent if the requested slots
            # do not include accelerators.
            assert agent_id == AgentId("i-cpu")


@pytest.mark.asyncio
async def test_drf_scheduler() -> None:
    example_agents = create_example_agents()
    example_pending_sessions = create_example_pending_sessions()
    example_existing_sessions = create_example_existing_sessions()
    sgroup_opts = ScalingGroupOpts(agent_selection_strategy=AgentSelectionStrategy.DISPERSED)
    scheduler = DRFScheduler(sgroup_opts, {})
    agstate_cls = DispersedAgentSelector.get_state_cls()
    agselector = DispersedAgentSelector(
        sgroup_opts,
        {},
        agent_selection_resource_priority,
        state_store=InMemoryResourceGroupStateStore(agstate_cls),
    )
    picked_session_id = scheduler.pick_session(
        sum((ag.available_slots for ag in example_agents), start=ResourceSlot()),
        example_pending_sessions,
        example_existing_sessions,
    )
    pprint(example_pending_sessions)
    assert picked_session_id == example_pending_sessions[1].id
    picked_session = find_and_pop_picked_session(
        example_pending_sessions,
        picked_session_id,
    )
    agent_id = await agselector.assign_agent_for_session(
        example_agents,
        picked_session,
    )
    assert agent_id == "i-001"


@pytest.mark.asyncio
async def test_pending_timeout() -> None:
    class DummySession:
        def __init__(self, id, created_at, status) -> None:
            self.id = id
            self.created_at = created_at
            self.status = status

    now = datetime.now(tzutc())
    mock_query_result = MagicMock()
    mock_query_result.scalars = MagicMock()
    mock_query_result.scalars().all = MagicMock(
        return_value=[
            DummySession(
                id="session3",
                # created_at=datetime(2020, 12, 31, 23, 59, 59),
                created_at=now,
                status=SessionStatus.PENDING,
            ),
            DummySession(
                id="session2",
                # created_at=datetime(2020, 12, 30, 23, 59, 59),
                created_at=now - timedelta(seconds=86400),
                status=SessionStatus.PENDING,
            ),
            DummySession(
                id="session1",
                # created_at=datetime(2020, 12, 29, 23, 59, 59),
                created_at=now - timedelta(seconds=86400 * 3),
                status=SessionStatus.PENDING,
            ),
        ]
    )
    mock_dbsess = MagicMock()
    mock_dbsess.execute = AsyncMock(return_value=mock_query_result)

    scheduler = FIFOSlotScheduler(
        ScalingGroupOpts(pending_timeout=timedelta(seconds=86400 * 2)),
        {},
    )
    from unittest.mock import Mock

    repository = ScheduleRepository(db=Mock(), valkey_stat=Mock(), config_provider=Mock())
    _, candidate_session_rows, cancelled_session_rows = await repository._list_managed_sessions(
        mock_dbsess,
        "default",
        pending_timeout=scheduler.sgroup_opts.pending_timeout,
    )
    assert len(candidate_session_rows) == 2
    assert len(cancelled_session_rows) == 1
    assert cancelled_session_rows[0].id == "session1"

    scheduler = FIFOSlotScheduler(
        ScalingGroupOpts(pending_timeout=timedelta(seconds=0)),
        {},
    )
    _, candidate_session_rows, cancelled_session_rows = await repository._list_managed_sessions(
        mock_dbsess,
        "default",
        pending_timeout=scheduler.sgroup_opts.pending_timeout,
    )
    assert len(candidate_session_rows) == 3
    assert len(cancelled_session_rows) == 0


class DummyEtcd:
    async def get_prefix(self, key: str) -> Mapping[str, Any]:
        return {}

    async def get(self, key: str) -> Any:
        return None


@pytest.mark.asyncio
async def test_manually_assign_agent_available(
    file_lock_factory,
    registry_ctx: tuple[
        AgentRegistry, MagicMock, MagicMock, MagicMock, MagicMock, MagicMock, MagicMock
    ],
    mocker: pytest_mock.MockerFixture,
) -> None:
    example_agents = create_example_agents()
    example_pending_sessions = create_example_pending_sessions()

    (
        registry,
        mock_dbconn,
        mock_dbsess,
        mock_dbresult,
        mock_config_provider,
        mock_event_dispatcher,
        mock_event_producer,
    ) = registry_ctx
    mock_sched_ctx = MagicMock()
    mock_check_result = MagicMock()
    # Mock the recalc_concurrency_used function since it uses ValkeyStatClient
    mock_recalc_concurrency_used = AsyncMock()
    mocker.patch(
        "ai.backend.manager.repositories.schedule.repository.recalc_concurrency_used",
        mock_recalc_concurrency_used,
    )
    sgroup_opts = ScalingGroupOpts()
    agstate_cls = DispersedAgentSelector.get_state_cls()
    agselector = DispersedAgentSelector(
        sgroup_opts,
        {},
        agent_selection_resource_priority,
        state_store=InMemoryResourceGroupStateStore(agstate_cls),
    )
    sgroup_name = example_agents[0].scaling_group
    candidate_agents = example_agents
    example_pending_sessions[0].kernels[0].agent = example_agents[0].id
    sess_ctx = example_pending_sessions[0]
    mock_etcd = DummyEtcd()
    test_valkey_live = MagicMock()
    test_valkey_stat = MagicMock()

    mock_schedule_repository = MagicMock(spec=ScheduleRepository)

    dispatcher = SchedulerDispatcher(
        config_provider=mock_config_provider,
        etcd=mock_etcd,  # type: ignore
        event_producer=mock_event_producer,
        lock_factory=file_lock_factory,
        registry=registry,
        valkey_live=test_valkey_live,
        valkey_stat=test_valkey_stat,
        schedule_repository=mock_schedule_repository,
    )

    # manually assigned agent has None capacity
    mock_dbresult.scalar = MagicMock(return_value=None)
    await dispatcher._schedule_single_node_session(
        mock_sched_ctx,
        agselector,
        sgroup_name,
        candidate_agents,
        sess_ctx,
        mock_check_result,
    )
    result = mock_dbresult.scalar()
    assert result is None

    # manually assigned agent has empty capacity
    mock_dbresult.scalar = MagicMock(return_value={})
    await dispatcher._schedule_single_node_session(
        mock_sched_ctx,
        agselector,
        sgroup_name,
        candidate_agents,
        sess_ctx,
        mock_check_result,
    )
    result = mock_dbresult.scalar()
    assert result == {}

    # manually assigned agent is enough capacity
    mock_dbresult.scalar = MagicMock(
        return_value={
            "cpu": Decimal("8.0"),
            "mem": Decimal("8192"),
            "cuda.shares": Decimal("4"),
            "rocm.devices": Decimal("4"),
        }
    )
    await dispatcher._schedule_single_node_session(
        mock_sched_ctx,
        agselector,
        sgroup_name,
        candidate_agents,
        sess_ctx,
        mock_check_result,
    )
    result = mock_dbresult.scalar()
    for key in result:
        assert result[key] >= example_pending_sessions[0].requested_slots[key]

    # manually assigned agent is not enough capacity.
    mock_dbresult.scalar = MagicMock(
        return_value={
            "cpu": Decimal("0.0"),
            "mem": Decimal("0"),
            "cuda.shares": Decimal("0"),
            "rocm.devices": Decimal("0"),
        }
    )
    await dispatcher._schedule_single_node_session(
        mock_sched_ctx,
        agselector,
        sgroup_name,
        candidate_agents,
        sess_ctx,
        mock_check_result,
    )
    result = mock_dbresult.scalar()
    for key in result:
        assert result[key] <= example_pending_sessions[0].requested_slots[key]


@pytest.mark.asyncio
@mock.patch("ai.backend.manager.scheduler.predicates.datetime")
async def test_multiple_timezones_for_reserved_batch_session_predicate(
    mock_dt: MagicMock,
) -> None:
    mock_db_conn = MagicMock()
    mock_sched_ctx = MagicMock()
    mock_sess_ctx = MagicMock()
    mock_sess_ctx.session_type = SessionTypes.BATCH
    mock_sess_ctx.kernel_id = "fake-kernel-id"

    now = "2020-06-29T00:00:00+00:00"
    mock_dt.now = MagicMock(return_value=dtparse(now))

    # Start time is not yet reached (now < start time)
    start_time = "2020-06-29T00:00:01+00:00"
    mock_db_conn.scalar = AsyncMock(return_value=dtparse(start_time))
    result = await check_reserved_batch_session(mock_db_conn, mock_sched_ctx, mock_sess_ctx)
    assert not result.passed, (now, start_time)

    # Start time is reached (now > start time)
    start_time = "2020-06-28T23:59:59+00:00"
    mock_db_conn.scalar = AsyncMock(return_value=dtparse(start_time))
    result = await check_reserved_batch_session(mock_db_conn, mock_sched_ctx, mock_sess_ctx)
    assert result.passed, (now, start_time)

    # Start time is not yet reached by timezone (now < start time)
    # Note that 6/29 00:00 (UTC) < 6/29 00:00 (-09:00) == 6/29 09:00 (UTC)
    for i in range(1, 12):
        start_time = f"2020-06-29T00:00:00-{i:02d}:00"
        mock_db_conn.scalar = AsyncMock(return_value=dtparse(start_time))
        result = await check_reserved_batch_session(mock_db_conn, mock_sched_ctx, mock_sess_ctx)
        assert not result.passed, (now, start_time)

    # Start time is reached by timezone (now > start time)
    # Note that 6/29 00:00 (UTC) > 6/29 00:00 (+09:00) == 6/28 15:00 (UTC)
    for i in range(1, 12):
        start_time = f"2020-06-29T00:00:00+{i:02d}:00"
        mock_db_conn.scalar = AsyncMock(return_value=dtparse(start_time))
        result = await check_reserved_batch_session(mock_db_conn, mock_sched_ctx, mock_sess_ctx)
        assert result.passed, (now, start_time)

    # Should pass if start time is not specified (start immediately).
    mock_db_conn.scalar = AsyncMock(return_value=None)
    result = await check_reserved_batch_session(mock_db_conn, mock_sched_ctx, mock_sess_ctx)
    assert result.passed
