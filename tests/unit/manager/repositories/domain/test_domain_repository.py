"""
Tests for DomainRepository functionality.
Tests the repository layer with real database operations.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.exception import DomainNotFound, InvalidAPIParameters
from ai.backend.common.types import (
    DefaultForUnspecified,
    ResourceSlot,
    VFolderHostPermission,
    VFolderHostPermissionMap,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.domain.types import DomainData, UserInfo
from ai.backend.manager.errors.resource import (
    DomainDeletionFailed,
    DomainHasActiveKernels,
    DomainHasGroups,
    DomainHasUsers,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow, domains, row_to_data
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow, ProjectType, groups
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow, KernelStatus
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.domain.creators import DomainCreatorSpec
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.domain.updaters import DomainUpdaterSpec
from ai.backend.manager.types import TriState
from ai.backend.testutils.db import with_tables


class TestDomainRepository:
    """Test cases for DomainRepository"""

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
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ImageRow,
                VFolderRow,
                EndpointRow,
                DeploymentPolicyRow,
                DeploymentAutoScalingPolicyRow,
                DeploymentRevisionRow,
                SessionRow,
                AgentRow,
                KernelRow,
                RoutingRow,
                ResourcePresetRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def db_with_default_resource_policies(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database with default resource policies seeded for domain creation."""
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                KeyPairResourcePolicyRow(
                    name="default",
                    default_for_unspecified=DefaultForUnspecified.LIMITED,
                    total_resource_slots=ResourceSlot({}),
                    max_session_lifetime=0,
                    max_concurrent_sessions=30,
                    max_pending_session_count=10,
                    max_pending_session_resource_slots=None,
                    max_concurrent_sftp_sessions=1,
                    max_containers_per_session=1,
                    idle_timeout=1800,
                    allowed_vfolder_hosts={},
                )
            )
            db_sess.add(
                UserResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=-1,
                    max_network_count=5,
                )
            )
            await db_sess.commit()
        yield db_with_cleanup

    @pytest.fixture
    def domain_repository(
        self, db_with_default_resource_policies: ExtendedAsyncSAEngine
    ) -> DomainRepository:
        """Create DomainRepository instance with real database"""
        repo = DomainRepository(db=db_with_default_resource_policies)

        # Create mock for _role_manager
        mock_role_manager = MagicMock()
        mock_role_manager.create_system_role = AsyncMock(return_value=None)
        repo._role_manager = mock_role_manager

        return repo

    @pytest.fixture
    def sample_domain_creator(self) -> DomainCreatorSpec:
        """Create domain creator for testing"""
        return DomainCreatorSpec(
            name="test-domain",
            description="Test domain description",
            is_active=True,
            total_resource_slots=ResourceSlot.from_user_input({"cpu": "10", "mem": "20g"}, None),
            allowed_vfolder_hosts={"local": ["modify-vfolder", "upload-file", "download-file"]},
            allowed_docker_registries=["registry.example.com"],
            integration_id="test-integration",
            dotfiles=b"test dotfiles",
        )

    @pytest.fixture
    async def sample_domain(
        self, db_with_default_resource_policies: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[DomainData, None]:
        """Create a sample domain for testing."""
        async with db_with_default_resource_policies.begin() as conn:
            domain_data = {
                "name": "sample-domain",
                "description": "Sample domain for testing",
                "is_active": True,
                "total_resource_slots": ResourceSlot.from_user_input(
                    {"cpu": "8", "mem": "16g"}, None
                ),
                "allowed_vfolder_hosts": VFolderHostPermissionMap({
                    "local": {
                        VFolderHostPermission(p)
                        for p in ["modify-vfolder", "upload-file", "download-file"]
                    }
                }),
                "allowed_docker_registries": ["registry.example.com"],
                "dotfiles": b"test dotfiles",
                "integration_id": "test-integration",
            }

            result = await conn.execute(sa.insert(domains).values(domain_data).returning(domains))
            domain_row = result.first()

            # Create model-store group for the domain
            group_data = {
                "id": uuid.uuid4(),
                "name": "model-store",
                "description": "Model store group for sample-domain",
                "domain_name": "sample-domain",
                "is_active": True,
                "created_at": datetime.now(tz=UTC),
                "modified_at": datetime.now(tz=UTC),
                "type": ProjectType.GENERAL,
                "total_resource_slots": {},
                "allowed_vfolder_hosts": {},
                "integration_id": None,
                "resource_policy": "default",
            }

            await conn.execute(sa.insert(groups).values(group_data))
            await conn.commit()

            assert domain_row is not None
            yield row_to_data(domain_row)

    @pytest.fixture
    def user_info(self) -> UserInfo:
        """Create user info for testing"""
        return UserInfo(id=uuid.uuid4(), role=UserRole.SUPERADMIN, domain_name="default")

    @pytest.fixture
    async def inactive_domain(
        self, db_with_default_resource_policies: ExtendedAsyncSAEngine
    ) -> str:
        """Create an inactive domain for purge testing."""
        domain_name = f"inactive-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_default_resource_policies.begin_session() as session:
            domain = DomainRow(
                name=domain_name,
                description="Test domain for purging",
                is_active=False,
                total_resource_slots=ResourceSlot.from_user_input({"cpu": "8", "mem": "16g"}, None),
                allowed_vfolder_hosts={},
                allowed_docker_registries=["registry.example.com"],
                dotfiles=b"test dotfiles",
                integration_id="test-integration",
            )
            session.add(domain)
            await session.commit()
        return domain_name

    @pytest.fixture
    async def domain_with_user(
        self, db_with_default_resource_policies: ExtendedAsyncSAEngine
    ) -> str:
        """Create an inactive domain with a user for purge testing."""
        domain_name = f"domain-with-user-{uuid.uuid4().hex[:8]}"
        async with db_with_default_resource_policies.begin_session() as session:
            domain = DomainRow(
                name=domain_name,
                description="Test domain with users",
                is_active=False,
                total_resource_slots=ResourceSlot.from_user_input({"cpu": "8", "mem": "16g"}, None),
                allowed_vfolder_hosts={},
                allowed_docker_registries=["registry.example.com"],
                dotfiles=b"test dotfiles",
                integration_id="test-integration",
            )
            session.add(domain)

            password_info = PasswordInfo(
                password="test_password",
                algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                rounds=100_000,
                salt_size=32,
            )
            user = UserRow(
                uuid=uuid.uuid4(),
                username=f"testuser-{uuid.uuid4().hex[:8]}",
                email=f"test-{uuid.uuid4().hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                full_name="Test User",
                description="Test user",
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=domain_name,
                role=UserRole.USER,
                resource_policy="default",
            )
            session.add(user)
            await session.commit()
        return domain_name

    @pytest.fixture
    async def domain_with_group(
        self, db_with_default_resource_policies: ExtendedAsyncSAEngine
    ) -> str:
        """Create an inactive domain with a group for purge testing."""
        domain_name = f"domain-with-group-{uuid.uuid4().hex[:8]}"
        async with db_with_default_resource_policies.begin_session() as session:
            domain = DomainRow(
                name=domain_name,
                description="Test domain with groups",
                is_active=False,
                total_resource_slots=ResourceSlot.from_user_input({"cpu": "8", "mem": "16g"}, None),
                allowed_vfolder_hosts={},
                allowed_docker_registries=["registry.example.com"],
                dotfiles=b"test dotfiles",
                integration_id="test-integration",
            )
            session.add(domain)

            group = GroupRow(
                id=uuid.uuid4(),
                name=f"test-group-{uuid.uuid4().hex[:8]}",
                description="Test group",
                is_active=True,
                domain_name=domain_name,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                integration_id=None,
                resource_policy="default",
                type=ProjectType.GENERAL,
            )
            session.add(group)
            await session.commit()
        return domain_name

    @pytest.fixture
    async def domain_with_active_kernel(
        self, db_with_default_resource_policies: ExtendedAsyncSAEngine
    ) -> str:
        """Create an inactive domain with an active kernel for purge testing."""
        domain_name = f"domain-with-kernel-{uuid.uuid4().hex[:8]}"
        user_uuid = uuid.uuid4()
        group_id = uuid.uuid4()
        session_id = uuid.uuid4()

        async with db_with_default_resource_policies.begin_session() as session:
            domain = DomainRow(
                name=domain_name,
                description="Test domain with active kernels",
                is_active=False,
                total_resource_slots=ResourceSlot.from_user_input({"cpu": "8", "mem": "16g"}, None),
                allowed_vfolder_hosts={},
                allowed_docker_registries=["registry.example.com"],
                dotfiles=b"test dotfiles",
                integration_id="test-integration",
            )
            session.add(domain)

            group = GroupRow(
                id=group_id,
                name=f"test-group-{uuid.uuid4().hex[:8]}",
                description="Test group",
                is_active=True,
                domain_name=domain_name,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                integration_id=None,
                resource_policy="default",
                type=ProjectType.GENERAL,
            )
            session.add(group)

            password_info = PasswordInfo(
                password="test_password",
                algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                rounds=100_000,
                salt_size=32,
            )
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{uuid.uuid4().hex[:8]}",
                email=f"test-{uuid.uuid4().hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                full_name="Test User",
                description="Test user",
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=domain_name,
                role=UserRole.USER,
                resource_policy="default",
            )
            session.add(user)

            sess = SessionRow(
                id=session_id,
                creation_id=str(uuid.uuid4()).replace("-", ""),
                cluster_size=1,
                domain_name=domain_name,
                group_id=group_id,
                user_uuid=user_uuid,
                vfolder_mounts={},
            )
            session.add(sess)

            kernel = KernelRow(
                session_id=session_id,
                domain_name=domain_name,
                group_id=group_id,
                user_uuid=user_uuid,
                cluster_role="main",
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
    async def test_create_domain_success(
        self,
        db_with_default_resource_policies: ExtendedAsyncSAEngine,
        domain_repository: DomainRepository,
        sample_domain_creator: DomainCreatorSpec,
    ) -> None:
        """Test successful domain creation"""
        # Ensure domain doesn't exist
        async with db_with_default_resource_policies.begin() as conn:
            result = await conn.execute(
                sa.select(domains).where(domains.c.name == sample_domain_creator.name)
            )
            assert result.first() is None

        # Create domain
        created_domain = await domain_repository.create_domain(Creator(spec=sample_domain_creator))

        assert created_domain.name == sample_domain_creator.name
        assert created_domain.description == sample_domain_creator.description
        assert created_domain.is_active == sample_domain_creator.is_active
        assert created_domain.total_resource_slots == sample_domain_creator.total_resource_slots
        assert created_domain.integration_id == sample_domain_creator.integration_id

        # Verify domain exists in database
        async with db_with_default_resource_policies.begin() as conn:
            result = await conn.execute(
                sa.select(domains).where(domains.c.name == sample_domain_creator.name)
            )
            domain_row = result.first()
            assert domain_row is not None
            assert domain_row.name == sample_domain_creator.name

            # Verify model-store group was created
            result = await conn.execute(
                sa.select(groups).where(groups.c.domain_name == sample_domain_creator.name)
            )
            group_row = result.first()
            assert group_row is not None
            assert group_row.name == "model-store"

    @pytest.mark.asyncio
    async def test_create_domain_duplicate_name(
        self,
        domain_repository: DomainRepository,
        sample_domain_creator: DomainCreatorSpec,
    ) -> None:
        """Test domain creation with duplicate name"""
        # Create domain first
        await domain_repository.create_domain(Creator(spec=sample_domain_creator))

        # Try to create another domain with same name
        duplicate_creator = Creator(
            spec=DomainCreatorSpec(
                name=sample_domain_creator.name,  # Same name
                description="Duplicate domain",
                is_active=True,
            )
        )

        with pytest.raises(InvalidAPIParameters):
            await domain_repository.create_domain(duplicate_creator)

    @pytest.mark.asyncio
    async def test_modify_domain_success(
        self,
        db_with_default_resource_policies: ExtendedAsyncSAEngine,
        domain_repository: DomainRepository,
    ) -> None:
        """Test successful domain modification"""
        domain_name = "modify-test-simple"
        domain_creator = Creator(
            spec=DomainCreatorSpec(
                name=domain_name,
                description="Original description",
                is_active=True,
                total_resource_slots=ResourceSlot.from_user_input(
                    {"cpu": "10", "mem": "20g"}, None
                ),
                allowed_vfolder_hosts={"local": ["modify-vfolder"]},
                allowed_docker_registries=["registry.example.com"],
                integration_id="test-integration",
                dotfiles=b"test dotfiles",
            )
        )

        # Create domain
        await domain_repository.create_domain(domain_creator)

        # Create updater
        updater_spec = DomainUpdaterSpec(
            description=TriState.update("Updated description"),
            total_resource_slots=TriState.update(
                ResourceSlot.from_user_input({"cpu": "20", "mem": "40g"}, None)
            ),
        )
        updater = Updater(spec=updater_spec, pk_value=domain_name)

        # Modify domain
        modified_domain = await domain_repository.modify_domain(updater)

        assert modified_domain is not None
        assert modified_domain.name == domain_name
        assert modified_domain.description == "Updated description"

        # Verify changes in database
        async with db_with_default_resource_policies.begin() as conn:
            result = await conn.execute(sa.select(domains).where(domains.c.name == domain_name))
            domain_row = result.first()
            assert domain_row is not None
            assert domain_row.description == "Updated description"

    @pytest.mark.asyncio
    async def test_modify_domain_not_found(
        self,
        domain_repository: DomainRepository,
    ) -> None:
        """Test domain modification when domain not found"""
        updater_spec = DomainUpdaterSpec(
            description=TriState.update("Updated description"),
        )
        updater = Updater(spec=updater_spec, pk_value="nonexistent-domain")

        with pytest.raises(DomainNotFound):
            await domain_repository.modify_domain(updater)

    @pytest.mark.asyncio
    async def test_soft_delete_domain_success(
        self,
        db_with_default_resource_policies: ExtendedAsyncSAEngine,
        domain_repository: DomainRepository,
    ) -> None:
        """Test successful domain soft deletion"""
        domain_name = "delete-test-simple"
        domain_creator = Creator(
            spec=DomainCreatorSpec(
                name=domain_name,
                description="Test domain for deletion",
                is_active=True,
                total_resource_slots=ResourceSlot.from_user_input(
                    {"cpu": "10", "mem": "20g"}, None
                ),
                allowed_vfolder_hosts={"local": ["modify-vfolder"]},
                allowed_docker_registries=["registry.example.com"],
                integration_id="test-integration",
                dotfiles=b"test dotfiles",
            )
        )

        # Create domain
        await domain_repository.create_domain(domain_creator)

        # Soft delete domain (now returns None)
        await domain_repository.soft_delete_domain(domain_name)

        # Verify domain is marked as inactive
        async with db_with_default_resource_policies.begin() as conn:
            result = await conn.execute(sa.select(domains).where(domains.c.name == domain_name))
            domain_row = result.first()
            assert domain_row is not None
            assert domain_row.is_active is False

    @pytest.mark.asyncio
    async def test_soft_delete_domain_not_found(
        self,
        domain_repository: DomainRepository,
    ) -> None:
        """Test domain soft deletion when domain not found"""
        with pytest.raises(DomainNotFound):
            await domain_repository.soft_delete_domain("nonexistent-domain")

    @pytest.mark.asyncio
    async def test_purge_domain_success(
        self,
        db_with_default_resource_policies: ExtendedAsyncSAEngine,
        domain_repository: DomainRepository,
        inactive_domain: str,
    ) -> None:
        """Test successful domain purging"""
        # Purge domain (should succeed since no users/groups/kernels)
        await domain_repository.purge_domain(inactive_domain)

        # Verify domain is completely removed
        async with db_with_default_resource_policies.begin() as conn:
            result = await conn.execute(sa.select(domains).where(domains.c.name == inactive_domain))
            domain_row = result.first()
            assert domain_row is None

    @pytest.mark.asyncio
    async def test_purge_domain_with_users(
        self,
        domain_repository: DomainRepository,
        domain_with_user: str,
    ) -> None:
        """Test domain purging when domain has users"""
        # Try to purge domain (should fail due to users)
        with pytest.raises(DomainHasUsers):
            await domain_repository.purge_domain(domain_with_user)

    @pytest.mark.asyncio
    async def test_purge_domain_not_found(
        self,
        domain_repository: DomainRepository,
    ) -> None:
        """Test domain purging when domain not found"""
        with pytest.raises(DomainDeletionFailed):
            await domain_repository.purge_domain("nonexistent-domain")

    @pytest.mark.asyncio
    async def test_create_domain_with_all_fields(
        self,
        db_with_default_resource_policies: ExtendedAsyncSAEngine,
        domain_repository: DomainRepository,
    ) -> None:
        """Test creating domain with all possible fields"""
        comprehensive_creator = Creator(
            spec=DomainCreatorSpec(
                name="comprehensive-domain",
                description="Comprehensive domain with all features",
                is_active=True,
                total_resource_slots=ResourceSlot.from_user_input(
                    {"cpu": "100", "mem": "500g", "cuda.device": "8"}, None
                ),
                allowed_vfolder_hosts={
                    "local": ["modify-vfolder", "upload-file", "download-file"],
                    "shared": ["download-file"],
                    "scratch": ["modify-vfolder", "upload-file", "download-file"],
                },
                allowed_docker_registries=[
                    "docker.io",
                    "registry.example.com",
                    "private.registry",
                ],
                integration_id="comprehensive-integration",
                dotfiles=b"comprehensive dotfiles configuration",
            )
        )

        created_domain = await domain_repository.create_domain(comprehensive_creator)

        assert created_domain.name == "comprehensive-domain"
        assert created_domain.description == "Comprehensive domain with all features"
        assert created_domain.is_active is True
        assert created_domain.total_resource_slots == ResourceSlot.from_user_input(
            {"cpu": "100", "mem": "500g", "cuda.device": "8"}, None
        )
        assert created_domain.integration_id == "comprehensive-integration"
        assert len(created_domain.allowed_docker_registries) == 3
        assert created_domain.dotfiles == b"comprehensive dotfiles configuration"

        # Verify in database
        async with db_with_default_resource_policies.begin() as conn:
            result = await conn.execute(
                sa.select(domains).where(domains.c.name == "comprehensive-domain")
            )
            domain_row = result.first()
            assert domain_row is not None
            assert domain_row.name == "comprehensive-domain"
            assert domain_row.is_active is True

    @pytest.mark.asyncio
    async def test_purge_domain_with_groups(
        self,
        domain_repository: DomainRepository,
        domain_with_group: str,
    ) -> None:
        """Test domain purging when domain has groups"""
        # Try to purge domain (should fail due to groups)
        with pytest.raises(DomainHasGroups):
            await domain_repository.purge_domain(domain_with_group)

    @pytest.mark.asyncio
    async def test_purge_domain_with_active_kernels(
        self,
        domain_repository: DomainRepository,
        domain_with_active_kernel: str,
    ) -> None:
        """Test domain purging when domain has active kernels"""
        # Try to purge domain (should fail due to active kernels)
        with pytest.raises(DomainHasActiveKernels):
            await domain_repository.purge_domain(domain_with_active_kernel)
