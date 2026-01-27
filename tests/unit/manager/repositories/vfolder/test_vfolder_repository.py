"""
Tests for VfolderRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, create_autospec

import pytest

from ai.backend.common.types import BinarySize, VFolderHostPermissionMap, VFolderUsageMode
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.data.vfolder.types import (
    VFolderCreateParams,
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
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
from ai.backend.manager.models.user import (
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderPermissionRow, VFolderRow
from ai.backend.manager.repositories.permission_controller.role_manager import RoleManager
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.testutils.db import with_tables


class TestVfolderRepository:
    """Test cases for VfolderRepository"""

    def _make_vfolder_create_params(
        self,
        *,
        folder_id: uuid.UUID,
        domain_name: str,
        group_id: uuid.UUID,
        user_id: uuid.UUID,
        permission: VFolderMountPermission = VFolderMountPermission.READ_ONLY,
        usage_mode: VFolderUsageMode = VFolderUsageMode.MODEL,
    ) -> VFolderCreateParams:
        """Create VFolderCreateParams for testing."""
        return VFolderCreateParams(
            id=folder_id,
            name=f"test-model-{folder_id.hex[:8]}",
            domain_name=domain_name,
            quota_scope_id=f"project:{group_id}",
            usage_mode=usage_mode,
            permission=permission,
            host="local",
            creator=f"test-{user_id.hex[:8]}@example.com",
            ownership_type=VFolderOwnershipType.GROUP,
            user=user_id,
            group=group_id,
            unmanaged_path=None,
            cloneable=False,
            status=VFolderOperationStatus.READY,
        )

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
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
                VFolderPermissionRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test domain and return domain name"""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain for vfolder",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.flush()

        yield domain_name

    @pytest.fixture
    async def test_user_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test user resource policy and return policy name"""
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            user_policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(user_policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_project_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test project resource policy and return policy name"""
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            project_policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_network_count=3,
            )
            db_sess.add(project_policy)
            await db_sess.flush()

        yield policy_name

    @pytest.fixture
    async def test_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test user and return user UUID"""
        user_uuid = uuid.uuid4()

        password_info = PasswordInfo(
            password="dummy",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=600_000,
            salt_size=32,
        )

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{user_uuid.hex[:8]}",
                email=f"test-{user_uuid.hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=test_domain_name,
                role=UserRole.USER,
                resource_policy=test_user_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.flush()

        yield user_uuid

    @pytest.fixture
    async def test_model_store_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_project_resource_policy_name: str,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Create test model-store group and return group UUID"""
        group_uuid = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            group = GroupRow(
                id=group_uuid,
                name=f"test-model-store-{group_uuid.hex[:8]}",
                domain_name=test_domain_name,
                description="Test model-store group",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                resource_policy=test_project_resource_policy_name,
                type=ProjectType.MODEL_STORE,
            )
            db_sess.add(group)
            await db_sess.flush()

        yield group_uuid

    @pytest.fixture
    def mock_role_manager(self) -> RoleManager:
        """Create a mock RoleManager with autospec"""
        mock = create_autospec(RoleManager, instance=True)
        mock.map_entity_to_scope = AsyncMock()
        mock.add_object_permission_to_user_role = AsyncMock()
        return mock

    @pytest.fixture
    async def vfolder_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        mock_role_manager: RoleManager,
    ) -> AsyncGenerator[VfolderRepository, None]:
        """Create VfolderRepository instance with database and mocked RoleManager"""
        repo = VfolderRepository(db=db_with_cleanup)
        repo._role_manager = mock_role_manager
        yield repo

    async def test_model_store_vfolder_permission_is_overridden_to_read_only(
        self,
        vfolder_repository: VfolderRepository,
        test_domain_name: str,
        test_user: uuid.UUID,
        test_model_store_group: uuid.UUID,
    ) -> None:
        """Test that model-store vfolder permission is always READ_ONLY.

        The service layer (VFolderService.create) overrides any requested permission
        to READ_ONLY for model-store group type. This test verifies that the repository
        correctly stores the READ_ONLY permission received from the service layer.
        """
        folder_id = uuid.uuid4()
        params = self._make_vfolder_create_params(
            folder_id=folder_id,
            domain_name=test_domain_name,
            group_id=test_model_store_group,
            user_id=test_user,
            permission=VFolderMountPermission.READ_ONLY,
            usage_mode=VFolderUsageMode.MODEL,
        )

        vfolder_data = await vfolder_repository.create_vfolder_with_permission(
            params, create_owner_permission=True
        )

        assert vfolder_data.id == folder_id
        assert vfolder_data.name == params.name
        assert vfolder_data.permission == VFolderMountPermission.READ_ONLY
        assert vfolder_data.usage_mode == VFolderUsageMode.MODEL
        assert vfolder_data.ownership_type == VFolderOwnershipType.GROUP
        assert vfolder_data.group == test_model_store_group


