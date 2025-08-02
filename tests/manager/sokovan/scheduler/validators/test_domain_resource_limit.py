"""Tests for domain resource limit validator."""

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
)
from ai.backend.manager.sokovan.scheduler.validators import (
    DomainResourceLimitValidator,
    DomainResourceQuotaExceeded,
)


class TestDomainResourceLimitValidator:
    @pytest.fixture
    def domain_name(self) -> str:
        return "test-domain"

    @pytest.fixture
    def validator(self) -> DomainResourceLimitValidator:
        return DomainResourceLimitValidator()

    def test_passes_when_under_limit(
        self, validator: DomainResourceLimitValidator, domain_name: str
    ) -> None:
        workload = SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("2"), mem=Decimal("2")),
            user_uuid=uuid.uuid4(),
            group_id=uuid.uuid4(),
            domain_name=domain_name,
        )
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={},
                by_group={},
                by_domain={domain_name: ResourceSlot(cpu=Decimal("3"), mem=Decimal("3"))},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},
                user_policies={},
                group_limits={},
                domain_limits={domain_name: ResourceSlot(cpu=Decimal("10"), mem=Decimal("10"))},
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
        )

        # Should not raise (3 + 2 <= 10)
        validator.validate(snapshot, workload)

    def test_fails_when_exceeds_limit(
        self, validator: DomainResourceLimitValidator, domain_name: str
    ) -> None:
        workload = SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("5"), mem=Decimal("5")),
            user_uuid=uuid.uuid4(),
            group_id=uuid.uuid4(),
            domain_name=domain_name,
        )
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={},
                by_group={},
                by_domain={domain_name: ResourceSlot(cpu=Decimal("8"), mem=Decimal("8"))},
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},
                user_policies={},
                group_limits={},
                domain_limits={domain_name: ResourceSlot(cpu=Decimal("10"), mem=Decimal("10"))},
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
        )

        with pytest.raises(DomainResourceQuotaExceeded) as exc_info:
            validator.validate(snapshot, workload)
        assert "Your domain resource quota is exceeded" in str(exc_info.value)

    def test_passes_when_no_limit(
        self, validator: DomainResourceLimitValidator, domain_name: str
    ) -> None:
        workload = SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            user_uuid=uuid.uuid4(),
            group_id=uuid.uuid4(),
            domain_name=domain_name,
        )
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={},
                by_group={},
                by_domain={domain_name: ResourceSlot(cpu=Decimal("50"), mem=Decimal("50"))},
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
        )

        # Should not raise when no limit is defined
        validator.validate(snapshot, workload)

    def test_passes_when_no_current_occupancy(
        self, validator: DomainResourceLimitValidator, domain_name: str
    ) -> None:
        workload = SessionWorkload(
            session_id=SessionId(uuid.uuid4()),
            access_key=AccessKey("user1"),
            requested_slots=ResourceSlot(cpu=Decimal("5"), mem=Decimal("5")),
            user_uuid=uuid.uuid4(),
            group_id=uuid.uuid4(),
            domain_name=domain_name,
        )
        snapshot = SystemSnapshot(
            total_capacity=ResourceSlot(cpu=Decimal("100"), mem=Decimal("100")),
            resource_occupancy=ResourceOccupancySnapshot(
                by_keypair={},
                by_user={},
                by_group={},
                by_domain={},  # No current occupancy for domain
            ),
            resource_policy=ResourcePolicySnapshot(
                keypair_policies={},
                user_policies={},
                group_limits={},
                domain_limits={domain_name: ResourceSlot(cpu=Decimal("10"), mem=Decimal("10"))},
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
        )

        # Should not raise (0 + 5 <= 10)
        validator.validate(snapshot, workload)
