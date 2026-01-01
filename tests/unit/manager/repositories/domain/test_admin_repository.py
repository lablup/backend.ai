from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

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
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.group import ProjectType
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.kernel import KernelStatus
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.user import UserRole, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.domain.admin_repository import AdminDomainRepository
from ai.backend.testutils.db import with_tables

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
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                DomainRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                ProjectResourcePolicyRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ScalingGroupRow,
                AgentRow,
                SessionRow,
                KernelRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def admin_domain_repository(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AdminDomainRepository:
        """Create AdminDomainRepository instance with real database"""
        return AdminDomainRepository(db=db_with_cleanup)

    @pytest.fixture
    async def sample_domain(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Create a test domain and return its name."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            domain = DomainRow(
                name=domain_name,
                description=f"Test domain {domain_name}",
                is_active=True,
                total_resource_slots=ResourceSlot.from_user_input({"cpu": "8", "mem": "16g"}, None),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
                dotfiles=b"",
                integration_id=None,
            )
            session.add(domain)
            await session.commit()
        return domain_name

    @pytest.fixture
    async def domain_with_user(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Create a domain with a user and return domain name."""
        domain_name = f"domain-with-user-{uuid.uuid4().hex[:8]}"
        resource_policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as session:
            # Create domain
            domain = DomainRow(
                name=domain_name,
                description=f"Test domain {domain_name}",
                is_active=True,
                total_resource_slots=ResourceSlot.from_user_input({"cpu": "8", "mem": "16g"}, None),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
                dotfiles=b"",
                integration_id=None,
            )
            session.add(domain)

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
                uuid=uuid.uuid4(),
                username="testuser",
                email="testuser@example.com",
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
            await session.commit()

        return domain_name

    @pytest.fixture
    async def domain_with_group(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Create a domain with a group and return domain name."""
        domain_name = f"domain-with-group-{uuid.uuid4().hex[:8]}"
        resource_policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as session:
            # Create domain
            domain = DomainRow(
                name=domain_name,
                description=f"Test domain {domain_name}",
                is_active=True,
                total_resource_slots=ResourceSlot.from_user_input({"cpu": "8", "mem": "16g"}, None),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
                dotfiles=b"",
                integration_id=None,
            )
            session.add(domain)

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
                id=uuid.uuid4(),
                name="test-group",
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
            await session.commit()

        return domain_name

    @pytest.fixture
    async def domain_with_kernel(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Create a domain with an active kernel and return domain name."""
        domain_name = f"domain-with-kernel-{uuid.uuid4().hex[:8]}"
        user_resource_policy_name = f"user-policy-{uuid.uuid4().hex[:8]}"
        project_resource_policy_name = f"project-policy-{uuid.uuid4().hex[:8]}"
        session_id = uuid.uuid4()
        user_uuid = uuid.uuid4()
        group_id = uuid.uuid4()

        async with db_with_cleanup.begin_session() as session:
            # Create domain
            domain = DomainRow(
                name=domain_name,
                description=f"Test domain {domain_name}",
                is_active=True,
                total_resource_slots=ResourceSlot.from_user_input({"cpu": "8", "mem": "16g"}, None),
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
                dotfiles=b"",
                integration_id=None,
            )
            session.add(domain)

            # Create resource policies
            user_resource_policy = UserResourcePolicyRow(
                name=user_resource_policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=10,
                max_customized_image_count=10,
            )
            session.add(user_resource_policy)

            project_resource_policy = ProjectResourcePolicyRow(
                name=project_resource_policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(project_resource_policy)

            # Create group
            group = GroupRow(
                id=group_id,
                name=f"test-group-{uuid.uuid4().hex[:8]}",
                domain_name=domain_name,
                total_resource_slots={},
                resource_policy=project_resource_policy_name,
            )
            session.add(group)

            # Create user
            user = UserRow(
                uuid=user_uuid,
                email=f"test-{uuid.uuid4().hex[:8]}@example.com",
                username=f"test-user-{uuid.uuid4().hex[:8]}",
                password=create_test_password_info("test_password"),
                domain_name=domain_name,
                resource_policy=user_resource_policy_name,
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

            # Create kernel (RUNNING status)
            kernel = KernelRow(
                session_id=str(session_id).replace("-", ""),
                domain_name=domain_name,
                group_id=str(group_id).replace("-", ""),
                user_uuid=str(user_uuid).replace("-", ""),
                cluster_role=DEFAULT_ROLE,
                status=KernelStatus.RUNNING,
                occupied_slots={},
                repl_in_port=0,
                repl_out_port=0,
                stdin_port=0,
                stdout_port=0,
                vfolder_mounts={},
            )
            session.add(kernel)
            await session.commit()

        return domain_name

    @pytest.mark.asyncio
    async def test_purge_domain_force_success_empty_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        admin_domain_repository: AdminDomainRepository,
        sample_domain: str,
    ) -> None:
        """Test successful purge of an empty domain (no users, groups, active kernels)"""
        # Purge the domain
        await admin_domain_repository.purge_domain_force(sample_domain)

        # Verify domain is completely removed
        async with db_with_cleanup.begin_session() as session:
            result = await session.scalar(
                sa.select(DomainRow).where(DomainRow.name == sample_domain)
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
        admin_domain_repository: AdminDomainRepository,
        domain_with_user: str,
    ) -> None:
        """Test purge raises DomainHasUsers when domain has users"""
        with pytest.raises(DomainHasUsers):
            await admin_domain_repository.purge_domain_force(domain_with_user)

    @pytest.mark.asyncio
    async def test_purge_domain_force_fails_with_active_groups(
        self,
        admin_domain_repository: AdminDomainRepository,
        domain_with_group: str,
    ) -> None:
        """Test purge raises DomainHasGroups when domain has groups"""
        with pytest.raises(DomainHasGroups):
            await admin_domain_repository.purge_domain_force(domain_with_group)

    @pytest.mark.asyncio
    async def test_purge_domain_force_fails_with_active_kernels(
        self,
        admin_domain_repository: AdminDomainRepository,
        domain_with_kernel: str,
    ) -> None:
        """Test purge raises DomainHasActiveKernels when domain has active kernels"""
        with pytest.raises(DomainHasActiveKernels):
            await admin_domain_repository.purge_domain_force(domain_with_kernel)