class TestVfolderRepositoryAllowedVfolderHosts:
    """Tests for VfolderRepository.get_allowed_vfolder_hosts() method"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test domain."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.flush()

        return domain_name

    @pytest.fixture
    async def test_user_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test user resource policy."""
        policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy)
            await db_sess.flush()

        return policy_name

    @pytest.fixture
    async def test_project_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test project resource policy."""
        policy_name = f"test-project-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_network_count=3,
            )
            db_sess.add(policy)
            await db_sess.flush()

        return policy_name

    @pytest.fixture
    async def test_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
    ) -> uuid.UUID:
        """Create test user."""
        user_uuid = uuid.uuid4()

        password_info = PasswordInfo(
            password="dummy",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=600_000,
            salt_size=32,
        )

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{user_uuid.hex[:8]}",
                email=f"test-{user_uuid.hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=test_domain_name,
                role=UserRole.USER,
                resource_policy=test_user_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.flush()

        return user_uuid

    @pytest.fixture
    async def test_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_project_resource_policy_name: str,
    ) -> uuid.UUID:
        """Create a group with allowed_vfolder_hosts set."""
        group_uuid = uuid.uuid4()

        async with db_with_cleanup.begin_session() as db_sess:
            group = GroupRow(
                id=group_uuid,
                name=f"test-group-{group_uuid.hex[:8]}",
                domain_name=test_domain_name,
                description="Test group with vfolder hosts",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={
                    "local": ["create-vfolder", "mount-in-session"],
                },
                resource_policy=test_project_resource_policy_name,
                type=ProjectType.GENERAL,
            )
            db_sess.add(group)
            await db_sess.flush()

        return group_uuid

    @pytest.fixture
    async def vfolder_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> VfolderRepository:
        """Create VfolderRepository instance."""
        return VfolderRepository(db=db_with_cleanup)

    async def test_get_allowed_vfolder_hosts_returns_vfolder_host_permission_map(
        self,
        vfolder_repository: VfolderRepository,
        test_user: uuid.UUID,
        test_group: uuid.UUID,
    ) -> None:
        """Test that get_allowed_vfolder_hosts returns VFolderHostPermissionMap type."""
        result = await vfolder_repository.get_allowed_vfolder_hosts(
            user_uuid=test_user,
            group_uuid=test_group,
        )

        assert isinstance(result, VFolderHostPermissionMap)


class TestVfolderRepositoryPurge:
    """Tests for VfolderRepository.purge_vfolder() method"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                VFolderRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_domain_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test domain."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots={},
                allowed_vfolder_hosts={},
                allowed_docker_registries=[],
            )
            db_sess.add(domain)
            await db_sess.flush()

        return domain_name

    @pytest.fixture
    async def test_user_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create test user resource policy."""
        policy_name = f"test-user-policy-{uuid.uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            policy = UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                max_session_count_per_model_session=5,
                max_customized_image_count=3,
            )
            db_sess.add(policy)
            await db_sess.flush()

        return policy_name

    @pytest.fixture
    async def test_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_user_resource_policy_name: str,
    ) -> uuid.UUID:
        """Create test user."""
        user_uuid = uuid.uuid4()

        password_info = PasswordInfo(
            password="dummy",
            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
            rounds=600_000,
            salt_size=32,
        )

        async with db_with_cleanup.begin_session() as db_sess:
            user = UserRow(
                uuid=user_uuid,
                username=f"testuser-{user_uuid.hex[:8]}",
                email=f"test-{user_uuid.hex[:8]}@example.com",
                password=password_info,
                need_password_change=False,
                status=UserStatus.ACTIVE,
                status_info="active",
                domain_name=test_domain_name,
                role=UserRole.USER,
                resource_policy=test_user_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.flush()

        return user_uuid

    @pytest.fixture
    async def vfolder_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> VfolderRepository:
        """Create VfolderRepository instance."""
        return VfolderRepository(db=db_with_cleanup)

    async def _create_vfolder_in_db(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        vfolder_id: uuid.UUID,
        domain_name: str,
        user_id: uuid.UUID,
        status: VFolderOperationStatus,
    ) -> None:
        """Helper to create a vfolder directly in DB."""
        async with db.begin_session() as db_sess:
            vfolder = VFolderRow(
                id=vfolder_id,
                name=f"test-vfolder-{vfolder_id.hex[:8]}",
                host="local:volume1",
                domain_name=domain_name,
                quota_scope_id=f"user:{user_id}",
                usage_mode=VFolderUsageMode.GENERAL,
                permission=VFolderMountPermission.READ_WRITE,
                max_files=0,
                max_size=None,
                num_files=0,
                cur_size=0,
                creator=f"test-{user_id.hex[:8]}@example.com",
                unmanaged_path=None,
                ownership_type=VFolderOwnershipType.USER,
                user=user_id,
                group=None,
                cloneable=False,
                status=status,
            )
            db_sess.add(vfolder)
            await db_sess.flush()

    async def _vfolder_exists(self, db: ExtendedAsyncSAEngine, vfolder_id: uuid.UUID) -> bool:
        """Check if vfolder exists in DB."""
        import sqlalchemy as sa

        async with db.begin_readonly_session() as session:
            query = sa.select(VFolderRow.id).where(VFolderRow.id == vfolder_id)
            result = await session.execute(query)
            return result.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "status",
        [
            VFolderOperationStatus.DELETE_COMPLETE,
            VFolderOperationStatus.DELETE_PENDING,
        ],
        ids=["delete_complete", "delete_pending"],
    )
    async def test_purge_vfolder_success(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        test_domain_name: str,
        test_user: uuid.UUID,
        status: VFolderOperationStatus,
    ) -> None:
        """Test successful purge of vfolder with purgable status."""
        from ai.backend.manager.repositories.base.purger import Purger

        vfolder_id = uuid.uuid4()
        await self._create_vfolder_in_db(
            db_with_cleanup,
            vfolder_id=vfolder_id,
            domain_name=test_domain_name,
            user_id=test_user,
            status=status,
        )

        # Verify vfolder exists before purge
        assert await self._vfolder_exists(db_with_cleanup, vfolder_id)

        purger = Purger(row_class=VFolderRow, pk_value=vfolder_id)
        result = await vfolder_repository.purge_vfolder(purger)

        # Verify result contains correct data
        assert result.id == vfolder_id
        assert result.status == status

        # Verify vfolder is deleted from DB
        assert not await self._vfolder_exists(db_with_cleanup, vfolder_id)

    @pytest.mark.asyncio
    async def test_purge_vfolder_not_found(
        self,
        vfolder_repository: VfolderRepository,
    ) -> None:
        """Test purge fails when vfolder doesn't exist."""
        from ai.backend.manager.errors.storage import VFolderNotFound
        from ai.backend.manager.repositories.base.purger import Purger

        non_existent_id = uuid.uuid4()
        purger = Purger(row_class=VFolderRow, pk_value=non_existent_id)

        with pytest.raises(VFolderNotFound):
            await vfolder_repository.purge_vfolder(purger)
