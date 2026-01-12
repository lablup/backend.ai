"""Tests for user resource limit validator."""

from decimal import Decimal

import pytest

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.sokovan.scheduler.provisioner.validators import (
    UserResourceLimitValidator,
    UserResourceQuotaExceeded,
)
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


class TestUserResourceLimitValidator:
    @pytest.fixture
    def validator(self) -> UserResourceLimitValidator:
        return UserResourceLimitValidator()

    def test_passes_when_under_limit(
        self,
        validator: UserResourceLimitValidator,
        user_specific_small_workload: SessionWorkload,
    ) -> None:
        workload = user_specific_small_workload
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={workload.user_uuid: ResourceSlot(cpu=Decimal("3"), mem=Decimal("3"))},
                by_group={},
                by_domain={},
                by_agent={},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},
                user_policies={
                    workload.user_uuid: UserResourcePolicy(
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
            known_slot_types={},
        )

        # Should not raise (3 + 2 <= 10)
        validator.validate(snapshot, workload)

    def test_fails_when_exceeds_limit(
        self,
        validator: UserResourceLimitValidator,
        user_specific_medium_workload: SessionWorkload,
    ) -> None:
        workload = user_specific_medium_workload
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={workload.user_uuid: ResourceSlot(cpu=Decimal("8"), mem=Decimal("8"))},
                by_group={},
                by_domain={},
                by_agent={},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},
                user_policies={
                    workload.user_uuid: UserResourcePolicy(
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
            known_slot_types={},
        )

        with pytest.raises(UserResourceQuotaExceeded) as exc_info:
            validator.validate(snapshot, workload)
        assert "Your main-keypair resource quota is exceeded" in str(exc_info.value)

    def test_passes_when_no_policy(
        self,
        validator: UserResourceLimitValidator,
        user_specific_minimal_workload: SessionWorkload,
    ) -> None:
        workload = user_specific_minimal_workload
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={}, by_user={}, by_group={}, by_domain={}, by_agent={}
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
            known_slot_types={},
        )

        # Should not raise when no user-specific policy is defined
        validator.validate(snapshot, workload)

    def test_passes_when_no_current_occupancy(
        self,
        validator: UserResourceLimitValidator,
        user_specific_medium_workload: SessionWorkload,
    ) -> None:
        workload = user_specific_medium_workload
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={},  # No current occupancy for user
                by_group={},
                by_domain={},
                by_agent={},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},
                user_policies={
                    workload.user_uuid: UserResourcePolicy(
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
            known_slot_types={},
        )

        # Should not raise (0 + 5 <= 10)
        validator.validate(snapshot, workload)
