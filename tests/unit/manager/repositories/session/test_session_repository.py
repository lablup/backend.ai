"""
Tests for SessionRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc
from sqlalchemy.orm import selectinload

from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    DefaultForUnspecified,
    KernelId,
    ResourceSlot,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow, ProjectType
from ai.backend.manager.models.kernel import KernelRow, KernelStatus
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_slot import ResourceAllocationRow, ResourceSlotTypeRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow, batch_populate_session_occupied_slots
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.session.repository import SessionRepository
from ai.backend.testutils.db import with_tables


@dataclass
class SessionTestData:
    domain_name: str
    user_id: uuid.UUID
    group_id: uuid.UUID
    session_id: SessionId
    kernel_id: KernelId
    access_key: AccessKey


class TestSessionRepository:
    """Test cases for SessionRepository using real database"""

    @pytest.fixture
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                ScalingGroupRow,
                AgentRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                GroupRow,
                KeyPairRow,
                SessionRow,
                KernelRow,
                ResourceSlotTypeRow,
                ResourceAllocationRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> SessionRepository:
        return SessionRepository(db_with_cleanup)

    @pytest.fixture
    async def session_with_kernel(self, db_with_cleanup: ExtendedAsyncSAEngine) -> SessionTestData:
        """Create a session with kernel for testing search operations."""
        domain_name = "test-domain"
        user_id = uuid.uuid4()
        group_id = uuid.uuid4()
        session_id = SessionId(uuid.uuid4())
        kernel_id = KernelId(uuid.uuid4())
        access_key = AccessKey("TESTKEY12345678")

        async with db_with_cleanup.begin_session() as db_sess:
            # Create domain
            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
                integration_id=None,
            )
            db_sess.add(domain)

            # Create scaling group
            scaling_group = ScalingGroupRow(
                name="default",
                is_active=True,
                is_public=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_sess.add(scaling_group)

            # Create resource policies
            user_resource_policy = UserResourcePolicyRow(
                name="default-user-policy",
                max_vfolder_count=100,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            db_sess.add(user_resource_policy)

            project_resource_policy = ProjectResourcePolicyRow(
                name="default-project-policy",
                max_vfolder_count=100,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
            db_sess.add(project_resource_policy)

            keypair_resource_policy = KeyPairResourcePolicyRow(
                name="default-keypair-policy",
                default_for_unspecified=DefaultForUnspecified.UNLIMITED,
                total_resource_slots=ResourceSlot(),
                max_session_lifetime=0,
                max_concurrent_sessions=10,
                max_concurrent_sftp_sessions=5,
                max_containers_per_session=1,
                idle_timeout=3600,
            )
            db_sess.add(keypair_resource_policy)

            await db_sess.flush()

            # Create user
            user = UserRow(
                uuid=user_id,
                username="testuser",
                email="test@example.com",
                password=None,
                need_password_change=False,
                full_name="Test User",
                description="Test user",
                status=UserStatus.ACTIVE,
                status_info="",
                domain_name=domain_name,
                role=UserRole.USER,
                resource_policy=user_resource_policy.name,
                allowed_client_ip=None,
                totp_key=None,
                main_access_key=None,
            )
            db_sess.add(user)

            # Create group
            group = GroupRow(
                id=group_id,
                name="test-group",
                description="Test group",
                is_active=True,
                domain_name=domain_name,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                resource_policy=project_resource_policy.name,
                type=ProjectType.GENERAL,
            )
            db_sess.add(group)

            await db_sess.flush()

            # Create keypair
            keypair = KeyPairRow(
                user_id="test@example.com",
                user=user_id,
                access_key=access_key,
                secret_key="test-secret-key",
                is_active=True,
                is_admin=False,
                resource_policy=keypair_resource_policy.name,
                rate_limit=1000,
            )
            db_sess.add(keypair)

            await db_sess.flush()

            # Create session
            now = datetime.now(tzutc())
            session = SessionRow(
                id=session_id,
                creation_id="test-creation-id",
                name="test-session",
                session_type=SessionTypes.INTERACTIVE,
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                domain_name=domain_name,
                group_id=group_id,
                user_uuid=user_id,
                access_key=access_key,
                tag=None,
                status=SessionStatus.RUNNING,
                status_info=None,
                status_data=None,
                status_history={},
                result=SessionResult.UNDEFINED,
                created_at=now,
                terminated_at=None,
                starts_at=None,
                startup_command=None,
                callback_url=None,
                occupying_slots=ResourceSlot({"cpu": "1", "mem": "1073741824"}),
                requested_slots=ResourceSlot({"cpu": "1", "mem": "1073741824"}),
                vfolder_mounts=[],
                environ=None,
                bootstrap_script=None,
                use_host_network=False,
                scaling_group_name="default",
            )
            db_sess.add(session)

            await db_sess.flush()

            # Create kernel
            kernel = KernelRow(
                id=kernel_id,
                session_id=session_id,
                session_type=SessionTypes.INTERACTIVE,
                domain_name=domain_name,
                group_id=group_id,
                user_uuid=user_id,
                access_key=access_key,
                cluster_mode=ClusterMode.SINGLE_NODE.value,
                cluster_size=1,
                cluster_role="main",
                cluster_idx=0,
                local_rank=0,
                cluster_hostname="main",
                image="cr.backend.ai/stable/python:latest",
                architecture="x86_64",
                registry="cr.backend.ai",
                agent=None,
                agent_addr=None,
                container_id=None,
                repl_in_port=2000,
                repl_out_port=2001,
                stdin_port=2002,
                stdout_port=2003,
                use_host_network=False,
                status=KernelStatus.RUNNING,
                status_info=None,
                status_data=None,
                status_history={},
                status_changed=now,
                result=SessionResult.UNDEFINED,
                created_at=now,
                terminated_at=None,
                starts_at=None,
                occupied_slots=ResourceSlot({"cpu": "1", "mem": "1073741824"}),
                requested_slots=ResourceSlot({"cpu": "1", "mem": "1073741824"}),
                occupied_shares={},
                environ=None,
                vfolder_mounts=[],
                attached_devices={},
                resource_opts=None,
                preopen_ports=None,
                bootstrap_script=None,
                startup_command=None,
            )
            db_sess.add(kernel)

            await db_sess.commit()

        return SessionTestData(
            domain_name=domain_name,
            user_id=user_id,
            group_id=group_id,
            session_id=session_id,
            kernel_id=kernel_id,
            access_key=access_key,
        )

    # =========================================================================
    # Tests - SearchKernels
    # =========================================================================

    async def test_search_kernels(
        self,
        repository: SessionRepository,
        session_with_kernel: SessionTestData,
    ) -> None:
        """Test search_kernels returns kernel info when kernels exist"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        result = await repository.search_kernels(querier)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False

        kernel_info = result.items[0]
        assert kernel_info.id == session_with_kernel.kernel_id
        assert kernel_info.session.session_id == str(session_with_kernel.session_id)

    async def test_search_kernels_empty_result(
        self,
        repository: SessionRepository,
    ) -> None:
        """Test search_kernels returns empty result when no kernels exist"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        result = await repository.search_kernels(querier)

        assert result.total_count == 0
        assert len(result.items) == 0
        assert result.has_next_page is False
        assert result.has_previous_page is False

    # =========================================================================
    # Tests - SearchSessions
    # =========================================================================

    async def test_search_sessions(
        self,
        repository: SessionRepository,
        session_with_kernel: SessionTestData,
    ) -> None:
        """Test search returns session data when sessions exist"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        result = await repository.search(querier=querier)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False

        session_data = result.items[0]
        assert session_data.id == session_with_kernel.session_id
        assert session_data.name == "test-session"
        assert session_data.domain_name == session_with_kernel.domain_name
        assert session_data.group_id == session_with_kernel.group_id
        assert session_data.user_uuid == session_with_kernel.user_id
        assert session_data.access_key == session_with_kernel.access_key

    async def test_search_sessions_empty_result(
        self,
        repository: SessionRepository,
    ) -> None:
        """Test search returns empty result when no sessions exist"""
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        result = await repository.search(querier=querier)

        assert result.total_count == 0
        assert len(result.items) == 0
        assert result.has_next_page is False
        assert result.has_previous_page is False


