"""Tests for concurrency validator."""

import uuid
from decimal import Decimal

import pytest

from ai.backend.common.types import AccessKey, ResourceSlot, SessionId
from ai.backend.manager.sokovan.scheduler.provisioner.validators import (
    ConcurrencyLimitExceeded,
    ConcurrencyValidator,
)
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


class TestConcurrencyValidator:
    @pytest.fixture
    def validator(self) -> ConcurrencyValidator:
        return ConcurrencyValidator()

    @pytest.fixture
    def sftp_validator(self) -> ConcurrencyValidator:
        return ConcurrencyValidator()

    @pytest.fixture
    def workload(self) -> SessionWorkload:
        return SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("1"), mem=Decimal("1")),
            user_uuid=uuid.uuid4(),
            group_id=uuid.uuid4(),
            domain_name="default",
            scaling_group="default",
            is_private=False,
        )

    @pytest.fixture
    def sftp_workload(self) -> SessionWorkload:
        return SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("1"), mem=Decimal("1")),
            user_uuid=uuid.uuid4(),
            group_id=uuid.uuid4(),
            domain_name="default",
            scaling_group="default",
            is_private=True,
        )

    def test_passes_when_under_limit(
        self, validator: ConcurrencyValidator, workload: SessionWorkload
    ) -> None:
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={}, by_user={}, by_group={}, by_domain={}, by_agent={}
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
            concurrency=ConcurrencySnapshot(
                sessions_by_keypair={AccessKey("user1"): 2},  # Under limit of 3
                sftp_sessions_by_keypair={},
            ),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        # Should not raise
        validator.validate(snapshot, workload)

    def test_fails_when_at_limit(
        self, validator: ConcurrencyValidator, workload: SessionWorkload
    ) -> None:
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={}, by_user={}, by_group={}, by_domain={}, by_agent={}
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
            concurrency=ConcurrencySnapshot(
                sessions_by_keypair={AccessKey("user1"): 3},  # At limit
                sftp_sessions_by_keypair={},
            ),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        with pytest.raises(ConcurrencyLimitExceeded) as exc_info:
            validator.validate(snapshot, workload)
        assert "You cannot run more than 3 concurrent sessions" in str(exc_info.value)

    def test_sftp_validator_checks_sftp_sessions(
        self, sftp_validator: ConcurrencyValidator, sftp_workload: SessionWorkload
    ) -> None:
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={}, by_user={}, by_group={}, by_domain={}, by_agent={}
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
            concurrency=ConcurrencySnapshot(
                sessions_by_keypair={AccessKey("user1"): 3},
                sftp_sessions_by_keypair={AccessKey("user1"): 1},  # At SFTP limit
            ),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        with pytest.raises(ConcurrencyLimitExceeded) as exc_info:
            sftp_validator.validate(snapshot, sftp_workload)
        assert "You cannot run more than 1 SFTP sessions" in str(exc_info.value)

    def test_passes_when_no_policy(
        self, validator: ConcurrencyValidator, workload: SessionWorkload
    ) -> None:
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={}, by_user={}, by_group={}, by_domain={}, by_agent={}
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},  # No policy for user1
                user_policies={},
                group_limits={},
                domain_limits={},
            ),
            concurrency=ConcurrencySnapshot(
                sessions_by_keypair={AccessKey("user1"): 10},
                sftp_sessions_by_keypair={},
            ),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        # Should not raise when no policy is defined
        validator.validate(snapshot, workload)

    def test_passes_when_limit_is_none(
        self, validator: ConcurrencyValidator, workload: SessionWorkload
    ) -> None:
        """Test that None values in max_concurrent_sessions means unlimited."""
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={}, by_user={}, by_group={}, by_domain={}, by_agent={}
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={
                    AccessKey("user1"): KeyPairResourcePolicy(
                        name="unlimited",
                        total_resource_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                        max_concurrent_sessions=None,  # None means unlimited
                        max_concurrent_sftp_sessions=None,  # None means unlimited
                        max_pending_session_count=None,
                        max_pending_session_resource_slots=None,
                    )
                },
                user_policies={},
                group_limits={},
                domain_limits={},
            ),
            concurrency=ConcurrencySnapshot(
                sessions_by_keypair={AccessKey("user1"): 100},  # Many sessions
                sftp_sessions_by_keypair={AccessKey("user1"): 50},  # Many SFTP sessions
            ),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        # Should not raise when limit is None (unlimited)
        validator.validate(snapshot, workload)

    def test_passes_when_limit_is_zero(
        self,
        validator: ConcurrencyValidator,
        sftp_validator: ConcurrencyValidator,
        workload: SessionWorkload,
        sftp_workload: SessionWorkload,
    ) -> None:
        """Test that 0 in max_concurrent_sessions means unlimited."""
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={}, by_user={}, by_group={}, by_domain={}, by_agent={}
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={
                    AccessKey("user1"): KeyPairResourcePolicy(
                        name="unlimited",
                        total_resource_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                        max_concurrent_sessions=0,  # 0 also means unlimited
                        max_concurrent_sftp_sessions=0,  # 0 also means unlimited
                        max_pending_session_count=None,
                        max_pending_session_resource_slots=None,
                    )
                },
                user_policies={},
                group_limits={},
                domain_limits={},
            ),
            concurrency=ConcurrencySnapshot(
                sessions_by_keypair={AccessKey("user1"): 100},  # Many sessions
                sftp_sessions_by_keypair={AccessKey("user1"): 50},  # Many SFTP sessions
            ),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        # Should not raise when limit is 0 (unlimited)
        validator.validate(snapshot, workload)
        sftp_validator.validate(snapshot, sftp_workload)
