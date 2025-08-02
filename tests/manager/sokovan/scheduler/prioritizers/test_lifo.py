import uuid
from decimal import Decimal

import pytest

from ai.backend.common.types import AccessKey, ResourceSlot, SessionId
from ai.backend.manager.sokovan.scheduler.prioritizers.lifo import LIFOSchedulingPrioritizer
from ai.backend.manager.sokovan.scheduler.types import SessionWorkload, SystemSnapshot


class TestLIFOSchedulingPrioritizer:
    @pytest.fixture
    def prioritizer(self):
        return LIFOSchedulingPrioritizer()

    @pytest.fixture
    def system_snapshot(self):
        return SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            user_allocations={},
        )

    @pytest.mark.asyncio
    async def test_name(self, prioritizer):
        assert prioritizer.name == "LIFO-scheduling-prioritizer"

    @pytest.mark.asyncio
    async def test_empty_workload(self, prioritizer, system_snapshot):
        result = await prioritizer.prioritize(system_snapshot, [])
        assert result == []

    @pytest.mark.asyncio
    async def test_reverses_order(self, prioritizer, system_snapshot):
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

        # LIFO should reverse the order
        assert len(result) == 3
        assert result[0] == workloads[2]  # Last becomes first
        assert result[1] == workloads[1]  # Middle stays middle
        assert result[2] == workloads[0]  # First becomes last

    @pytest.mark.asyncio
    async def test_single_workload(self, prioritizer, system_snapshot):
        workloads = [
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user1"),
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                priority=0,
            ),
        ]

        result = await prioritizer.prioritize(system_snapshot, workloads)

        # Single item should remain the same
        assert len(result) == 1
        assert result[0] == workloads[0]

    @pytest.mark.asyncio
    async def test_ignores_system_snapshot(self, prioritizer):
        # LIFO should work the same regardless of system state
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
                access_key=AccessKey("user2"),
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                priority=0,
            ),
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user1"),
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                priority=0,
            ),
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user3"),  # New user
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                priority=0,
            ),
        ]

        result = await prioritizer.prioritize(snapshot_with_allocations, workloads)

        # Should still reverse order despite different allocations
        assert len(result) == 3
        assert result[0] == workloads[2]
        assert result[1] == workloads[1]
        assert result[2] == workloads[0]
