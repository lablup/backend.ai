"""
Tests for VfolderRepository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock, create_autospec

import pytest
import sqlalchemy as sa

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
from ai.backend.manager.models.resource_policy import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import (
    UserRole,
    UserRow,
    UserStatus,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.permission_controller.role_manager import RoleManager
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository


def _make_vfolder_create_params(
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


class TestVfolderRepository:
    """Test cases for VfolderRepository"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database engine that auto-cleans vfolder data after each test"""
        yield database_engine
        # Note: VFolderRow cleanup is handled by more specific fixtures due to FK constraints

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

        try:
            yield domain_name
        finally:
            async with db_with_cleanup.begin_session() as db_sess:
                await db_sess.execute(sa.delete(DomainRow).where(DomainRow.name == domain_name))

    @pytest.fixture
    async def test_resource_policy_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[str, None]:
        """Create test resource policies and return policy name"""
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

            project_policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=BinarySize.from_str("10GiB"),
                max_network_count=3,
            )
            db_sess.add(project_policy)
            await db_sess.flush()

        try:
            yield policy_name
        finally:
            async with db_with_cleanup.begin_session() as db_sess:
                await db_sess.execute(
                    sa.delete(UserResourcePolicyRow).where(
                        UserResourcePolicyRow.name == policy_name
                    )
                )
                await db_sess.execute(
                    sa.delete(ProjectResourcePolicyRow).where(
                        ProjectResourcePolicyRow.name == policy_name
                    )
                )

    @pytest.fixture
    async def test_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
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
                resource_policy=test_resource_policy_name,
            )
            db_sess.add(user)
            await db_sess.flush()

        try:
            yield user_uuid
        finally:
            async with db_with_cleanup.begin_session() as db_sess:
                await db_sess.execute(sa.delete(UserRow).where(UserRow.uuid == user_uuid))

    @pytest.fixture
    async def test_model_store_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain_name: str,
        test_resource_policy_name: str,
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
                resource_policy=test_resource_policy_name,
                type=ProjectType.MODEL_STORE,
            )
            db_sess.add(group)
            await db_sess.flush()

        try:
            yield group_uuid
        finally:
            async with db_with_cleanup.begin_session() as db_sess:
                await db_sess.execute(sa.delete(GroupRow).where(GroupRow.id == group_uuid))

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

    @pytest.fixture
    async def test_vfolder_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[uuid.UUID, None]:
        """Generate vfolder ID and cleanup after test"""
        folder_id = uuid.uuid4()
        yield folder_id
        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(sa.delete(VFolderRow).where(VFolderRow.id == folder_id))

    async def test_create_vfolder_with_read_only_permission_in_model_store(
        self,
        vfolder_repository: VfolderRepository,
        test_domain_name: str,
        test_user: uuid.UUID,
        test_model_store_group: uuid.UUID,
        test_vfolder_id: uuid.UUID,
    ) -> None:
        """Test creating vfolder with READ_ONLY permission in model-store group succeeds"""
        params = _make_vfolder_create_params(
            folder_id=test_vfolder_id,
            domain_name=test_domain_name,
            group_id=test_model_store_group,
            user_id=test_user,
            permission=VFolderMountPermission.READ_ONLY,
            usage_mode=VFolderUsageMode.MODEL,
        )

        vfolder_data = await vfolder_repository.create_vfolder_with_permission(
            params, create_owner_permission=True
        )

        assert vfolder_data.id == test_vfolder_id
        assert vfolder_data.name == params.name
        assert vfolder_data.permission == VFolderMountPermission.READ_ONLY
        assert vfolder_data.usage_mode == VFolderUsageMode.MODEL
        assert vfolder_data.ownership_type == VFolderOwnershipType.GROUP
        assert vfolder_data.group == test_model_store_group
