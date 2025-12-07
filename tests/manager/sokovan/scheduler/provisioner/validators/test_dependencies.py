"""Tests for dependencies validator."""

import uuid
from decimal import Decimal

import pytest

from ai.backend.common.types import AccessKey, ResourceSlot, SessionId, SessionResult
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.sokovan.scheduler.provisioner.validators import (
    DependenciesNotSatisfied,
    DependenciesValidator,
)
from ai.backend.manager.sokovan.scheduler.types import (
    ConcurrencySnapshot,
    PendingSessionSnapshot,
    ResourceOccupancySnapshot,
    ResourcePolicySnapshot,
    SessionDependencyInfo,
    SessionDependencySnapshot,
    SessionWorkload,
    SystemSnapshot,
)


class TestDependenciesValidator:
    @pytest.fixture
    def validator(self) -> DependenciesValidator:
        return DependenciesValidator()

    def test_passes_when_no_dependencies(self, validator: DependenciesValidator) -> None:
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
                keypair_policies={}, user_policies={}, group_limits={}, domain_limits={}
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(by_session={}),
            known_slot_types={},
        )

        # Should not raise
        validator.validate(snapshot, workload)

    def test_passes_when_dependencies_satisfied(self, validator: DependenciesValidator) -> None:
        session_id = SessionId(uuid.uuid4())
        dep_id = SessionId(uuid.uuid4())
        workload = SessionWorkload(
            session_id=session_id,
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
                keypair_policies={}, user_policies={}, group_limits={}, domain_limits={}
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(
                by_session={
                    session_id: [
                        SessionDependencyInfo(
                            depends_on=dep_id,
                            dependency_name="dep1",
                            dependency_status=SessionStatus.TERMINATED,
                            dependency_result=SessionResult.SUCCESS,
                        )
                    ]
                }
            ),
        )

        # Should not raise
        validator.validate(snapshot, workload)

    def test_fails_when_dependencies_not_satisfied(self, validator: DependenciesValidator) -> None:
        session_id = SessionId(uuid.uuid4())
        dep_id = SessionId(uuid.uuid4())
        workload = SessionWorkload(
            session_id=session_id,
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
                keypair_policies={}, user_policies={}, group_limits={}, domain_limits={}
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(
                by_session={
                    session_id: [
                        SessionDependencyInfo(
                            depends_on=dep_id,
                            dependency_name="dep1",
                            dependency_status=SessionStatus.RUNNING,
                            dependency_result=SessionResult.UNDEFINED,
                        )
                    ]
                }
            ),
        )

        with pytest.raises(DependenciesNotSatisfied) as exc_info:
            validator.validate(snapshot, workload)
        assert "Waiting dependency sessions to finish as success" in str(exc_info.value)
        assert f"dep1 ({dep_id})" in str(exc_info.value)

    def test_fails_when_multiple_dependencies_not_satisfied(
        self, validator: DependenciesValidator
    ) -> None:
        session_id = SessionId(uuid.uuid4())
        dep_id1 = SessionId(uuid.uuid4())
        dep_id2 = SessionId(uuid.uuid4())
        workload = SessionWorkload(
            session_id=session_id,
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
                keypair_policies={}, user_policies={}, group_limits={}, domain_limits={}
            ),
            concurrency=ConcurrencySnapshot(sessions_by_keypair={}, sftp_sessions_by_keypair={}),
            pending_sessions=PendingSessionSnapshot(by_keypair={}),
            session_dependencies=SessionDependencySnapshot(
                by_session={
                    session_id: [
                        SessionDependencyInfo(
                            depends_on=dep_id1,
                            dependency_name="dep1",
                            dependency_status=SessionStatus.TERMINATED,
                            dependency_result=SessionResult.SUCCESS,
                        ),
                        SessionDependencyInfo(
                            depends_on=dep_id2,
                            dependency_name="dep2",
                            dependency_status=SessionStatus.RUNNING,
                            dependency_result=SessionResult.UNDEFINED,
                        ),
                    ]
                }
            ),
        )

        with pytest.raises(DependenciesNotSatisfied) as exc_info:
            validator.validate(snapshot, workload)
        assert "Waiting dependency sessions to finish as success" in str(exc_info.value)
        assert f"dep2 ({dep_id2})" in str(exc_info.value)
        assert f"dep1 ({dep_id1})" not in str(exc_info.value)  # Should not include satisfied dep
