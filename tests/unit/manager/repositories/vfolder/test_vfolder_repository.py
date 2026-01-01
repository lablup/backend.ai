"""
Tests for VfolderRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, create_autospec

import pytest

from ai.backend.common.types import BinarySize, VFolderUsageMode
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.data.vfolder.types import (
    VFolderCreateParams,
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
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
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                VFolderRow,
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
                max_quota_scope_size=BinarySize.from_str("10GiB"),
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
                max_quota_scope_size=BinarySize.from_str("10GiB"),
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
