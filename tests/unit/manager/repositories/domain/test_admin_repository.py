from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.errors.resource import (
    DomainDeletionFailed,
    DomainHasActiveKernels,
    DomainHasGroups,
    DomainHasUsers,
)
from ai.backend.manager.models import (
    DomainRow,
    GroupRow,
    KernelRow,
    ProjectResourcePolicyRow,
    SessionRow,
    UserResourcePolicyRow,
    UserRow,
)
from ai.backend.manager.models.group import ProjectType
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.kernel import KernelStatus
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.domain.admin_repository import AdminDomainRepository

DEFAULT_ROLE = "main"


def create_test_password_info(password: str = "test_password") -> PasswordInfo:
    """Create a PasswordInfo object for testing with default PBKDF2 algorithm."""
    return PasswordInfo(
        password=password,
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


class TestAdminDomainRepository:
    """Test cases for AdminDomainRepository using real database"""

    @pytest.fixture
    def admin_domain_repository(
        self, database_engine: ExtendedAsyncSAEngine
    ) -> AdminDomainRepository:
        """Create AdminDomainRepository instance with real database"""
        return AdminDomainRepository(db=database_engine)

    @asynccontextmanager
    async def create_test_domain(
        self,
        database_engine: ExtendedAsyncSAEngine,
        name: str = "test-domain",
    ) -> AsyncGenerator[str, None]:
        """Create a test domain and ensure cleanup"""
        async with database_engine.begin_session() as session:
            domain = DomainRow(
                name=name,
                description=f"Test domain {name}",
                is_active=True,
                total_resource_slots=ResourceSlot.from_user_input({"cpu": "8", "mem": "16g"}, None),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
                dotfiles=b"",
                integration_id=None,
            )
            session.add(domain)
            await session.flush()

        try:
            yield name
        finally:
            async with database_engine.begin_session() as session:
                await session.execute(sa.delete(KernelRow).where(KernelRow.domain_name == name))
                await session.execute(sa.delete(SessionRow).where(SessionRow.domain_name == name))
                await session.execute(sa.delete(UserRow).where(UserRow.domain_name == name))
                await session.execute(sa.delete(GroupRow).where(GroupRow.domain_name == name))
                await session.execute(sa.delete(DomainRow).where(DomainRow.name == name))

    async def create_test_user(
        self,
        database_engine: ExtendedAsyncSAEngine,
        domain_name: str,
        email: str = "test@example.com",
    ) -> str:
        """Create a test user for the domain and return user UUID"""
        user_uuid = uuid.uuid4()
        resource_policy_name = f"test-policy-{uuid.uuid4()}"

        async with database_engine.begin_session() as session:
            # Create user resource policy
            user_resource_policy = UserResourcePolicyRow(
                name=resource_policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            session.add(user_resource_policy)

            # Create user
            user = UserRow(
                uuid=user_uuid,
                username=email.split("@")[0],
                email=email,
                password=create_test_password_info("test_password"),
                need_password_change=False,
                full_name="Test User",
                description="Test user",
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=domain_name,
                role=UserRole.USER,
                resource_policy=resource_policy_name,
            )
            session.add(user)
            await session.flush()

        return str(user_uuid)

    async def create_test_group(
        self,
        database_engine: ExtendedAsyncSAEngine,
        domain_name: str,
        group_name: str = "test-group",
    ) -> str:
        """Create a test group for the domain and return group ID"""
        group_id = uuid.uuid4()
        resource_policy_name = f"test-policy-{uuid.uuid4()}"

        async with database_engine.begin_session() as session:
            # Create project resource policy
            project_resource_policy = ProjectResourcePolicyRow(
                name=resource_policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(project_resource_policy)

            # Create group
            group = GroupRow(
                id=group_id,
                name=group_name,
                description="Test group",
                is_active=True,
                domain_name=domain_name,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                integration_id=None,
                resource_policy=resource_policy_name,
                type=ProjectType.GENERAL,
            )
            session.add(group)
            await session.flush()

        return str(group_id)

    async def create_test_kernel(
        self,
        database_engine: ExtendedAsyncSAEngine,
        domain_name: str,
        status: KernelStatus = KernelStatus.RUNNING,
    ) -> str:
        """Create a test kernel for the domain and return session ID"""
        session_id = uuid.uuid4()
        user_uuid = uuid.uuid4()
        group_id = uuid.uuid4()
        resource_policy_name = f"test-policy-{uuid.uuid4()}"

        async with database_engine.begin_session() as session:
            # Create resource policies
            user_resource_policy = UserResourcePolicyRow(
                name=resource_policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            session.add(user_resource_policy)

            project_resource_policy = ProjectResourcePolicyRow(
                name=resource_policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(project_resource_policy)

            # Create group
            group = GroupRow(
                id=group_id,
                name=f"test-group-{uuid.uuid4()}",
                domain_name=domain_name,
                total_resource_slots={},
                resource_policy=resource_policy_name,
            )
            session.add(group)

            # Create user
            user = UserRow(
                uuid=user_uuid,
                email=f"test-{uuid.uuid4()}@example.com",
                username=f"test-user-{uuid.uuid4()}",
                password=create_test_password_info("test_password"),
                domain_name=domain_name,
                resource_policy=resource_policy_name,
            )
            session.add(user)

            # Create session
            sess = SessionRow(
                id=str(session_id).replace("-", ""),
                creation_id=str(uuid.uuid4()).replace("-", ""),
                cluster_size=1,
                domain_name=domain_name,
                group_id=str(group_id).replace("-", ""),
                user_uuid=str(user_uuid).replace("-", ""),
                vfolder_mounts={},
            )
            session.add(sess)

            # Create kernel
            kernel = KernelRow(
                session_id=str(session_id).replace("-", ""),
                domain_name=domain_name,
                group_id=str(group_id).replace("-", ""),
                user_uuid=str(user_uuid).replace("-", ""),
                cluster_role=DEFAULT_ROLE,
                status=status,
                occupied_slots={},
                repl_in_port=0,
                repl_out_port=0,
                stdin_port=0,
                stdout_port=0,
                vfolder_mounts={},
            )
            session.add(kernel)
            await session.flush()

        return str(session_id).replace("-", "")

    @pytest.mark.asyncio
    async def test_purge_domain_force_success_empty_domain(
        self,
        database_engine: ExtendedAsyncSAEngine,
        admin_domain_repository: AdminDomainRepository,
    ) -> None:
        """Test successful purge of an empty domain (no users, groups, active kernels)"""
        async with self.create_test_domain(database_engine, "empty-domain") as domain_name:
            # Purge the domain
            await admin_domain_repository.purge_domain_force(domain_name)

            # Verify domain is completely removed
            async with database_engine.begin_session() as session:
                result = await session.scalar(
                    sa.select(DomainRow).where(DomainRow.name == domain_name)
                )
                assert result is None

    @pytest.mark.asyncio
    async def test_purge_domain_force_nonexistent_domain(
        self,
        admin_domain_repository: AdminDomainRepository,
    ) -> None:
        """Test purge raises DomainDeletionFailed for nonexistent domain"""
        with pytest.raises(DomainDeletionFailed):
            await admin_domain_repository.purge_domain_force("nonexistent-domain")

    @pytest.mark.asyncio
    async def test_purge_domain_force_fails_with_active_users(
        self,
        database_engine: ExtendedAsyncSAEngine,
        admin_domain_repository: AdminDomainRepository,
    ) -> None:
        """Test purge raises DomainHasUsers when domain has users"""
        async with self.create_test_domain(database_engine, "domain-with-users") as domain_name:
            # Create a user in the domain
            await self.create_test_user(database_engine, domain_name, "testuser@example.com")

            # Attempt to purge should fail
            with pytest.raises(DomainHasUsers):
                await admin_domain_repository.purge_domain_force(domain_name)

    @pytest.mark.asyncio
    async def test_purge_domain_force_fails_with_active_groups(
        self,
        database_engine: ExtendedAsyncSAEngine,
        admin_domain_repository: AdminDomainRepository,
    ) -> None:
        """Test purge raises DomainHasGroups when domain has groups"""
        async with self.create_test_domain(database_engine, "domain-with-groups") as domain_name:
            # Create a group in the domain
            await self.create_test_group(database_engine, domain_name, "test-group")

            # Attempt to purge should fail
            with pytest.raises(DomainHasGroups):
                await admin_domain_repository.purge_domain_force(domain_name)

    @pytest.mark.asyncio
    async def test_purge_domain_force_fails_with_active_kernels(
        self,
        database_engine: ExtendedAsyncSAEngine,
        admin_domain_repository: AdminDomainRepository,
    ) -> None:
        """Test purge raises DomainHasActiveKernels when domain has active kernels"""
        async with self.create_test_domain(database_engine, "domain-with-kernels") as domain_name:
            # Create an active kernel in the domain
            await self.create_test_kernel(database_engine, domain_name, KernelStatus.RUNNING)

            # Attempt to purge should fail
            with pytest.raises(DomainHasActiveKernels):
                await admin_domain_repository.purge_domain_force(domain_name)
