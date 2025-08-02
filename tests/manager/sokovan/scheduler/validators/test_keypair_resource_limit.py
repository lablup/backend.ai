"""Tests for keypair resource limit validator."""

import uuid
from decimal import Decimal

import pytest

from ai.backend.common.types import AccessKey, ResourceSlot, SessionId
from ai.backend.manager.sokovan.scheduler.types import (
    ConcurrencySnapshot,
    KeyPairResourcePolicy,
    PendingSessionSnapshot,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencySnapshot,
    SessionWorkload,
    SystemSnapshot,
)
from ai.backend.manager.sokovan.scheduler.validators import (
    KeypairResourceLimitValidator,
    KeypairResourceQuotaExceeded,
)


class TestKeypairResourceLimitValidator:
    @pytest.fixture
    def validator(self) -> KeypairResourceLimitValidator:
        return KeypairResourceLimitValidator()

    def test_passes_when_under_limit(self, validator: KeypairResourceLimitValidator) -> None:
        workload = SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("2"), mem=Decimal("2")),
            user_uuid=uuid.uuid4(),
            group_id=uuid.uuid4(),
            domain_name="default",
        )
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={AccessKey("user1"): ResourceSlot(cpu=Decimal("3"), mem=Decimal("3"))},
                by_user={},
                by_group={},
                by_domain={},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={
                    AccessKey("user1"): KeyPairResourcePolicy(
                        name="default",
                        total_resource_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                        max_concurrent_sessions=3,
                        max_concurrent_sftp_sessions=1,
                        max_pending_session_count=5,
                        max_pending_session_resource_slots=None,
                    )
                },
                user_policies={},
                group_limits={},
                domain_limits={},
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
        )

        # Should not raise (3 + 2 <= 10)
        validator.validate(snapshot, workload)

    def test_fails_when_exceeds_limit(self, validator: KeypairResourceLimitValidator) -> None:
        workload = SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("5"), mem=Decimal("5")),
            user_uuid=uuid.uuid4(),
            group_id=uuid.uuid4(),
            domain_name="default",
        )
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={AccessKey("user1"): ResourceSlot(cpu=Decimal("8"), mem=Decimal("8"))},
                by_user={},
                by_group={},
                by_domain={},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={
                    AccessKey("user1"): KeyPairResourcePolicy(
                        name="default",
                        total_resource_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                        max_concurrent_sessions=3,
                        max_concurrent_sftp_sessions=1,
                        max_pending_session_count=5,
                        max_pending_session_resource_slots=None,
                    )
                },
                user_policies={},
                group_limits={},
                domain_limits={},
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
        )

        with pytest.raises(KeypairResourceQuotaExceeded) as exc_info:
            validator.validate(snapshot, workload)
        assert "Your keypair resource quota is exceeded" in str(exc_info.value)

    def test_passes_when_no_policy(self, validator: KeypairResourceLimitValidator) -> None:
        workload = SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            user_uuid=uuid.uuid4(),
            group_id=uuid.uuid4(),
            domain_name="default",
        )
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={AccessKey("user1"): ResourceSlot(cpu=Decimal("50"), mem=Decimal("50"))},
                by_user={},
                by_group={},
                by_domain={},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},  # No policy for user1
                user_policies={},
                group_limits={},
                domain_limits={},
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
        )

        # Should not raise when no policy is defined
        validator.validate(snapshot, workload)

    def test_passes_when_no_current_occupancy(
        self, validator: KeypairResourceLimitValidator
    ) -> None:
        workload = SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("5"), mem=Decimal("5")),
            user_uuid=uuid.uuid4(),
            group_id=uuid.uuid4(),
            domain_name="default",
        )
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},  # No current occupancy for user1
                by_user={},
                by_group={},
                by_domain={},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={
                    AccessKey("user1"): KeyPairResourcePolicy(
                        name="default",
                        total_resource_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                        max_concurrent_sessions=3,
                        max_concurrent_sftp_sessions=1,
                        max_pending_session_count=5,
                        max_pending_session_resource_slots=None,
                    )
                },
                user_policies={},
                group_limits={},
                domain_limits={},
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
        )

        # Should not raise (0 + 5 <= 10)
        validator.validate(snapshot, workload)
