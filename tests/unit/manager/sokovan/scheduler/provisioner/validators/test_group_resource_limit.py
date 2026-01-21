"""Tests for group resource limit validator."""

import uuid
from decimal import Decimal

import pytest

from ai.backend.common.types import AccessKey, ResourceSlot, SessionId
from ai.backend.manager.sokovan.scheduler.provisioner.validators import (
    GroupResourceLimitValidator,
    GroupResourceQuotaExceeded,
)
from ai.backend.manager.sokovan.scheduler.types import (
    ConcurrencySnapshot,
    PendingSessionSnapshot,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencySnapshot,
    SessionWorkload,
    SystemSnapshot,
)


class TestGroupResourceLimitValidator:
    @pytest.fixture
    def group_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def validator(self) -> GroupResourceLimitValidator:
        return GroupResourceLimitValidator()

    def test_passes_when_under_limit(
        self, validator: GroupResourceLimitValidator, group_id: uuid.UUID
    ) -> None:
        workload = SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("2"), mem=Decimal("2")),
            user_uuid=uuid.uuid4(),
            group_id=group_id,
            domain_name="default",
            scaling_group="default",
        )
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={},
                by_group={group_id: ResourceSlot(cpu=Decimal("3"), mem=Decimal("3"))},
                by_domain={},
                by_agent={},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},
                user_policies={},
                group_limits={group_id: ResourceSlot(cpu=Decimal("10"), mem=Decimal("10"))},
                domain_limits={},
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        # Should not raise (3 + 2 <= 10)
        validator.validate(snapshot, workload)

    def test_fails_when_exceeds_limit(
        self, validator: GroupResourceLimitValidator, group_id: uuid.UUID
    ) -> None:
        workload = SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("5"), mem=Decimal("5")),
            user_uuid=uuid.uuid4(),
            group_id=group_id,
            domain_name="default",
            scaling_group="default",
        )
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={},
                by_group={group_id: ResourceSlot(cpu=Decimal("8"), mem=Decimal("8"))},
                by_domain={},
                by_agent={},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},
                user_policies={},
                group_limits={group_id: ResourceSlot(cpu=Decimal("10"), mem=Decimal("10"))},
                domain_limits={},
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        with pytest.raises(GroupResourceQuotaExceeded) as exc_info:
            validator.validate(snapshot, workload)
        assert "Your group resource quota is exceeded" in str(exc_info.value)

    def test_passes_when_no_limit(
        self, validator: GroupResourceLimitValidator, group_id: uuid.UUID
    ) -> None:
        workload = SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            user_uuid=uuid.uuid4(),
            group_id=group_id,
            domain_name="default",
            scaling_group="default",
        )
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={},
                by_group={group_id: ResourceSlot(cpu=Decimal("50"), mem=Decimal("50"))},
                by_domain={},
                by_agent={},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},
                user_policies={},
                group_limits={},  # No limit for group
                domain_limits={},
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        # Should not raise when no limit is defined
        validator.validate(snapshot, workload)

    def test_passes_when_no_current_occupancy(
        self, validator: GroupResourceLimitValidator, group_id: uuid.UUID
    ) -> None:
        workload = SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("5"), mem=Decimal("5")),
            user_uuid=uuid.uuid4(),
            group_id=group_id,
            domain_name="default",
            scaling_group="default",
        )
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={},
                by_group={},  # No current occupancy for group
                by_domain={},
                by_agent={},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},
                user_policies={},
                group_limits={group_id: ResourceSlot(cpu=Decimal("10"), mem=Decimal("10"))},
                domain_limits={},
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        # Should not raise (0 + 5 <= 10)
        validator.validate(snapshot, workload)
