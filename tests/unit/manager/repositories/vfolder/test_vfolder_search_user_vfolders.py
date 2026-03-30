"""
Tests for VfolderRepository.search_user_vfolders() functionality.
Verifies that user-scoped vfolder search includes vfolders where the user is the owner
(VFolderRow.user) or has been granted permission (via VFolderPermissionRow).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.types import BinarySize, ResourceSlot, VFolderUsageMode
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.data.vfolder.types import (
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderPermissionRow, VFolderRow
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.repositories.vfolder.types import UserVFolderSearchScope
from ai.backend.testutils.db import with_tables


class TestVfolderSearchUserVfolders:
    """Tests for VfolderRepository.search_user_vfolders()"""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
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
    async def vfolder_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> VfolderRepository:
        return VfolderRepository(db=db_with_cleanup)

    @pytest.fixture
    async def test_data(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[dict[str, uuid.UUID], None]:
        """Create two users with vfolders: user_a has 2 vfolders, user_b has 1 (all GROUP-owned)."""
        domain_name = "test-domain"
        user_a_id = uuid.uuid4()
        user_b_id = uuid.uuid4()
        project_id = uuid.uuid4()
        vfolder_1_id = uuid.uuid4()
        vfolder_2_id = uuid.uuid4()
        vfolder_3_id = uuid.uuid4()

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
                UserResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_network_count=3,
                )
            )
            db_sess.add(
                KeyPairResourcePolicyRow(
                    name="default",
                    total_resource_slots=ResourceSlot(),
                    max_session_lifetime=0,
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=5,
                    max_containers_per_session=1,
                    idle_timeout=3600,
                )
            )
            await db_sess.flush()

            db_sess.add(
                UserRow(
                    uuid=user_a_id,
                    username="usera",
                    email="usera@example.com",
                    password=None,
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy="default",
                )
            )
            db_sess.add(
                UserRow(
                    uuid=user_b_id,
                    username="userb",
                    email="userb@example.com",
                    password=None,
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy="default",
                )
            )
            await db_sess.flush()

            db_sess.add(
                KeyPairRow(
                    user_id="usera@example.com",
                    user=user_a_id,
                    access_key="TESTKEY0000000A",
                    secret_key="test-secret-a",
                    is_active=True,
                    is_admin=False,
                    resource_policy="default",
                    rate_limit=1000,
                )
            )
            db_sess.add(
                KeyPairRow(
                    user_id="userb@example.com",
                    user=user_b_id,
                    access_key="TESTKEY0000000B",
                    secret_key="test-secret-b",
                    is_active=True,
                    is_admin=False,
                    resource_policy="default",
                    rate_limit=1000,
                )
            )
            await db_sess.flush()

            db_sess.add(
                GroupRow(
                    id=project_id,
                    name="project-a",
                    domain_name=domain_name,
                    description="Test project-a",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    resource_policy="default",
                    type=ProjectType.GENERAL,
                )
            )
            await db_sess.flush()

            for vid, user_id, name in [
                (vfolder_1_id, user_a_id, "vfolder-1"),
                (vfolder_2_id, user_a_id, "vfolder-2"),
                (vfolder_3_id, user_b_id, "vfolder-3"),
            ]:
                db_sess.add(
                    VFolderRow(
                        id=vid,
                        name=name,
                        host="local:volume1",
                        domain_name=domain_name,
                        quota_scope_id=f"project:{project_id}",
                        usage_mode=VFolderUsageMode.GENERAL,
                        permission=VFolderMountPermission.READ_WRITE,
                        max_files=0,
                        max_size=None,
                        num_files=0,
                        cur_size=0,
                        creator="usera@example.com",
                        unmanaged_path=None,
                        ownership_type=VFolderOwnershipType.GROUP,
                        user=user_id,
                        group=project_id,
                        cloneable=False,
                        status=VFolderOperationStatus.READY,
                    )
                )
            await db_sess.flush()

        yield {
            "user_a_id": user_a_id,
            "user_b_id": user_b_id,
            "vfolder_1_id": vfolder_1_id,
            "vfolder_2_id": vfolder_2_id,
            "vfolder_3_id": vfolder_3_id,
        }

    async def test_returns_only_vfolders_for_target_user(
        self,
        vfolder_repository: VfolderRepository,
        test_data: dict[str, uuid.UUID],
    ) -> None:
        """search_user_vfolders returns only vfolders where VFolderRow.user matches the target user."""
        scope = UserVFolderSearchScope(user_id=test_data["user_a_id"])
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await vfolder_repository.search_user_vfolders(querier, scope)

        assert result.total_count == 2
        assert len(result.items) == 2
        returned_ids = {item.id for item in result.items}
        assert returned_ids == {test_data["vfolder_1_id"], test_data["vfolder_2_id"]}

    async def test_does_not_return_vfolders_from_other_user(
        self,
        vfolder_repository: VfolderRepository,
        test_data: dict[str, uuid.UUID],
    ) -> None:
        """search_user_vfolders for user_b returns only vfolders with user_b as VFolderRow.user."""
        scope = UserVFolderSearchScope(user_id=test_data["user_b_id"])
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await vfolder_repository.search_user_vfolders(querier, scope)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.items[0].id == test_data["vfolder_3_id"]

    async def test_pagination_fields(
        self,
        vfolder_repository: VfolderRepository,
        test_data: dict[str, uuid.UUID],
    ) -> None:
        """search_user_vfolders returns correct pagination fields."""
        scope = UserVFolderSearchScope(user_id=test_data["user_a_id"])
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await vfolder_repository.search_user_vfolders(querier, scope)

        assert result.has_next_page is False
        assert result.has_previous_page is False

    @pytest.fixture
    async def mixed_ownership_data(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[dict[str, uuid.UUID], None]:
        """Create a user with both USER-owned and GROUP-owned vfolders."""
        domain_name = "test-domain"
        user_id = uuid.uuid4()
        project_id = uuid.uuid4()
        user_vfolder_id = uuid.uuid4()
        group_vfolder_id = uuid.uuid4()

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
                UserResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_network_count=3,
                )
            )
            db_sess.add(
                KeyPairResourcePolicyRow(
                    name="default",
                    total_resource_slots=ResourceSlot(),
                    max_session_lifetime=0,
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=5,
                    max_containers_per_session=1,
                    idle_timeout=3600,
                )
            )
            await db_sess.flush()

            db_sess.add(
                UserRow(
                    uuid=user_id,
                    username="testuser",
                    email="test@example.com",
                    password=None,
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy="default",
                )
            )
            await db_sess.flush()

            db_sess.add(
                KeyPairRow(
                    user_id="test@example.com",
                    user=user_id,
                    access_key="TESTKEY0000000M",
                    secret_key="test-secret-m",
                    is_active=True,
                    is_admin=False,
                    resource_policy="default",
                    rate_limit=1000,
                )
            )
            await db_sess.flush()

            db_sess.add(
                GroupRow(
                    id=project_id,
                    name="project-mixed",
                    domain_name=domain_name,
                    description="Test project",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    resource_policy="default",
                    type=ProjectType.GENERAL,
                )
            )
            await db_sess.flush()

            # USER-owned vfolder
            db_sess.add(
                VFolderRow(
                    id=user_vfolder_id,
                    name="my-personal-vfolder",
                    host="local:volume1",
                    domain_name=domain_name,
                    quota_scope_id=f"user:{user_id}",
                    usage_mode=VFolderUsageMode.GENERAL,
                    permission=VFolderMountPermission.READ_WRITE,
                    max_files=0,
                    max_size=None,
                    num_files=0,
                    cur_size=0,
                    creator="test@example.com",
                    unmanaged_path=None,
                    ownership_type=VFolderOwnershipType.USER,
                    user=user_id,
                    group=None,
                    cloneable=False,
                    status=VFolderOperationStatus.READY,
                )
            )
            # GROUP-owned vfolder with same user
            db_sess.add(
                VFolderRow(
                    id=group_vfolder_id,
                    name="project-shared-vfolder",
                    host="local:volume1",
                    domain_name=domain_name,
                    quota_scope_id=f"project:{project_id}",
                    usage_mode=VFolderUsageMode.GENERAL,
                    permission=VFolderMountPermission.READ_WRITE,
                    max_files=0,
                    max_size=None,
                    num_files=0,
                    cur_size=0,
                    creator="test@example.com",
                    unmanaged_path=None,
                    ownership_type=VFolderOwnershipType.GROUP,
                    user=user_id,
                    group=project_id,
                    cloneable=False,
                    status=VFolderOperationStatus.READY,
                )
            )
            await db_sess.flush()

        yield {
            "user_id": user_id,
            "user_vfolder_id": user_vfolder_id,
            "group_vfolder_id": group_vfolder_id,
        }

    async def test_returns_vfolders_regardless_of_ownership_type(
        self,
        vfolder_repository: VfolderRepository,
        mixed_ownership_data: dict[str, uuid.UUID],
    ) -> None:
        """search_user_vfolders returns both USER-owned and GROUP-owned vfolders
        as long as VFolderRow.user matches, regardless of ownership_type."""
        scope = UserVFolderSearchScope(user_id=mixed_ownership_data["user_id"])
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await vfolder_repository.search_user_vfolders(querier, scope)

        assert result.total_count == 2
        returned_ids = {item.id for item in result.items}
        assert returned_ids == {
            mixed_ownership_data["user_vfolder_id"],
            mixed_ownership_data["group_vfolder_id"],
        }

    async def test_nonexistent_user_raises_error(
        self,
        vfolder_repository: VfolderRepository,
        test_data: dict[str, uuid.UUID],
    ) -> None:
        """search_user_vfolders raises UserNotFound for a nonexistent user."""
        scope = UserVFolderSearchScope(user_id=uuid.uuid4())
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        with pytest.raises(UserNotFound):
            await vfolder_repository.search_user_vfolders(querier, scope)

    @pytest.fixture
    async def permission_data(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[dict[str, uuid.UUID], None]:
        """Create two users where user_a owns vfolders and user_b has permission on one of them.

        - vfolder_owned: owned by user_a
        - vfolder_shared: owned by user_b, user_a has READ_ATTRIBUTE permission
        - vfolder_no_access: owned by user_b, user_a has no permission
        """
        domain_name = "test-domain"
        user_a_id = uuid.uuid4()
        user_b_id = uuid.uuid4()
        project_id = uuid.uuid4()
        vfolder_owned_id = uuid.uuid4()
        vfolder_shared_id = uuid.uuid4()
        vfolder_no_access_id = uuid.uuid4()

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
                UserResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=BinarySize.finite_from_str("10GiB"),
                    max_network_count=3,
                )
            )
            db_sess.add(
                KeyPairResourcePolicyRow(
                    name="default",
                    total_resource_slots=ResourceSlot(),
                    max_session_lifetime=0,
                    max_concurrent_sessions=10,
                    max_concurrent_sftp_sessions=5,
                    max_containers_per_session=1,
                    idle_timeout=3600,
                )
            )
            await db_sess.flush()

            db_sess.add(
                UserRow(
                    uuid=user_a_id,
                    username="usera",
                    email="usera@example.com",
                    password=None,
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy="default",
                )
            )
            db_sess.add(
                UserRow(
                    uuid=user_b_id,
                    username="userb",
                    email="userb@example.com",
                    password=None,
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    resource_policy="default",
                )
            )
            await db_sess.flush()

            db_sess.add(
                KeyPairRow(
                    user_id="usera@example.com",
                    user=user_a_id,
                    access_key="TESTKEY0000000P",
                    secret_key="test-secret-p",
                    is_active=True,
                    is_admin=False,
                    resource_policy="default",
                    rate_limit=1000,
                )
            )
            db_sess.add(
                KeyPairRow(
                    user_id="userb@example.com",
                    user=user_b_id,
                    access_key="TESTKEY0000000Q",
                    secret_key="test-secret-q",
                    is_active=True,
                    is_admin=False,
                    resource_policy="default",
                    rate_limit=1000,
                )
            )
            await db_sess.flush()

            db_sess.add(
                GroupRow(
                    id=project_id,
                    name="project-perm",
                    domain_name=domain_name,
                    description="Test project",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    resource_policy="default",
                    type=ProjectType.GENERAL,
                )
            )
            await db_sess.flush()

            # vfolder owned by user_a
            db_sess.add(
                VFolderRow(
                    id=vfolder_owned_id,
                    name="owned-by-a",
                    host="local:volume1",
                    domain_name=domain_name,
                    quota_scope_id=f"user:{user_a_id}",
                    usage_mode=VFolderUsageMode.GENERAL,
                    permission=VFolderMountPermission.READ_WRITE,
                    max_files=0,
                    max_size=None,
                    num_files=0,
                    cur_size=0,
                    creator="usera@example.com",
                    unmanaged_path=None,
                    ownership_type=VFolderOwnershipType.USER,
                    user=user_a_id,
                    group=None,
                    cloneable=False,
                    status=VFolderOperationStatus.READY,
                )
            )
            # vfolder owned by user_b, will be shared to user_a
            db_sess.add(
                VFolderRow(
                    id=vfolder_shared_id,
                    name="shared-to-a",
                    host="local:volume1",
                    domain_name=domain_name,
                    quota_scope_id=f"user:{user_b_id}",
                    usage_mode=VFolderUsageMode.GENERAL,
                    permission=VFolderMountPermission.READ_WRITE,
                    max_files=0,
                    max_size=None,
                    num_files=0,
                    cur_size=0,
                    creator="userb@example.com",
                    unmanaged_path=None,
                    ownership_type=VFolderOwnershipType.USER,
                    user=user_b_id,
                    group=None,
                    cloneable=False,
                    status=VFolderOperationStatus.READY,
                )
            )
            # vfolder owned by user_b, NOT shared to user_a
            db_sess.add(
                VFolderRow(
                    id=vfolder_no_access_id,
                    name="no-access-for-a",
                    host="local:volume1",
                    domain_name=domain_name,
                    quota_scope_id=f"user:{user_b_id}",
                    usage_mode=VFolderUsageMode.GENERAL,
                    permission=VFolderMountPermission.READ_WRITE,
                    max_files=0,
                    max_size=None,
                    num_files=0,
                    cur_size=0,
                    creator="userb@example.com",
                    unmanaged_path=None,
                    ownership_type=VFolderOwnershipType.USER,
                    user=user_b_id,
                    group=None,
                    cloneable=False,
                    status=VFolderOperationStatus.READY,
                )
            )
            await db_sess.flush()

            # Grant user_a permission on vfolder_shared
            db_sess.add(
                VFolderPermissionRow(
                    permission=VFolderMountPermission.READ_ONLY,
                    vfolder=vfolder_shared_id,
                    user=user_a_id,
                )
            )
            await db_sess.flush()

        yield {
            "user_a_id": user_a_id,
            "user_b_id": user_b_id,
            "vfolder_owned_id": vfolder_owned_id,
            "vfolder_shared_id": vfolder_shared_id,
            "vfolder_no_access_id": vfolder_no_access_id,
        }

    async def test_returns_vfolders_with_permission(
        self,
        vfolder_repository: VfolderRepository,
        permission_data: dict[str, uuid.UUID],
    ) -> None:
        """search_user_vfolders returns vfolders the user owns AND vfolders shared via permission."""
        scope = UserVFolderSearchScope(user_id=permission_data["user_a_id"])
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await vfolder_repository.search_user_vfolders(querier, scope)

        returned_ids = {item.id for item in result.items}
        assert returned_ids == {
            permission_data["vfolder_owned_id"],
            permission_data["vfolder_shared_id"],
        }
        assert result.total_count == 2

    async def test_does_not_return_vfolders_without_permission(
        self,
        vfolder_repository: VfolderRepository,
        permission_data: dict[str, uuid.UUID],
    ) -> None:
        """search_user_vfolders does not return vfolders the user neither owns nor has permission for."""
        scope = UserVFolderSearchScope(user_id=permission_data["user_a_id"])
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await vfolder_repository.search_user_vfolders(querier, scope)

        returned_ids = {item.id for item in result.items}
        assert permission_data["vfolder_no_access_id"] not in returned_ids

    async def test_no_duplicate_when_owner_has_permission(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        permission_data: dict[str, uuid.UUID],
        vfolder_repository: VfolderRepository,
    ) -> None:
        """When a user owns a vfolder AND has a permission row for it, it appears only once."""
        # Add a permission row for user_a on their own vfolder
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                VFolderPermissionRow(
                    permission=VFolderMountPermission.READ_ONLY,
                    vfolder=permission_data["vfolder_owned_id"],
                    user=permission_data["user_a_id"],
                )
            )
            await db_sess.flush()

        scope = UserVFolderSearchScope(user_id=permission_data["user_a_id"])
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await vfolder_repository.search_user_vfolders(querier, scope)

        returned_ids = [item.id for item in result.items]
        assert len(returned_ids) == 2
        assert set(returned_ids) == {
            permission_data["vfolder_owned_id"],
            permission_data["vfolder_shared_id"],
        }
