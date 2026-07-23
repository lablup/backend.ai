"""
Tests for SchedulingHistoryRepository functionality.
Tests the repository layer with real database operations.

Note: This repository is read-only. History records are created via
SchedulerDBSource.update_with_history() during actual scheduling operations.
These tests verify the search functionality with directly inserted test data.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import pytest

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    OrderDirection,
    ReplicaGroupHistoryOrderField,
)
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.common.identifier.replica_group_history import ReplicaGroupHistoryID
from ai.backend.common.schema.deployment import IntOrPercent, ReplicaGroupRolloutSpec
from ai.backend.common.types import BinarySize, KernelId, ResourceSlot, SessionId
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupHandlerCategory,
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
    RouteStatus,
)
from ai.backend.manager.data.kernel.types import KernelSchedulingPhase
from ai.backend.manager.data.session.types import (
    SchedulingResult,
    SessionStatus,
)
from ai.backend.manager.errors.deployment import ReplicaGroupNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.replica_group_history import ReplicaGroupHistoryRow
from ai.backend.manager.models.replica_group_history.conditions import (
    ReplicaGroupHistoryConditions,
)
from ai.backend.manager.models.replica_group_history.orders import resolve_replica_group_order
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.scheduling_history import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
from ai.backend.manager.models.scheduling_history.conditions import (
    DeploymentHistoryConditions,
    KernelSchedulingHistoryConditions,
    RouteHistoryConditions,
    SessionSchedulingHistoryConditions,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.scheduling_history import (
    SchedulingHistoryRepository,
)
from ai.backend.manager.repositories.scheduling_history.types import (
    ReplicaGroupHistorySearchScope,
)
from ai.backend.testutils.db import with_tables

_ROLLOUT = ReplicaGroupRolloutSpec(
    max_surge=IntOrPercent(count=1),
    max_unavailable=IntOrPercent(count=0),
)


@dataclass(frozen=True)
class _SeededHistory:
    """Ids of the seeded replica groups and the history rows attached to them."""

    deployment_id: DeploymentID
    target_group_id: ReplicaGroupID
    sibling_group_id: ReplicaGroupID
    target_lifecycle_ids: list[ReplicaGroupHistoryID]
    target_scaling_id: ReplicaGroupHistoryID
    sibling_lifecycle_id: ReplicaGroupHistoryID

    @property
    def target_ids(self) -> set[ReplicaGroupHistoryID]:
        return {*self.target_lifecycle_ids, self.target_scaling_id}


@dataclass(frozen=True)
class _PaginationCase:
    """One offset-pagination request and the page it must produce."""

    limit: int
    offset: int
    expected_len: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class _CategoryCase:
    """One handler category and the phases its rows carry, per replica group."""

    category: ReplicaGroupHandlerCategory
    expected_target_phases: list[str]
    expected_sibling_phases: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class _OrderCase:
    """One ordering request and the attempts sequence it must produce."""

    direction: OrderDirection
    expected_attempts: list[int]


class TestSchedulingHistoryRepository:
    """Test cases for SchedulingHistoryRepository (read-only)"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup.

        Note: SQLAlchemy ORM mapper initialization requires all related Row models
        to be imported and included in with_tables, even if they don't have direct
        FK relationships with scheduling_history tables.
        """
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                # Base tables required for ORM mapper initialization
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ContainerRegistryRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                DeploymentPolicyRow,
                DeploymentAutoScalingPolicyRow,
                RuntimeVariantRow,
                DeploymentRevisionPresetRow,
                DeploymentRevisionRow,
                SessionRow,
                AgentRow,
                KernelRow,
                ReplicaGroupRow,
                RoutingRow,
                ResourcePresetRow,
                # Scheduling history tables (no FK dependencies)
                SessionSchedulingHistoryRow,
                KernelSchedulingHistoryRow,
                DeploymentHistoryRow,
                RouteHistoryRow,
                ReplicaGroupHistoryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def scheduling_history_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[SchedulingHistoryRepository, None]:
        """Create SchedulingHistoryRepository instance with database"""
        repo = SchedulingHistoryRepository(db=db_with_cleanup)
        yield repo

    # ========== Session History Tests ==========

    async def test_search_session_history_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching session history with pagination"""
        session_id = SessionId(uuid.uuid4())

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(5):
                row = SessionSchedulingHistoryRow(
                    session_id=session_id,
                    phase=f"PHASE_{i}",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"Message {i}",
                    attempts=1,
                )
                db_sess.add(row)
            await db_sess.flush()

        # Search with pagination
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=2, offset=0),
            conditions=[SessionSchedulingHistoryConditions.by_session_id(session_id)],
            orders=[],
        )
        result = await scheduling_history_repository.search_session_history(querier)

        assert len(result.items) == 2
        assert result.total_count == 5
        assert result.has_next_page is True
        assert result.has_previous_page is False

    async def test_search_session_history_by_session_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching session history filtered by session_id"""
        session_id_1 = SessionId(uuid.uuid4())
        session_id_2 = SessionId(uuid.uuid4())

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            # Create history for session 1
            for i in range(3):
                row = SessionSchedulingHistoryRow(
                    session_id=session_id_1,
                    phase=f"PHASE_{i}",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"Session 1 - Message {i}",
                    attempts=1,
                )
                db_sess.add(row)

            # Create history for session 2
            for i in range(2):
                row = SessionSchedulingHistoryRow(
                    session_id=session_id_2,
                    phase=f"PHASE_{i}",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"Session 2 - Message {i}",
                    attempts=1,
                )
                db_sess.add(row)
            await db_sess.flush()

        # Search for session 1 only
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[SessionSchedulingHistoryConditions.by_session_id(session_id_1)],
            orders=[],
        )
        result = await scheduling_history_repository.search_session_history(querier)

        assert result.total_count == 3
        assert all(item.session_id == session_id_1 for item in result.items)

    async def test_search_session_history_by_result(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching session history filtered by result"""
        session_id = SessionId(uuid.uuid4())

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            # Success records
            for i in range(3):
                row = SessionSchedulingHistoryRow(
                    session_id=session_id,
                    phase=f"PHASE_{i}",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"Success {i}",
                    attempts=1,
                )
                db_sess.add(row)

            # Failure records
            for i in range(2):
                row = SessionSchedulingHistoryRow(
                    session_id=session_id,
                    phase=f"FAIL_PHASE_{i}",
                    result=str(SchedulingResult.FAILURE),
                    error_code="TEST_ERROR",
                    message=f"Failure {i}",
                    attempts=1,
                )
                db_sess.add(row)
            await db_sess.flush()

        # Search for failures only
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[
                SessionSchedulingHistoryConditions.by_session_id(session_id),
                SessionSchedulingHistoryConditions.by_results([SchedulingResult.FAILURE]),
            ],
            orders=[],
        )
        result = await scheduling_history_repository.search_session_history(querier)

        assert result.total_count == 2
        assert all(item.result == SchedulingResult.FAILURE for item in result.items)

    async def test_search_session_history_with_status_transition(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching session history with from/to status"""
        session_id = SessionId(uuid.uuid4())

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            row = SessionSchedulingHistoryRow(
                session_id=session_id,
                phase="SCHEDULE",
                from_status=str(SessionStatus.PENDING),
                to_status=str(SessionStatus.SCHEDULED),
                result=str(SchedulingResult.SUCCESS),
                message="Scheduled successfully",
                attempts=1,
            )
            db_sess.add(row)
            await db_sess.flush()

        # Search
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[SessionSchedulingHistoryConditions.by_session_id(session_id)],
            orders=[],
        )
        result = await scheduling_history_repository.search_session_history(querier)

        assert result.total_count == 1
        item = result.items[0]
        assert item.from_status == SessionStatus.PENDING
        assert item.to_status == SessionStatus.SCHEDULED

    # ========== Kernel History Tests ==========

    async def test_search_kernel_history_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching kernel history with pagination"""
        kernel_id = KernelId(uuid.uuid4())
        session_id = SessionId(uuid.uuid4())

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(5):
                row = KernelSchedulingHistoryRow(
                    kernel_id=kernel_id,
                    session_id=session_id,
                    phase=f"PHASE_{i}",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"Message {i}",
                    attempts=1,
                )
                db_sess.add(row)
            await db_sess.flush()

        # Search with pagination
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=2, offset=0),
            conditions=[KernelSchedulingHistoryConditions.by_kernel_id(kernel_id)],
            orders=[],
        )
        result = await scheduling_history_repository.search_kernel_history(querier)

        assert len(result.items) == 2
        assert result.total_count == 5
        assert result.has_next_page is True
        assert result.has_previous_page is False

    async def test_search_kernel_history_with_status_transition(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching kernel history with from/to status"""
        kernel_id = KernelId(uuid.uuid4())
        session_id = SessionId(uuid.uuid4())

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            row = KernelSchedulingHistoryRow(
                kernel_id=kernel_id,
                session_id=session_id,
                phase="PREPARING",
                from_status=str(KernelSchedulingPhase.PREPARING),
                to_status=str(KernelSchedulingPhase.PREPARED),
                result=str(SchedulingResult.SUCCESS),
                message="Kernel prepared",
                attempts=1,
            )
            db_sess.add(row)
            await db_sess.flush()

        # Search
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[KernelSchedulingHistoryConditions.by_kernel_id(kernel_id)],
            orders=[],
        )
        result = await scheduling_history_repository.search_kernel_history(querier)

        assert result.total_count == 1
        item = result.items[0]
        assert item.from_status == KernelSchedulingPhase.PREPARING
        assert item.to_status == KernelSchedulingPhase.PREPARED

    # ========== Deployment History Tests ==========

    async def test_search_deployment_history_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching deployment history with pagination"""
        deployment_id = uuid.uuid4()

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(5):
                row = DeploymentHistoryRow(
                    deployment_id=deployment_id,
                    phase=f"PHASE_{i}",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"Message {i}",
                    attempts=1,
                )
                db_sess.add(row)
            await db_sess.flush()

        # Search with pagination
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=2, offset=0),
            conditions=[DeploymentHistoryConditions.by_deployment_id(deployment_id)],
            orders=[],
        )
        result = await scheduling_history_repository.search_deployment_history(querier)

        assert len(result.items) == 2
        assert result.total_count == 5
        assert result.has_next_page is True
        assert result.has_previous_page is False

    async def test_search_deployment_history_by_result(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching deployment history filtered by result"""
        deployment_id = uuid.uuid4()

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            # Success records
            for i in range(2):
                row = DeploymentHistoryRow(
                    deployment_id=deployment_id,
                    phase=f"PHASE_{i}",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"Success {i}",
                    attempts=1,
                )
                db_sess.add(row)

            # Failure records
            for i in range(3):
                row = DeploymentHistoryRow(
                    deployment_id=deployment_id,
                    phase=f"FAIL_PHASE_{i}",
                    result=str(SchedulingResult.FAILURE),
                    error_code="RESOURCE_LIMIT",
                    message=f"Failure {i}",
                    attempts=1,
                )
                db_sess.add(row)
            await db_sess.flush()

        # Search for failures only
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[
                DeploymentHistoryConditions.by_deployment_id(deployment_id),
                DeploymentHistoryConditions.by_results([SchedulingResult.FAILURE]),
            ],
            orders=[],
        )
        result = await scheduling_history_repository.search_deployment_history(querier)

        assert result.total_count == 3
        assert all(item.result == SchedulingResult.FAILURE for item in result.items)

    # ========== Route History Tests ==========

    async def test_search_route_history_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching route history with pagination"""
        route_id = uuid.uuid4()
        deployment_id = uuid.uuid4()

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(5):
                row = RouteHistoryRow(
                    route_id=route_id,
                    deployment_id=deployment_id,
                    phase=f"PHASE_{i}",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"Message {i}",
                    attempts=1,
                )
                db_sess.add(row)
            await db_sess.flush()

        # Search with pagination
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=2, offset=0),
            conditions=[RouteHistoryConditions.by_route_id(route_id)],
            orders=[],
        )
        result = await scheduling_history_repository.search_route_history(querier)

        assert len(result.items) == 2
        assert result.total_count == 5
        assert result.has_next_page is True
        assert result.has_previous_page is False

    async def test_search_route_history_with_status_transition(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching route history with from/to status"""
        route_id = uuid.uuid4()
        deployment_id = uuid.uuid4()

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            row = RouteHistoryRow(
                route_id=route_id,
                deployment_id=deployment_id,
                phase="PROVISION",
                from_status=RouteStatus.PROVISIONING.value,
                to_status=RouteStatus.RUNNING.value,
                result=str(SchedulingResult.SUCCESS),
                message="Route provisioned",
                attempts=1,
            )
            db_sess.add(row)
            await db_sess.flush()

        # Search
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[RouteHistoryConditions.by_route_id(route_id)],
            orders=[],
        )
        result = await scheduling_history_repository.search_route_history(querier)

        assert result.total_count == 1
        item = result.items[0]
        assert item.from_status == RouteStatus.PROVISIONING.value
        assert item.to_status == RouteStatus.RUNNING.value

    async def test_search_route_history_by_deployment_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test searching route history filtered by deployment_id"""
        deployment_id_1 = uuid.uuid4()
        deployment_id_2 = uuid.uuid4()

        # Insert test data directly
        async with db_with_cleanup.begin_session() as db_sess:
            # Create history for deployment 1
            for i in range(3):
                row = RouteHistoryRow(
                    route_id=uuid.uuid4(),
                    deployment_id=deployment_id_1,
                    phase=f"PHASE_{i}",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"Deployment 1 - Message {i}",
                    attempts=1,
                )
                db_sess.add(row)

            # Create history for deployment 2
            for i in range(2):
                row = RouteHistoryRow(
                    route_id=uuid.uuid4(),
                    deployment_id=deployment_id_2,
                    phase=f"PHASE_{i}",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"Deployment 2 - Message {i}",
                    attempts=1,
                )
                db_sess.add(row)
            await db_sess.flush()

        # Search for deployment 1 only
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[RouteHistoryConditions.by_deployment_id(deployment_id_1)],
            orders=[],
        )
        result = await scheduling_history_repository.search_route_history(querier)

        assert result.total_count == 3
        assert all(item.deployment_id == deployment_id_1 for item in result.items)

    # ========== Replica Group History Tests ==========

    @pytest.fixture
    async def seeded(self, db_with_cleanup: ExtendedAsyncSAEngine) -> _SeededHistory:
        """Seed one deployment with two replica groups and history on both.

        The target group carries two lifecycle rows and one scaling row so the
        category axis has both sides; the sibling group carries one row that a
        scoped query must leave out. Rows go in through the session directly so
        a broken repository cannot also break the arrangement.
        """
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        sgroup_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"
        user_policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
        project_policy_name = f"test-proj-policy-{uuid.uuid4().hex[:8]}"
        user_uuid = uuid.uuid4()
        group_id = uuid.uuid4()
        deployment_id = DeploymentID(uuid.uuid4())
        target_group_id = ReplicaGroupID(uuid.uuid4())
        sibling_group_id = ReplicaGroupID(uuid.uuid4())
        target_lifecycle_ids = [ReplicaGroupHistoryID(uuid.uuid4()) for _ in range(2)]
        target_scaling_id = ReplicaGroupHistoryID(uuid.uuid4())
        sibling_lifecycle_id = ReplicaGroupHistoryID(uuid.uuid4())
        now = datetime.now(tz=UTC)

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    name=domain_name,
                    description="Test domain",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    allowed_docker_registries=[],
                )
            )
            db_sess.add(
                ScalingGroupRow(
                    name=sgroup_name,
                    description="Test scaling group",
                    is_active=True,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                )
            )
            db_sess.add(
                UserResourcePolicyRow(
                    name=user_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=project_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=int(BinarySize.from_str("100GiB")),
                    max_network_count=5,
                )
            )
            await db_sess.flush()
            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"testuser-{user_uuid.hex[:8]}",
                    email=f"test-{user_uuid.hex[:8]}@example.com",
                    password=PasswordInfo(
                        password="test_password",
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=100_000,
                        salt_size=32,
                    ),
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy=user_policy_name,
                )
            )
            db_sess.add(
                GroupRow(
                    id=group_id,
                    name=f"test-group-{uuid.uuid4().hex[:8]}",
                    domain_name=domain_name,
                    resource_policy=project_policy_name,
                )
            )
            await db_sess.flush()
            db_sess.add(
                EndpointRow(
                    id=deployment_id,
                    name=f"test-endpoint-{uuid.uuid4().hex[:8]}",
                    created_user=user_uuid,
                    session_owner=user_uuid,
                    domain=domain_name,
                    project=group_id,
                    resource_group=sgroup_name,
                    desired_replicas=1,
                    open_to_public=False,
                    lifecycle_stage=EndpointLifecycle.CREATED,
                )
            )
            await db_sess.flush()
            db_sess.add_all([
                ReplicaGroupRow(
                    id=gid,
                    deployment_id=deployment_id,
                    desired_current_replica_count=1,
                    desired_target_replica_count=0,
                    lifecycle=ReplicaGroupLifecycle.STABLE,
                    scaling_status=ReplicaGroupScalingStatus.STABLE,
                    rollout=_ROLLOUT,
                )
                for gid in (target_group_id, sibling_group_id)
            ])
            await db_sess.flush()
            db_sess.add_all([
                ReplicaGroupHistoryRow(
                    id=hid,
                    replica_group_id=target_group_id,
                    deployment_id=deployment_id,
                    category=ReplicaGroupHandlerCategory.LIFECYCLE,
                    phase="DEPLOYING",
                    from_status="CREATED",
                    to_status="STABLE",
                    result=str(SchedulingResult.SUCCESS),
                    message=f"lifecycle transition {offset}",
                    attempts=offset + 1,
                    created_at=now + timedelta(seconds=offset),
                    updated_at=now + timedelta(seconds=offset),
                )
                for offset, hid in enumerate(target_lifecycle_ids)
            ])
            db_sess.add(
                ReplicaGroupHistoryRow(
                    id=target_scaling_id,
                    replica_group_id=target_group_id,
                    deployment_id=deployment_id,
                    category=ReplicaGroupHandlerCategory.SCALING,
                    phase="SCALING_OUT",
                    from_status="STABLE",
                    to_status="SCALING_OUT",
                    result=str(SchedulingResult.SUCCESS),
                    message="scale out",
                    attempts=3,
                    created_at=now + timedelta(seconds=2),
                    updated_at=now + timedelta(seconds=2),
                )
            )
            db_sess.add(
                ReplicaGroupHistoryRow(
                    id=sibling_lifecycle_id,
                    replica_group_id=sibling_group_id,
                    deployment_id=deployment_id,
                    category=ReplicaGroupHandlerCategory.LIFECYCLE,
                    phase="TERMINATING",
                    from_status="STABLE",
                    to_status="TERMINATED",
                    result=str(SchedulingResult.SUCCESS),
                    message="sibling transition",
                    attempts=1,
                    created_at=now,
                    updated_at=now,
                )
            )
            await db_sess.commit()

        return _SeededHistory(
            deployment_id=deployment_id,
            target_group_id=target_group_id,
            sibling_group_id=sibling_group_id,
            target_lifecycle_ids=target_lifecycle_ids,
            target_scaling_id=target_scaling_id,
            sibling_lifecycle_id=sibling_lifecycle_id,
        )

    # ========== admin search (unscoped) ==========

    async def test_admin_search_spans_every_replica_group(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
        seeded: _SeededHistory,
    ) -> None:
        result = await scheduling_history_repository.admin_search_replica_group_history(
            BatchQuerier(pagination=OffsetPagination(limit=50, offset=0))
        )

        assert {item.id for item in result.items} == {
            *seeded.target_ids,
            seeded.sibling_lifecycle_id,
        }
        assert result.total_count == 4

    @pytest.mark.parametrize(
        "case",
        [
            _PaginationCase(
                limit=2, offset=0, expected_len=2, has_next_page=True, has_previous_page=False
            ),
            _PaginationCase(
                limit=2, offset=2, expected_len=2, has_next_page=False, has_previous_page=True
            ),
            _PaginationCase(
                limit=10, offset=0, expected_len=4, has_next_page=False, has_previous_page=False
            ),
            _PaginationCase(
                limit=2, offset=4, expected_len=0, has_next_page=False, has_previous_page=True
            ),
        ],
        ids=lambda case: f"limit{case.limit}-offset{case.offset}",
    )
    async def test_admin_search_paginates(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
        seeded: _SeededHistory,
        case: _PaginationCase,
    ) -> None:
        result = await scheduling_history_repository.admin_search_replica_group_history(
            BatchQuerier(pagination=OffsetPagination(limit=case.limit, offset=case.offset))
        )

        assert len(result.items) == case.expected_len
        assert result.total_count == 4
        assert result.has_next_page is case.has_next_page
        assert result.has_previous_page is case.has_previous_page

    @pytest.mark.parametrize(
        "case",
        [
            _CategoryCase(
                category=ReplicaGroupHandlerCategory.LIFECYCLE,
                expected_target_phases=["DEPLOYING", "DEPLOYING"],
                expected_sibling_phases=["TERMINATING"],
            ),
            _CategoryCase(
                category=ReplicaGroupHandlerCategory.SCALING,
                expected_target_phases=["SCALING_OUT"],
            ),
        ],
        ids=lambda case: case.category.value,
    )
    async def test_admin_search_narrows_by_querier_condition(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
        seeded: _SeededHistory,
        case: _CategoryCase,
    ) -> None:
        result = await scheduling_history_repository.admin_search_replica_group_history(
            BatchQuerier(
                pagination=OffsetPagination(limit=50, offset=0),
                conditions=[ReplicaGroupHistoryConditions.by_category(case.category)],
            )
        )

        assert sorted(item.phase for item in result.items) == sorted(
            case.expected_target_phases + case.expected_sibling_phases
        )

    # ========== scoped search ==========

    async def test_scoped_search_excludes_the_sibling_group(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
        seeded: _SeededHistory,
    ) -> None:
        result = await scheduling_history_repository.scoped_search_replica_group_history(
            BatchQuerier(pagination=OffsetPagination(limit=50, offset=0)),
            ReplicaGroupHistorySearchScope(replica_group_id=seeded.target_group_id),
        )

        assert {item.id for item in result.items} == seeded.target_ids
        assert result.total_count == 3

    @pytest.mark.parametrize(
        "case",
        [
            _CategoryCase(
                category=ReplicaGroupHandlerCategory.LIFECYCLE,
                expected_target_phases=["DEPLOYING", "DEPLOYING"],
                expected_sibling_phases=["TERMINATING"],
            ),
            _CategoryCase(
                category=ReplicaGroupHandlerCategory.SCALING,
                expected_target_phases=["SCALING_OUT"],
            ),
        ],
        ids=lambda case: case.category.value,
    )
    async def test_scoped_search_intersects_the_querier_condition(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
        seeded: _SeededHistory,
        case: _CategoryCase,
    ) -> None:
        """The scope bounds the rows; the querier condition narrows within it."""
        result = await scheduling_history_repository.scoped_search_replica_group_history(
            BatchQuerier(
                pagination=OffsetPagination(limit=50, offset=0),
                conditions=[ReplicaGroupHistoryConditions.by_category(case.category)],
            ),
            ReplicaGroupHistorySearchScope(replica_group_id=seeded.target_group_id),
        )

        assert sorted(item.phase for item in result.items) == sorted(case.expected_target_phases)

    @pytest.mark.parametrize(
        "case",
        [
            _OrderCase(direction=OrderDirection.ASC, expected_attempts=[1, 2, 3]),
            _OrderCase(direction=OrderDirection.DESC, expected_attempts=[3, 2, 1]),
        ],
        ids=lambda case: case.direction.value,
    )
    async def test_scoped_search_applies_the_order(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
        seeded: _SeededHistory,
        case: _OrderCase,
    ) -> None:
        result = await scheduling_history_repository.scoped_search_replica_group_history(
            BatchQuerier(
                pagination=OffsetPagination(limit=50, offset=0),
                orders=[
                    resolve_replica_group_order(
                        ReplicaGroupHistoryOrderField.ATTEMPTS, case.direction
                    )
                ],
            ),
            ReplicaGroupHistorySearchScope(replica_group_id=seeded.target_group_id),
        )

        assert [item.attempts for item in result.items] == case.expected_attempts

    async def test_scoped_search_rejects_an_unknown_replica_group(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
        seeded: _SeededHistory,
    ) -> None:
        """The scope's existence check runs before the query."""
        with pytest.raises(ReplicaGroupNotFound):
            await scheduling_history_repository.scoped_search_replica_group_history(
                BatchQuerier(pagination=OffsetPagination(limit=50, offset=0)),
                ReplicaGroupHistorySearchScope(replica_group_id=ReplicaGroupID(uuid.uuid4())),
            )

    # ========== deployment resolution ==========

    async def test_resolve_returns_the_owning_deployment(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
        seeded: _SeededHistory,
    ) -> None:
        deployment_id = await scheduling_history_repository.resolve_replica_group_deployment(
            seeded.target_group_id
        )

        assert deployment_id == seeded.deployment_id

    async def test_resolve_rejects_an_unknown_replica_group(
        self,
        scheduling_history_repository: SchedulingHistoryRepository,
        seeded: _SeededHistory,
    ) -> None:
        with pytest.raises(ReplicaGroupNotFound):
            await scheduling_history_repository.resolve_replica_group_deployment(
                ReplicaGroupID(uuid.uuid4())
            )
