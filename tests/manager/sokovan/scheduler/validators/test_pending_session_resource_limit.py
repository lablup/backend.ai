"""Tests for pending session resource limit validator."""

import uuid
from datetime import datetime
from decimal import Decimal

import pytest

from ai.backend.common.types import AccessKey, ResourceSlot, SessionId
from ai.backend.manager.sokovan.scheduler.provisioner.validators import (
    PendingSessionResourceLimitValidator,
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


class TestPendingSessionResourceLimitValidator:
    @pytest.fixture
    def validator(self) -> PendingSessionResourceLimitValidator:
        return PendingSessionResourceLimitValidator()

    def test_passes_when_under_limit(self, validator: PendingSessionResourceLimitValidator) -> None:
        workload = SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("2"), mem=Decimal("2")),
            user_uuid=uuid.uuid4(),
            group_id=uuid.uuid4(),
            domain_name="default",
            scaling_group="default",
        )
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
                        max_pending_session_resource_slots=ResourceSlot(
                            cpu=Decimal("10"), mem=Decimal("10")
                        ),
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
                            requested_slots=ResourceSlot(cpu=Decimal("3"), mem=Decimal("3")),
                            creation_time=datetime.now(),
                        ),
                    ]
                }
            ),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        # Should not raise (3 + 2 <= 10)
        validator.validate(snapshot, workload)

    def test_passes_when_no_limit(self, validator: PendingSessionResourceLimitValidator) -> None:
        workload = SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            user_uuid=uuid.uuid4(),
            group_id=uuid.uuid4(),
            domain_name="default",
            scaling_group="default",
        )
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
                        max_pending_session_resource_slots=None,  # No resource limit
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
                            requested_slots=ResourceSlot(cpu=Decimal("50"), mem=Decimal("50")),
                            creation_time=datetime.now(),
                        ),
                    ]
                }
            ),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        # Should not raise when no limit is set
        validator.validate(snapshot, workload)

    def test_passes_when_no_policy(self, validator: PendingSessionResourceLimitValidator) -> None:
        workload = SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
            user_uuid=uuid.uuid4(),
            group_id=uuid.uuid4(),
            domain_name="default",
            scaling_group="default",
        )
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
                            requested_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                            creation_time=datetime.now(),
                        ),
                    ]
                }
            ),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        # Should not raise when no policy is defined
        validator.validate(snapshot, workload)

    def test_handles_multiple_pending_sessions(
        self, validator: PendingSessionResourceLimitValidator
    ) -> None:
        workload = SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("1"), mem=Decimal("1")),
            user_uuid=uuid.uuid4(),
            group_id=uuid.uuid4(),
            domain_name="default",
            scaling_group="default",
        )
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
                        max_pending_session_resource_slots=ResourceSlot(
                            cpu=Decimal("10"), mem=Decimal("10")
                        ),
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
                            requested_slots=ResourceSlot(cpu=Decimal("3"), mem=Decimal("3")),
                            creation_time=datetime.now(),
                        ),
                        PendingSessionInfo(
                            session_id=SessionId(uuid.uuid4()),
                            requested_slots=ResourceSlot(cpu=Decimal("3"), mem=Decimal("3")),
                            creation_time=datetime.now(),
                        ),
                        PendingSessionInfo(
                            session_id=SessionId(uuid.uuid4()),
                            requested_slots=ResourceSlot(cpu=Decimal("3"), mem=Decimal("3")),
                            creation_time=datetime.now(),
                        ),
                    ]
                }
            ),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        # Should not raise (3+3+3 + 1 = 10 <= 10)
        validator.validate(snapshot, workload)
