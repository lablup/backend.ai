import uuid
from decimal import Decimal

import pytest

from ai.backend.common.types import AccessKey, ResourceSlot, SessionId
from ai.backend.manager.sokovan.scheduler.prioritizers.lifo import LIFOSchedulingPrioritizer
from ai.backend.manager.sokovan.scheduler.types import (
    ConcurrencySnapshot,
    PendingSessionSnapshot,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencySnapshot,
    SessionWorkload,
    SystemSnapshot,
)


class TestLIFOSchedulingPrioritizer:
    @pytest.fixture
    def prioritizer(self) -> LIFOSchedulingPrioritizer:
        return LIFOSchedulingPrioritizer()

    @pytest.fixture
    def system_snapshot(self) -> SystemSnapshot:
        return SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={},
                by_group={},
                by_domain={},
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
        )

    @pytest.mark.asyncio
    async def test_name(self, prioritizer: LIFOSchedulingPrioritizer) -> None:
        assert prioritizer.name == "LIFO-scheduling-prioritizer"

    @pytest.mark.asyncio
    async def test_empty_workload(
        self, prioritizer: LIFOSchedulingPrioritizer, system_snapshot: SystemSnapshot
    ) -> None:
        result = await prioritizer.prioritize(system_snapshot, [])
        assert result == []

    @pytest.mark.asyncio
    async def test_reverses_order(
        self, prioritizer: LIFOSchedulingPrioritizer, system_snapshot: SystemSnapshot
    ) -> None:
        workloads = [
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user1"),
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                user_uuid=uuid.uuid4(),
                group_id=uuid.uuid4(),
                domain_name="default",
                priority=0,
            ),
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user2"),
                requested_slots=ResourceSlot(cpu=Decimal("20"), mem=Decimal("20")),
                user_uuid=uuid.uuid4(),
                group_id=uuid.uuid4(),
                domain_name="default",
                priority=0,
            ),
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user3"),
                requested_slots=ResourceSlot(cpu=Decimal("30"), mem=Decimal("30")),
                user_uuid=uuid.uuid4(),
                group_id=uuid.uuid4(),
                domain_name="default",
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
    async def test_single_workload(
        self, prioritizer: LIFOSchedulingPrioritizer, system_snapshot: SystemSnapshot
    ) -> None:
        workloads = [
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user1"),
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                user_uuid=uuid.uuid4(),
                group_id=uuid.uuid4(),
                domain_name="default",
                priority=0,
            ),
        ]

        result = await prioritizer.prioritize(system_snapshot, workloads)

        # Single item should remain the same
        assert len(result) == 1
        assert result[0] == workloads[0]

    @pytest.mark.asyncio
    async def test_ignores_system_snapshot(self, prioritizer: LIFOSchedulingPrioritizer) -> None:
        # LIFO should work the same regardless of system state
        snapshot_with_allocations = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={
                    AccessKey("user1"): ResourceSlot(cpu=Decimal("50"), mem=Decimal("50")),
                    AccessKey("user2"): ResourceSlot(cpu=Decimal("30"), mem=Decimal("30")),
                },
                by_user={},
                by_group={},
                by_domain={},
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
        )

        workloads = [
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user2"),
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                user_uuid=uuid.uuid4(),
                group_id=uuid.uuid4(),
                domain_name="default",
                priority=0,
            ),
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user1"),
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                user_uuid=uuid.uuid4(),
                group_id=uuid.uuid4(),
                domain_name="default",
                priority=0,
            ),
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user3"),  # New user
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                user_uuid=uuid.uuid4(),
                group_id=uuid.uuid4(),
                domain_name="default",
                priority=0,
            ),
        ]

        result = await prioritizer.prioritize(snapshot_with_allocations, workloads)

        # Should still reverse order despite different allocations
        assert len(result) == 3
        assert result[0] == workloads[2]
        assert result[1] == workloads[1]
        assert result[2] == workloads[0]
