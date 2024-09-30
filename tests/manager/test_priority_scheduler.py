from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from ai.backend.common.types import (
    ResourceSlot,
    SessionId,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts
from ai.backend.manager.scheduler.fifo import FIFOSlotScheduler, LIFOSlotScheduler

from .scheduler_utils import (
    create_mock_session,
    find_and_pop_picked_session,
)


@pytest.mark.asyncio
async def test_priority_scheduler_fifo() -> None:
    sid = lambda: SessionId(uuid4())
    rs = ResourceSlot({"cpu": Decimal(1), "mem": Decimal(1024)})
    total_capacity = ResourceSlot({"cpu": Decimal(8), "mem": Decimal(8192)})
    pending_sessions = [
        create_mock_session(sid(), rs, priority=10),
        create_mock_session(sid(), rs, priority=8),
        create_mock_session(sid(), rs, priority=10),
        create_mock_session(sid(), rs, priority=12),
        create_mock_session(sid(), rs, priority=10),
    ]
    session_ids: list[SessionId] = [s.id for s in pending_sessions]
    picked_session_ids: list[SessionId] = []
    scheduler = FIFOSlotScheduler(ScalingGroupOpts(), {})
    while pending_sessions:
        _, prioritized_pending_sessions = scheduler.prioritize(pending_sessions)
        picked_session_id = scheduler.pick_session(total_capacity, prioritized_pending_sessions, [])
        assert picked_session_id is not None
        find_and_pop_picked_session(pending_sessions, picked_session_id)
        picked_session_ids.append(picked_session_id)

    assert picked_session_ids == [
        session_ids[3],  # priority 12
        session_ids[0],  # priority 10 (oldest)
        session_ids[2],  # priority 10
        session_ids[4],  # priority 10 (newest)
        session_ids[1],  # priority 8
    ]


@pytest.mark.asyncio
async def test_priority_scheduler_lifo() -> None:
    sid = lambda: SessionId(uuid4())
    rs = ResourceSlot({"cpu": Decimal(1), "mem": Decimal(1024)})
    total_capacity = ResourceSlot({"cpu": Decimal(8), "mem": Decimal(8192)})
    pending_sessions = [
        create_mock_session(sid(), rs, priority=10),
        create_mock_session(sid(), rs, priority=8),
        create_mock_session(sid(), rs, priority=10),
        create_mock_session(sid(), rs, priority=12),
        create_mock_session(sid(), rs, priority=10),
    ]
    session_ids: list[SessionId] = [s.id for s in pending_sessions]
    picked_session_ids: list[SessionId] = []
    scheduler = LIFOSlotScheduler(ScalingGroupOpts(), {})
    while pending_sessions:
        _, prioritized_pending_sessions = scheduler.prioritize(pending_sessions)
        picked_session_id = scheduler.pick_session(total_capacity, prioritized_pending_sessions, [])
        assert picked_session_id is not None
        find_and_pop_picked_session(pending_sessions, picked_session_id)
        picked_session_ids.append(picked_session_id)

    assert picked_session_ids == [
        session_ids[3],  # priority 12
        session_ids[4],  # priority 10 (newest)
        session_ids[2],  # priority 10
        session_ids[0],  # priority 10 (oldest)
        session_ids[1],  # priority 8
    ]
