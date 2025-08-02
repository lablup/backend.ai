"""Tests for user resource limit validator."""

import uuid
from decimal import Decimal

import pytest

from ai.backend.common.types import AccessKey, ResourceSlot, SessionId
from ai.backend.manager.sokovan.scheduler.types import (
    ConcurrencySnapshot,
    PendingSessionSnapshot,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencySnapshot,
    SessionWorkload,
    SystemSnapshot,
    UserResourcePolicy,
)
from ai.backend.manager.sokovan.scheduler.validators import (
    UserResourceLimitValidator,
    UserResourcePolicyNotFound,
    UserResourceQuotaExceeded,
)


class TestUserResourceLimitValidator:
    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def validator(self) -> UserResourceLimitValidator:
        return UserResourceLimitValidator()

    def test_passes_when_under_limit(
        self, validator: UserResourceLimitValidator, user_id: uuid.UUID
    ) -> None:
        workload = SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("2"), mem=Decimal("2")),
            user_uuid=user_id,
            group_id=uuid.uuid4(),
            domain_name="default",
        )
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={user_id: ResourceSlot(cpu=Decimal("3"), mem=Decimal("3"))},
                by_group={},
                by_domain={},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},
                user_policies={
                    user_id: UserResourcePolicy(
                        name="default",
                        total_resource_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                    )
                },
                group_limits={},
                domain_limits={},
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
        )

        # Should not raise (3 + 2 <= 10)
        validator.validate(snapshot, workload)

    def test_fails_when_exceeds_limit(
        self, validator: UserResourceLimitValidator, user_id: uuid.UUID
    ) -> None:
        workload = SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("5"), mem=Decimal("5")),
            user_uuid=user_id,
            group_id=uuid.uuid4(),
            domain_name="default",
        )
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={user_id: ResourceSlot(cpu=Decimal("8"), mem=Decimal("8"))},
                by_group={},
                by_domain={},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},
                user_policies={
                    user_id: UserResourcePolicy(
                        name="default",
                        total_resource_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                    )
                },
                group_limits={},
                domain_limits={},
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
        )

        with pytest.raises(UserResourceQuotaExceeded) as exc_info:
            validator.validate(snapshot, workload)
        assert "Your main-keypair resource quota is exceeded" in str(exc_info.value)

    def test_fails_when_no_policy(
        self, validator: UserResourceLimitValidator, user_id: uuid.UUID
    ) -> None:
        workload = SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("1"), mem=Decimal("1")),
            user_uuid=user_id,
            group_id=uuid.uuid4(),
            domain_name="default",
        )
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={},
                by_group={},
                by_domain={},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},
                user_policies={},  # No policy for user
                group_limits={},
                domain_limits={},
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
        )

        with pytest.raises(UserResourcePolicyNotFound) as exc_info:
            validator.validate(snapshot, workload)
        assert f"User has no resource policy (uid: {user_id})" in str(exc_info.value)

    def test_passes_when_no_current_occupancy(
        self, validator: UserResourceLimitValidator, user_id: uuid.UUID
    ) -> None:
        workload = SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("5"), mem=Decimal("5")),
            user_uuid=user_id,
            group_id=uuid.uuid4(),
            domain_name="default",
        )
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={},  # No current occupancy for user
                by_group={},
                by_domain={},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},
                user_policies={
                    user_id: UserResourcePolicy(
                        name="default",
                        total_resource_slots=ResourceSlot(cpu=Decimal("10"), mem=Decimal("10")),
                    )
                },
                group_limits={},
                domain_limits={},
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
        )

        # Should not raise (0 + 5 <= 10)
        validator.validate(snapshot, workload)
