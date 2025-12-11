"""Tests for pending session count limit validator."""

import uuid
from datetime import datetime
from decimal import Decimal

import pytest

from ai.backend.common.types import AccessKey, ResourceSlot, SessionId
from ai.backend.manager.sokovan.scheduler.provisioner.validators import (
    PendingSessionCountLimitExceeded,
    PendingSessionCountLimitValidator,
)
from ai.backend.manager.sokovan.scheduler.types import (
    ConcurrencySnapshot,
    KeyPairResourcePolicy,
    PendingSessionInfo,
    PendingSessionSnapshot,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencySnapshot,
    SessionWorkload,
    SystemSnapshot,
)


class TestPendingSessionCountLimitValidator:
    @pytest.fixture
    def validator(self) -> PendingSessionCountLimitValidator:
        return PendingSessionCountLimitValidator()

    def test_passes_when_under_limit(
        self, validator: PendingSessionCountLimitValidator, user1_minimal_workload: SessionWorkload
    ) -> None:
        workload = user1_minimal_workload
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
                        max_pending_session_count=3,
                        max_pending_session_resource_slots=None,
                    )
                },
                user_policies={},
                group_limits={},
                domain_limits={},
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(
                by_keypair={
                    AccessKey("user1"): [
                        PendingSessionInfo(
                            session_id=SessionId(uuid.uuid4()),
                            requested_slots=ResourceSlot(cpu=Decimal("1"), mem=Decimal("1")),
                            creation_time=datetime.now(),
                        ),
                        PendingSessionInfo(
                            session_id=SessionId(uuid.uuid4()),
                            requested_slots=ResourceSlot(cpu=Decimal("1"), mem=Decimal("1")),
                            creation_time=datetime.now(),
                        ),
                    ]
                }
            ),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        # Should not raise (2 < 3)
        validator.validate(snapshot, workload)

    def test_fails_when_at_limit(
        self, validator: PendingSessionCountLimitValidator, user1_minimal_workload: SessionWorkload
    ) -> None:
        workload = user1_minimal_workload
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
                        max_pending_session_count=2,
                        max_pending_session_resource_slots=None,
                    )
                },
                user_policies={},
                group_limits={},
                domain_limits={},
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(
                by_keypair={
                    AccessKey("user1"): [
                        PendingSessionInfo(
                            session_id=SessionId(uuid.uuid4()),
                            requested_slots=ResourceSlot(cpu=Decimal("1"), mem=Decimal("1")),
                            creation_time=datetime.now(),
                        ),
                        PendingSessionInfo(
                            session_id=SessionId(uuid.uuid4()),
                            requested_slots=ResourceSlot(cpu=Decimal("1"), mem=Decimal("1")),
                            creation_time=datetime.now(),
                        ),
                    ]
                }
            ),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        with pytest.raises(PendingSessionCountLimitExceeded) as exc_info:
            validator.validate(snapshot, workload)
        assert "You cannot create more than 2 pending session(s)" in str(exc_info.value)

    def test_passes_when_no_limit(
        self, validator: PendingSessionCountLimitValidator, user1_minimal_workload: SessionWorkload
    ) -> None:
        workload = user1_minimal_workload
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
                        max_pending_session_count=None,  # No limit
                        max_pending_session_resource_slots=None,
                    )
                },
                user_policies={},
                group_limits={},
                domain_limits={},
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(
                by_keypair={
                    AccessKey("user1"): [
                        PendingSessionInfo(
                            session_id=SessionId(uuid.uuid4()),
                            requested_slots=ResourceSlot(cpu=Decimal("1"), mem=Decimal("1")),
                            creation_time=datetime.now(),
                        )
                        for _ in range(100)  # Many pending sessions
                    ]
                }
            ),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        # Should not raise when no limit is set
        validator.validate(snapshot, workload)

    def test_passes_when_no_policy(
        self, validator: PendingSessionCountLimitValidator, user1_minimal_workload: SessionWorkload
    ) -> None:
        workload = user1_minimal_workload
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
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(
                by_keypair={
                    AccessKey("user1"): [
                        PendingSessionInfo(
                            session_id=SessionId(uuid.uuid4()),
                            requested_slots=ResourceSlot(cpu=Decimal("1"), mem=Decimal("1")),
                            creation_time=datetime.now(),
                        )
                        for _ in range(10)
                    ]
                }
            ),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        # Should not raise when no policy is defined
        validator.validate(snapshot, workload)
