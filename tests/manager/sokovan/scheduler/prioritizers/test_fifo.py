import uuid
from decimal import Decimal

import pytest

from ai.backend.common.types import AccessKey, ResourceSlot, SessionId
from ai.backend.manager.sokovan.scheduler.prioritizers.fifo import FIFOSchedulingPrioritizer
from ai.backend.manager.sokovan.scheduler.types import SessionWorkload, SystemSnapshot


class TestFIFOSchedulingPrioritizer:
    @pytest.fixture
    def prioritizer(self):
        return FIFOSchedulingPrioritizer()

    @pytest.fixture
    def system_snapshot(self):
        return SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            user_allocations={},
        )

    @pytest.mark.asyncio
    async def test_name(self, prioritizer):
        assert prioritizer.name == "FIFO-scheduling-prioritizer"

    @pytest.mark.asyncio
    async def test_empty_workload(self, prioritizer, system_snapshot):
        result = await prioritizer.prioritize(system_snapshot, [])
        assert result == []

    @pytest.mark.asyncio
    async def test_preserves_order(self, prioritizer, system_snapshot):
        workloads = [
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user1"),
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                priority=0,
            ),
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user2"),
                requested_slots=ResourceSlot(cpu=Decimal("20"), mem=Decimal("20")),
                priority=0,
            ),
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user3"),
                requested_slots=ResourceSlot(cpu=Decimal("30"), mem=Decimal("30")),
                priority=0,
            ),
        ]

        result = await prioritizer.prioritize(system_snapshot, workloads)

        # FIFO should preserve the original order
        assert len(result) == 3
        assert result[0] == workloads[0]
        assert result[1] == workloads[1]
        assert result[2] == workloads[2]

    @pytest.mark.asyncio
    async def test_ignores_system_snapshot(self, prioritizer):
        # FIFO should work the same regardless of system state
        snapshot_with_allocations = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            user_allocations={
                AccessKey("user1"): ResourceSlot(cpu=Decimal("50"), mem=Decimal("50")),
                AccessKey("user2"): ResourceSlot(cpu=Decimal("30"), mem=Decimal("30")),
            },
        )

        workloads = [
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user2"),  # User with more allocation
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                priority=0,
            ),
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user1"),  # User with less allocation
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                priority=0,
            ),
        ]

        result = await prioritizer.prioritize(snapshot_with_allocations, workloads)

        # Should still preserve original order despite different allocations
        assert len(result) == 2
        assert result[0] == workloads[0]
        assert result[1] == workloads[1]
