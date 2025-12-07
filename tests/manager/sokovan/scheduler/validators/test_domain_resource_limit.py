"""Tests for domain resource limit validator."""

from decimal import Decimal

import pytest

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.sokovan.scheduler.provisioner.validators import (
    DomainResourceLimitValidator,
    DomainResourceQuotaExceeded,
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


class TestDomainResourceLimitValidator:
    @pytest.fixture
    def validator(self) -> DomainResourceLimitValidator:
        return DomainResourceLimitValidator()

    def test_passes_when_under_limit(
        self,
        validator: DomainResourceLimitValidator,
        test_domain_small_resource_workload: SessionWorkload,
    ) -> None:
        workload = test_domain_small_resource_workload
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={},
                by_group={},
                by_domain={workload.domain_name: ResourceSlot(cpu=Decimal("3"), mem=Decimal("3"))},
                by_agent={},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},
                user_policies={},
                group_limits={},
                domain_limits={
                    workload.domain_name: ResourceSlot(cpu=Decimal("10"), mem=Decimal("10"))
                },
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
        validator: DomainResourceLimitValidator,
        test_domain_medium_resource_workload: SessionWorkload,
    ) -> None:
        workload = test_domain_medium_resource_workload
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={},
                by_group={},
                by_domain={workload.domain_name: ResourceSlot(cpu=Decimal("8"), mem=Decimal("8"))},
                by_agent={},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},
                user_policies={},
                group_limits={},
                domain_limits={
                    workload.domain_name: ResourceSlot(cpu=Decimal("10"), mem=Decimal("10"))
                },
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        with pytest.raises(DomainResourceQuotaExceeded) as exc_info:
            validator.validate(snapshot, workload)
        assert "Your domain resource quota is exceeded" in str(exc_info.value)

    def test_passes_when_no_limit(
        self,
        validator: DomainResourceLimitValidator,
        test_domain_large_resource_workload: SessionWorkload,
    ) -> None:
        workload = test_domain_large_resource_workload
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={},
                by_group={},
                by_domain={
                    workload.domain_name: ResourceSlot(cpu=Decimal("50"), mem=Decimal("50"))
                },
                by_agent={},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},
                user_policies={},
                group_limits={},
                domain_limits={},  # No limit for domain
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        # Should not raise when no limit is defined
        validator.validate(snapshot, workload)

    def test_passes_when_no_current_occupancy(
        self,
        validator: DomainResourceLimitValidator,
        test_domain_medium_resource_workload: SessionWorkload,
    ) -> None:
        workload = test_domain_medium_resource_workload
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={},
                by_group={},
                by_domain={},  # No current occupancy for domain,
                by_agent={},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},
                user_policies={},
                group_limits={},
                domain_limits={
                    workload.domain_name: ResourceSlot(cpu=Decimal("10"), mem=Decimal("10"))
                },
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        # Should not raise (0 + 5 <= 10)
        validator.validate(snapshot, workload)
