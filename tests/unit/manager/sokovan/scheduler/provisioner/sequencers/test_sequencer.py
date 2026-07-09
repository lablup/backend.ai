import uuid
from decimal import Decimal

import pytest

from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import AccessKey, ResourceSlot, SessionId
from ai.backend.manager.data.sokovan import (
    ConcurrencySnapshot,
    PendingSessionSnapshot,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencySnapshot,
    SessionWorkload,
    SystemSnapshot,
)
from ai.backend.manager.sokovan.scheduler.provisioner.sequencers.fifo import FIFOSequencer
from ai.backend.manager.sokovan.scheduler.provisioner.sequencers.sequencer import (
    SchedulingSequencer,
)


def make_workload(access_key: str, priority: int) -> SessionWorkload:
    return SessionWorkload(
        session_id=SessionId(uuid.uuid4()),
        access_key=AccessKey(access_key),
        requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
        user_uuid=uuid.uuid4(),
        group_id=uuid.uuid4(),
        domain_name="default",
        scaling_group="default",
        resource_group_id=ResourceGroupID(uuid.uuid4()),
        priority=priority,
    )


class TestSchedulingSequencer:
    @pytest.fixture
    def scaling_group(self) -> str:
        return "default"

    @pytest.fixture
    def sequencer(self) -> SchedulingSequencer:
        return SchedulingSequencer(FIFOSequencer())

    @pytest.fixture
    def system_snapshot(self) -> SystemSnapshot:
        return SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={},
                by_group={},
                by_domain={},
                by_agent={},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},
                user_policies={},
                group_limits={},
                domain_limits={},
            ),
            concurrency=ConcurrencySnapshot(
                sessions_by_keypair={},
                sftp_sessions_by_keypair={},
            ),
            pending_sessions=PendingSessionSnapshot(
                by_keypair={},
            ),
            session_dependencies=SessionDependencySnapshot(
                by_session={},
            ),
            known_slot_types={},
        )

    async def test_empty_workloads(
        self,
        scaling_group: str,
        sequencer: SchedulingSequencer,
        system_snapshot: SystemSnapshot,
    ) -> None:
        result = await sequencer.sequence(scaling_group, system_snapshot, [])
        assert result == []

    async def test_keeps_all_workloads_across_priorities(
        self,
        scaling_group: str,
        sequencer: SchedulingSequencer,
        system_snapshot: SystemSnapshot,
    ) -> None:
        workloads = [
            make_workload("high", priority=10),
            make_workload("mid", priority=5),
            make_workload("low", priority=0),
        ]

        result = await sequencer.sequence(scaling_group, system_snapshot, workloads)

        assert {w.access_key for w in result} == {AccessKey(k) for k in ("high", "mid", "low")}

    async def test_orders_by_descending_priority(
        self,
        scaling_group: str,
        sequencer: SchedulingSequencer,
        system_snapshot: SystemSnapshot,
    ) -> None:
        workloads = [
            make_workload("low", priority=0),
            make_workload("high", priority=10),
            make_workload("mid", priority=5),
        ]

        result = await sequencer.sequence(scaling_group, system_snapshot, workloads)

        assert [w.access_key for w in result] == [AccessKey(k) for k in ("high", "mid", "low")]

    async def test_preserves_order_within_same_priority(
        self,
        scaling_group: str,
        sequencer: SchedulingSequencer,
        system_snapshot: SystemSnapshot,
    ) -> None:
        workloads = [
            make_workload("high-first", priority=10),
            make_workload("low-first", priority=0),
            make_workload("high-second", priority=10),
            make_workload("low-second", priority=0),
        ]

        result = await sequencer.sequence(scaling_group, system_snapshot, workloads)

        assert [w.access_key for w in result] == [
            AccessKey(k) for k in ("high-first", "high-second", "low-first", "low-second")
        ]
