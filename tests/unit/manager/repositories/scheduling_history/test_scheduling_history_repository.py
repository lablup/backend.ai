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

import pytest

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    OrderDirection,
    ReplicaGroupHistoryOrderField,
)
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
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
    async def replica_group_ids(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> tuple[DeploymentID, ReplicaGroupID, ReplicaGroupID]:
        """Create a deployment with two replica groups and return their ids.

        The scoped search checks the replica group exists, so the rows and the
        endpoint they hang off must be real; that in turn needs the domain,
        project, scaling group and user the endpoint points at.
        """
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        sgroup_name = f"test-sgroup-{uuid.uuid4().hex[:8]}"
        user_policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"
        project_policy_name = f"test-proj-policy-{uuid.uuid4().hex[:8]}"
        user_uuid = uuid.uuid4()
        project_id = uuid.uuid4()
        deployment_id = DeploymentID(uuid.uuid4())
        target_group_id = ReplicaGroupID(uuid.uuid4())
        sibling_group_id = ReplicaGroupID(uuid.uuid4())

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
                    id=project_id,
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
                    project=project_id,
                    resource_group=sgroup_name,
                    desired_replicas=1,
                    open_to_public=False,
                    lifecycle_stage=EndpointLifecycle.CREATED,
                )
            )
            await db_sess.flush()
            for group_id in (target_group_id, sibling_group_id):
                db_sess.add(
                    ReplicaGroupRow(
                        id=group_id,
                        deployment_id=deployment_id,
                        desired_current_replica_count=1,
                        desired_target_replica_count=0,
                        lifecycle=ReplicaGroupLifecycle.STABLE,
                        scaling_status=ReplicaGroupScalingStatus.STABLE,
                        rollout=ReplicaGroupRolloutSpec(
                            max_surge=IntOrPercent(count=1),
                            max_unavailable=IntOrPercent(count=0),
                        ),
                    )
                )
            await db_sess.commit()

        return deployment_id, target_group_id, sibling_group_id

    async def test_admin_search_replica_group_history_spans_every_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
        replica_group_ids: tuple[DeploymentID, ReplicaGroupID, ReplicaGroupID],
    ) -> None:
        """Test that the unscoped admin search returns rows from every replica group"""
        deployment_id, target_group_id, sibling_group_id = replica_group_ids

        async with db_with_cleanup.begin_session() as db_sess:
            for group_id in (target_group_id, sibling_group_id):
                db_sess.add(
                    ReplicaGroupHistoryRow(
                        replica_group_id=group_id,
                        deployment_id=deployment_id,
                        category=ReplicaGroupHandlerCategory.LIFECYCLE,
                        phase="DEPLOYING",
                        result=str(SchedulingResult.SUCCESS),
                        message="lifecycle transition",
                        attempts=1,
                    )
                )
            await db_sess.flush()

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )
        result = await scheduling_history_repository.admin_search_replica_group_history(querier)

        assert result.total_count == 2
        assert {item.replica_group_id for item in result.items} == {
            target_group_id,
            sibling_group_id,
        }

    async def test_admin_search_replica_group_history_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
        replica_group_ids: tuple[DeploymentID, ReplicaGroupID, ReplicaGroupID],
    ) -> None:
        """Test searching replica-group history with pagination"""
        deployment_id, target_group_id, _ = replica_group_ids

        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(5):
                db_sess.add(
                    ReplicaGroupHistoryRow(
                        replica_group_id=target_group_id,
                        deployment_id=deployment_id,
                        category=ReplicaGroupHandlerCategory.LIFECYCLE,
                        phase=f"PHASE_{i}",
                        result=str(SchedulingResult.SUCCESS),
                        message=f"Message {i}",
                        attempts=1,
                    )
                )
            await db_sess.flush()

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=2, offset=0),
            conditions=[],
            orders=[],
        )
        result = await scheduling_history_repository.admin_search_replica_group_history(querier)

        assert len(result.items) == 2
        assert result.total_count == 5
        assert result.has_next_page is True
        assert result.has_previous_page is False

    async def test_admin_search_replica_group_history_by_category(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
        replica_group_ids: tuple[DeploymentID, ReplicaGroupID, ReplicaGroupID],
    ) -> None:
        """Test searching replica-group history filtered by handler category"""
        deployment_id, target_group_id, _ = replica_group_ids

        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(3):
                db_sess.add(
                    ReplicaGroupHistoryRow(
                        replica_group_id=target_group_id,
                        deployment_id=deployment_id,
                        category=ReplicaGroupHandlerCategory.LIFECYCLE,
                        phase=f"PHASE_{i}",
                        result=str(SchedulingResult.SUCCESS),
                        message=f"Lifecycle - Message {i}",
                        attempts=1,
                    )
                )
            for i in range(2):
                db_sess.add(
                    ReplicaGroupHistoryRow(
                        replica_group_id=target_group_id,
                        deployment_id=deployment_id,
                        category=ReplicaGroupHandlerCategory.SCALING,
                        phase=f"SCALING_{i}",
                        result=str(SchedulingResult.SUCCESS),
                        message=f"Scaling - Message {i}",
                        attempts=1,
                    )
                )
            await db_sess.flush()

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[
                ReplicaGroupHistoryConditions.by_category(ReplicaGroupHandlerCategory.SCALING)
            ],
            orders=[],
        )
        result = await scheduling_history_repository.admin_search_replica_group_history(querier)

        assert result.total_count == 2
        assert all(item.category == ReplicaGroupHandlerCategory.SCALING for item in result.items)

    async def test_scoped_search_replica_group_history_by_replica_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
        replica_group_ids: tuple[DeploymentID, ReplicaGroupID, ReplicaGroupID],
    ) -> None:
        """Test that the scoped search leaves out the sibling replica group"""
        deployment_id, target_group_id, sibling_group_id = replica_group_ids

        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(3):
                db_sess.add(
                    ReplicaGroupHistoryRow(
                        replica_group_id=target_group_id,
                        deployment_id=deployment_id,
                        category=ReplicaGroupHandlerCategory.LIFECYCLE,
                        phase=f"PHASE_{i}",
                        result=str(SchedulingResult.SUCCESS),
                        message=f"Target - Message {i}",
                        attempts=1,
                    )
                )
            for i in range(2):
                db_sess.add(
                    ReplicaGroupHistoryRow(
                        replica_group_id=sibling_group_id,
                        deployment_id=deployment_id,
                        category=ReplicaGroupHandlerCategory.LIFECYCLE,
                        phase=f"PHASE_{i}",
                        result=str(SchedulingResult.SUCCESS),
                        message=f"Sibling - Message {i}",
                        attempts=1,
                    )
                )
            await db_sess.flush()

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )
        result = await scheduling_history_repository.scoped_search_replica_group_history(
            querier,
            ReplicaGroupHistorySearchScope(replica_group_id=target_group_id),
        )

        assert result.total_count == 3
        assert all(item.replica_group_id == target_group_id for item in result.items)

    async def test_scoped_search_replica_group_history_narrows_within_the_scope(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
        replica_group_ids: tuple[DeploymentID, ReplicaGroupID, ReplicaGroupID],
    ) -> None:
        """Test that a querier condition narrows further, still bounded by the scope"""
        deployment_id, target_group_id, sibling_group_id = replica_group_ids

        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                ReplicaGroupHistoryRow(
                    replica_group_id=target_group_id,
                    deployment_id=deployment_id,
                    category=ReplicaGroupHandlerCategory.SCALING,
                    phase="SCALING_OUT",
                    result=str(SchedulingResult.SUCCESS),
                    message="Target - scaling",
                    attempts=1,
                )
            )
            db_sess.add(
                ReplicaGroupHistoryRow(
                    replica_group_id=target_group_id,
                    deployment_id=deployment_id,
                    category=ReplicaGroupHandlerCategory.LIFECYCLE,
                    phase="DEPLOYING",
                    result=str(SchedulingResult.SUCCESS),
                    message="Target - lifecycle",
                    attempts=1,
                )
            )
            db_sess.add(
                ReplicaGroupHistoryRow(
                    replica_group_id=sibling_group_id,
                    deployment_id=deployment_id,
                    category=ReplicaGroupHandlerCategory.SCALING,
                    phase="SCALING_OUT",
                    result=str(SchedulingResult.SUCCESS),
                    message="Sibling - scaling",
                    attempts=1,
                )
            )
            await db_sess.flush()

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[
                ReplicaGroupHistoryConditions.by_category(ReplicaGroupHandlerCategory.SCALING)
            ],
            orders=[],
        )
        result = await scheduling_history_repository.scoped_search_replica_group_history(
            querier,
            ReplicaGroupHistorySearchScope(replica_group_id=target_group_id),
        )

        assert result.total_count == 1
        assert result.items[0].message == "Target - scaling"

    async def test_scoped_search_replica_group_history_ordering(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
        replica_group_ids: tuple[DeploymentID, ReplicaGroupID, ReplicaGroupID],
    ) -> None:
        """Test that the requested order reaches the query"""
        deployment_id, target_group_id, _ = replica_group_ids

        async with db_with_cleanup.begin_session() as db_sess:
            for attempts in (2, 3, 1):
                db_sess.add(
                    ReplicaGroupHistoryRow(
                        replica_group_id=target_group_id,
                        deployment_id=deployment_id,
                        category=ReplicaGroupHandlerCategory.LIFECYCLE,
                        phase="DEPLOYING",
                        result=str(SchedulingResult.SUCCESS),
                        message=f"Attempts {attempts}",
                        attempts=attempts,
                    )
                )
            await db_sess.flush()

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[
                resolve_replica_group_order(
                    ReplicaGroupHistoryOrderField.ATTEMPTS, OrderDirection.ASC
                )
            ],
        )
        result = await scheduling_history_repository.scoped_search_replica_group_history(
            querier,
            ReplicaGroupHistorySearchScope(replica_group_id=target_group_id),
        )

        assert [item.attempts for item in result.items] == [1, 2, 3]

    async def test_scoped_search_replica_group_history_unknown_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test that the scope's existence check rejects an unknown replica group"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[],
        )

        with pytest.raises(ReplicaGroupNotFound):
            await scheduling_history_repository.scoped_search_replica_group_history(
                querier,
                ReplicaGroupHistorySearchScope(replica_group_id=ReplicaGroupID(uuid.uuid4())),
            )

    async def test_resolve_replica_group_deployment(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
        replica_group_ids: tuple[DeploymentID, ReplicaGroupID, ReplicaGroupID],
    ) -> None:
        """Test resolving the deployment owning a replica group"""
        deployment_id, target_group_id, _ = replica_group_ids

        resolved = await scheduling_history_repository.resolve_replica_group_deployment(
            target_group_id
        )

        assert resolved == deployment_id

    async def test_resolve_replica_group_deployment_unknown_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        scheduling_history_repository: SchedulingHistoryRepository,
    ) -> None:
        """Test that resolving an unknown replica group raises"""
        with pytest.raises(ReplicaGroupNotFound):
            await scheduling_history_repository.resolve_replica_group_deployment(
                ReplicaGroupID(uuid.uuid4())
            )
