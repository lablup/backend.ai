import uuid
from decimal import Decimal

import pytest

from ai.backend.common.types import AccessKey, ResourceSlot, SessionId
from ai.backend.manager.sokovan.scheduler.provisioner.sequencers.drf import DRFSequencer
from ai.backend.manager.sokovan.scheduler.types import (
    ConcurrencySnapshot,
    KeypairOccupancy,
    PendingSessionSnapshot,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencySnapshot,
    SessionWorkload,
    SystemSnapshot,
)


class TestDRFSequencer:
    @pytest.fixture
    def sequencer(self) -> DRFSequencer:
        return DRFSequencer()

    @pytest.fixture
    def empty_system_snapshot(self) -> SystemSnapshot:
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

    @pytest.fixture
    def system_snapshot_with_allocations(self) -> SystemSnapshot:
        return SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={
                    AccessKey("user1"): KeypairOccupancy(
                        occupied_slots=ResourceSlot(cpu=Decimal("20"), mem=Decimal("10")),
                        session_count=1,
                        sftp_session_count=0,
                    ),  # dominant share: 20%
                    AccessKey("user2"): KeypairOccupancy(
                        occupied_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("30")),
                        session_count=1,
                        sftp_session_count=0,
                    ),  # dominant share: 30%
                    AccessKey("user3"): KeypairOccupancy(
                        occupied_slots=ResourceSlot(cpu=Decimal("5"), mem=Decimal("5")),
                        session_count=1,
                        sftp_session_count=0,
                    ),  # dominant share: 5%
                },
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

    @pytest.mark.asyncio
    async def test_name(self, sequencer: DRFSequencer) -> None:
        assert sequencer.name == "DRFSequencer"

    @pytest.mark.asyncio
    async def test_empty_workload(
        self, sequencer: DRFSequencer, empty_system_snapshot: SystemSnapshot
    ) -> None:
        result = sequencer.sequence(empty_system_snapshot, [])
        assert result == []

    @pytest.mark.asyncio
    async def test_single_user_workloads(
        self, sequencer: DRFSequencer, empty_system_snapshot: SystemSnapshot
    ) -> None:
        workloads = [
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user1"),
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                user_uuid=uuid.uuid4(),
                group_id=uuid.uuid4(),
                domain_name="default",
                scaling_group="default",
                priority=0,
            ),
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user1"),
                requested_slots=ResourceSlot(cpu=Decimal("20"), mem=Decimal("20")),
                user_uuid=uuid.uuid4(),
                group_id=uuid.uuid4(),
                domain_name="default",
                scaling_group="default",
                priority=0,
            ),
        ]

        result = sequencer.sequence(empty_system_snapshot, workloads)

        # With no existing allocations, order should be preserved
        assert len(result) == 2
        assert result[0] == workloads[0]
        assert result[1] == workloads[1]

    @pytest.mark.asyncio
    async def test_multiple_users_different_dominant_shares(
        self,
        sequencer: DRFSequencer,
        system_snapshot_with_allocations: SystemSnapshot,
    ) -> None:
        workloads = [
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user2"),  # 30% dominant share
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                user_uuid=uuid.uuid4(),
                group_id=uuid.uuid4(),
                domain_name="default",
                scaling_group="default",
                priority=0,
            ),
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user3"),  # 5% dominant share (lowest)
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                user_uuid=uuid.uuid4(),
                group_id=uuid.uuid4(),
                domain_name="default",
                scaling_group="default",
                priority=0,
            ),
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user1"),  # 20% dominant share
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                user_uuid=uuid.uuid4(),
                group_id=uuid.uuid4(),
                domain_name="default",
                scaling_group="default",
                priority=0,
            ),
        ]

        result = sequencer.sequence(system_snapshot_with_allocations, workloads)

        # Should be ordered by dominant share (ascending): user3 (5%), user1 (20%), user2 (30%)
        assert len(result) == 3
        assert result[0].access_key == AccessKey("user3")
        assert result[1].access_key == AccessKey("user1")
        assert result[2].access_key == AccessKey("user2")

    @pytest.mark.asyncio
    async def test_multiple_users_same_dominant_share(
        self, sequencer: DRFSequencer, empty_system_snapshot: SystemSnapshot
    ) -> None:
        # All users have no existing allocations (0% dominant share)
        workloads = [
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user1"),
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                user_uuid=uuid.uuid4(),
                group_id=uuid.uuid4(),
                domain_name="default",
                scaling_group="default",
                priority=0,
            ),
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user2"),
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                user_uuid=uuid.uuid4(),
                group_id=uuid.uuid4(),
                domain_name="default",
                scaling_group="default",
                priority=0,
            ),
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user3"),
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                user_uuid=uuid.uuid4(),
                group_id=uuid.uuid4(),
                domain_name="default",
                scaling_group="default",
                priority=0,
            ),
        ]

        result = sequencer.sequence(empty_system_snapshot, workloads)

        # With same dominant share, order should be preserved
        assert len(result) == 3
        assert result[0] == workloads[0]
        assert result[1] == workloads[1]
        assert result[2] == workloads[2]

    @pytest.mark.asyncio
    async def test_new_user_gets_priority(
        self,
        sequencer: DRFSequencer,
        system_snapshot_with_allocations: SystemSnapshot,
    ) -> None:
        workloads = [
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user2"),  # 30% dominant share
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                user_uuid=uuid.uuid4(),
                group_id=uuid.uuid4(),
                domain_name="default",
                scaling_group="default",
                priority=0,
            ),
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("new_user"),  # 0% dominant share (new user)
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                user_uuid=uuid.uuid4(),
                group_id=uuid.uuid4(),
                domain_name="default",
                scaling_group="default",
                priority=0,
            ),
        ]

        result = sequencer.sequence(system_snapshot_with_allocations, workloads)

        # New user with 0% dominant share should get priority
        assert len(result) == 2
        assert result[0].access_key == AccessKey("new_user")
        assert result[1].access_key == AccessKey("user2")

    @pytest.mark.asyncio
    async def test_dominant_share_calculation_with_zero_capacity(
        self, sequencer: DRFSequencer
    ) -> None:
        # Test edge case where some resource has zero capacity
        system_snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(
                cpu=Decimal("100"), mem=Decimal("0")
            ),  # Zero memory capacity
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={
                    AccessKey("user1"): KeypairOccupancy(
                        occupied_slots=ResourceSlot(cpu=Decimal("50"), mem=Decimal("10")),
                        session_count=1,
                        sftp_session_count=0,
                    ),
                },
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

        workloads = [
            SessionWorkload(
                session_id=SessionId(uuid.uuid4()),
                access_key=AccessKey("user1"),
                requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                user_uuid=uuid.uuid4(),
                group_id=uuid.uuid4(),
                domain_name="default",
                scaling_group="default",
                priority=0,
            ),
        ]

        # Should not crash when dividing by zero capacity
        result = sequencer.sequence(system_snapshot, workloads)
        assert len(result) == 1
