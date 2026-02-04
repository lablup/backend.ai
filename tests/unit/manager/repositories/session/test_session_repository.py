"""
Tests for SessionRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import datetime

import pytest
from dateutil.tz import tzutc

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
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
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
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> SessionRepository:
        return SessionRepository(db_with_cleanup)

    @pytest.fixture
    def default_querier(self) -> BatchQuerier:
        return BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

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

    @pytest.mark.asyncio
    async def test_search_kernels(
        self,
        repository: SessionRepository,
        default_querier: BatchQuerier,
        session_with_kernel: SessionTestData,
    ) -> None:
        """Test search_kernels returns kernel info when kernels exist"""
        result = await repository.search_kernels(default_querier)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False

        kernel_info = result.items[0]
        assert kernel_info.id == session_with_kernel.kernel_id
        assert kernel_info.session.session_id == str(session_with_kernel.session_id)

    @pytest.mark.asyncio
    async def test_search_kernels_empty_result(
        self,
        repository: SessionRepository,
        default_querier: BatchQuerier,
    ) -> None:
        """Test search_kernels returns empty result when no kernels exist"""
        result = await repository.search_kernels(default_querier)

        assert result.total_count == 0
        assert len(result.items) == 0
        assert result.has_next_page is False
        assert result.has_previous_page is False

    # =========================================================================
    # Tests - SearchSessions
    # =========================================================================

    @pytest.mark.asyncio
    async def test_search_sessions(
        self,
        repository: SessionRepository,
        default_querier: BatchQuerier,
        session_with_kernel: SessionTestData,
    ) -> None:
        """Test search returns session data when sessions exist"""
        result = await repository.search(querier=default_querier)

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

    @pytest.mark.asyncio
    async def test_search_sessions_empty_result(
        self,
        repository: SessionRepository,
        default_querier: BatchQuerier,
    ) -> None:
        """Test search returns empty result when no sessions exist"""
        result = await repository.search(querier=default_querier)

        assert result.total_count == 0
        assert len(result.items) == 0
        assert result.has_next_page is False
        assert result.has_previous_page is False