class TestBatchPopulateSessionOccupiedSlots:
    """Test batch_populate_session_occupied_slots computes occupied_slots
    from the normalized resource_allocations table instead of the deprecated
    JSONB column."""

    @pytest.fixture
    async def db_with_resource_tables(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                AgentRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                GroupRow,
                KeyPairRow,
                SessionRow,
                KernelRow,
                ResourceSlotTypeRow,
                ResourceAllocationRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def session_with_allocations(
        self, db_with_resource_tables: ExtendedAsyncSAEngine
    ) -> SessionTestData:
        """Create a session with resource_allocations (but empty JSONB occupying_slots)."""
        domain_name = "test-domain"
        user_id = uuid.uuid4()
        group_id = uuid.uuid4()
        session_id = SessionId(uuid.uuid4())
        kernel_id = KernelId(uuid.uuid4())
        access_key = AccessKey("TESTKEY12345678")

        async with db_with_resource_tables.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
                integration_id=None,
            )
            db_sess.add(domain)

            scaling_group = ScalingGroupRow(
                name="default",
                is_active=True,
                is_public=True,
                driver="static",
                driver_opts={},
                scheduler="fifo",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_sess.add(scaling_group)

            user_resource_policy = UserResourcePolicyRow(
                name="default-user-policy",
                max_vfolder_count=100,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            db_sess.add(user_resource_policy)

            project_resource_policy = ProjectResourcePolicyRow(
                name="default-project-policy",
                max_vfolder_count=100,
                max_quota_scope_size=-1,
                max_network_count=10,
            )
            db_sess.add(project_resource_policy)

            keypair_resource_policy = KeyPairResourcePolicyRow(
                name="default-keypair-policy",
                default_for_unspecified=DefaultForUnspecified.UNLIMITED,
                total_resource_slots=ResourceSlot(),
                max_session_lifetime=0,
                max_concurrent_sessions=10,
                max_concurrent_sftp_sessions=5,
                max_containers_per_session=1,
                idle_timeout=3600,
            )
            db_sess.add(keypair_resource_policy)
            await db_sess.flush()

            user = UserRow(
                uuid=user_id,
                username="testuser",
                email="test@example.com",
                password=None,
                need_password_change=False,
                full_name="Test User",
                description="Test user",
                status=UserStatus.ACTIVE,
                status_info="",
                domain_name=domain_name,
                role=UserRole.USER,
                resource_policy=user_resource_policy.name,
                allowed_client_ip=None,
                totp_key=None,
                main_access_key=None,
            )
            db_sess.add(user)

            group = GroupRow(
                id=group_id,
                name="test-group",
                description="Test group",
                is_active=True,
                domain_name=domain_name,
                total_resource_slots=ResourceSlot(),
                allowed_vfolder_hosts={},
                resource_policy=project_resource_policy.name,
                type=ProjectType.GENERAL,
            )
            db_sess.add(group)
            await db_sess.flush()

            keypair = KeyPairRow(
                user_id="test@example.com",
                user=user_id,
                access_key=access_key,
                secret_key="test-secret-key",
                is_active=True,
                is_admin=False,
                resource_policy=keypair_resource_policy.name,
                rate_limit=1000,
            )
            db_sess.add(keypair)
            await db_sess.flush()

            now = datetime.now(tzutc())
            # Session with EMPTY occupying_slots (simulating post-Phase 3 state)
            session = SessionRow(
                id=session_id,
                creation_id="test-creation-id",
                name="test-session",
                session_type=SessionTypes.INTERACTIVE,
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                domain_name=domain_name,
                group_id=group_id,
                user_uuid=user_id,
                access_key=access_key,
                tag=None,
                status=SessionStatus.RUNNING,
                status_info=None,
                status_data=None,
                status_history={},
                result=SessionResult.UNDEFINED,
                created_at=now,
                terminated_at=None,
                starts_at=None,
                startup_command=None,
                callback_url=None,
                occupying_slots=ResourceSlot(),  # Empty! (post-Phase 3)
                requested_slots=ResourceSlot({"cpu": "2", "mem": "2147483648"}),
                vfolder_mounts=[],
                environ=None,
                bootstrap_script=None,
                use_host_network=False,
                scaling_group_name="default",
            )
            db_sess.add(session)
            await db_sess.flush()

            kernel = KernelRow(
                id=kernel_id,
                session_id=session_id,
                session_type=SessionTypes.INTERACTIVE,
                domain_name=domain_name,
                group_id=group_id,
                user_uuid=user_id,
                access_key=access_key,
                cluster_mode=ClusterMode.SINGLE_NODE.value,
                cluster_size=1,
                cluster_role="main",
                cluster_idx=0,
                local_rank=0,
                cluster_hostname="main",
                image="cr.backend.ai/stable/python:latest",
                architecture="x86_64",
                registry="cr.backend.ai",
                agent=None,
                agent_addr=None,
                container_id=None,
                repl_in_port=2000,
                repl_out_port=2001,
                stdin_port=2002,
                stdout_port=2003,
                use_host_network=False,
                status=KernelStatus.RUNNING,
                status_info=None,
                status_data=None,
                status_history={},
                status_changed=now,
                result=SessionResult.UNDEFINED,
                created_at=now,
                terminated_at=None,
                starts_at=None,
                occupied_slots=ResourceSlot(),
                requested_slots=ResourceSlot({"cpu": "2", "mem": "2147483648"}),
                occupied_shares={},
                environ=None,
                vfolder_mounts=[],
                attached_devices={},
                resource_opts=None,
                preopen_ports=None,
                bootstrap_script=None,
                startup_command=None,
            )
            db_sess.add(kernel)
            await db_sess.flush()

            # Seed resource_slot_types (required FK for resource_allocations)
            for slot_name, slot_type in [("cpu", "count"), ("mem", "bytes")]:
                db_sess.add(ResourceSlotTypeRow(slot_name=slot_name, slot_type=slot_type))
            await db_sess.flush()

            # Create normalized resource_allocations (the source of truth)
            db_sess.add(
                ResourceAllocationRow(
                    kernel_id=kernel_id,
                    slot_name="cpu",
                    requested=Decimal("2.000000"),
                    used=Decimal("1.500000"),
                )
            )
            db_sess.add(
                ResourceAllocationRow(
                    kernel_id=kernel_id,
                    slot_name="mem",
                    requested=Decimal("2147483648"),
                    used=None,  # NULL used -> falls back to requested
                )
            )
            await db_sess.commit()

        return SessionTestData(
            domain_name=domain_name,
            user_id=user_id,
            group_id=group_id,
            session_id=session_id,
            kernel_id=kernel_id,
            access_key=access_key,
        )

    async def test_batch_populate_computes_slots_from_resource_allocations(
        self,
        db_with_resource_tables: ExtendedAsyncSAEngine,
        session_with_allocations: SessionTestData,
    ) -> None:
        """Verify that batch_populate reads from resource_allocations
        instead of the deprecated JSONB column."""
        async with db_with_resource_tables.begin_readonly_session() as db_sess:
            stmt = (
                sa.select(SessionRow)
                .where(SessionRow.id == session_with_allocations.session_id)
                .options(selectinload(SessionRow.kernels))
            )
            session_row = await db_sess.scalar(stmt)
            assert session_row is not None

            # Before: JSONB column is empty (post-Phase 3)
            assert session_row.occupying_slots == ResourceSlot()

            # Act: batch_populate computes from resource_allocations
            await batch_populate_session_occupied_slots(db_sess, [session_row])

            # After: occupying_slots is populated from resource_allocations
            slots = session_row.occupying_slots
            assert slots is not None
            assert len(slots) == 2
            # cpu: used=1.5 takes precedence over requested=2.0
            assert slots["cpu"] == Decimal("1.500000")
            # mem: used=NULL -> requested=2147483648
            assert slots["mem"] == Decimal("2147483648")

    async def test_batch_populate_empty_sessions(
        self,
        db_with_resource_tables: ExtendedAsyncSAEngine,
    ) -> None:
        """Verify that batch_populate handles empty list gracefully."""
        async with db_with_resource_tables.begin_readonly_session() as db_sess:
            await batch_populate_session_occupied_slots(db_sess, [])

    async def test_search_returns_computed_occupied_slots(
        self,
        db_with_resource_tables: ExtendedAsyncSAEngine,
        session_with_allocations: SessionTestData,
    ) -> None:
        """Verify the search() repository method returns computed occupied_slots
        from resource_allocations, not the empty JSONB column."""
        repository = SessionRepository(db_with_resource_tables)
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        result = await repository.search(querier=querier)

        assert result.total_count == 1
        session_data = result.items[0]
        slots = session_data.occupying_slots
        assert slots is not None
        assert slots["cpu"] == Decimal("1.500000")
        assert slots["mem"] == Decimal("2147483648")
