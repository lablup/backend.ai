"""
Tests for VfolderRepository.search_user_vfolders() with cloneable filter.
Verifies that the cloneable condition correctly filters vfolders.
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
from ai.backend.manager.models.vfolder.conditions import VFolderConditions
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.repositories.vfolder.types import UserVFolderSearchScope
from ai.backend.testutils.db import with_tables


class TestVfolderSearchFilter:
    """Tests for search_user_vfolders with filters."""

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
    async def cloneable_data(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[dict[str, uuid.UUID], None]:
        """Create vfolders with mixed cloneable values.

        user_a owns:
          - vf_clone_1 (cloneable=True, GENERAL)
          - vf_clone_2 (cloneable=True, DATA)
          - vf_noclone_1 (cloneable=False, GENERAL)

        user_b owns:
          - vf_shared_clone (cloneable=True, shared to user_a via permission)
          - vf_noclone_b (cloneable=False, NOT shared)
        """
        domain_name = "test-domain"
        user_a_id = uuid.uuid4()
        user_b_id = uuid.uuid4()
        project_id = uuid.uuid4()
        vf_clone_1 = uuid.uuid4()
        vf_clone_2 = uuid.uuid4()
        vf_noclone_1 = uuid.uuid4()
        vf_shared_clone = uuid.uuid4()
        vf_noclone_b = uuid.uuid4()

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
                    access_key="TESTKEYCLONE000A",
                    secret_key="test-secret-ca",
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
                    access_key="TESTKEYCLONE000B",
                    secret_key="test-secret-cb",
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
                    name="project-clone",
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

            # user_a's cloneable vfolder (GENERAL)
            db_sess.add(
                VFolderRow(
                    id=vf_clone_1,
                    name="clone-1",
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
                    cloneable=True,
                    status=VFolderOperationStatus.READY,
                )
            )
            # user_a's cloneable vfolder (DATA)
            db_sess.add(
                VFolderRow(
                    id=vf_clone_2,
                    name="clone-2",
                    host="local:volume1",
                    domain_name=domain_name,
                    quota_scope_id=f"user:{user_a_id}",
                    usage_mode=VFolderUsageMode.DATA,
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
                    cloneable=True,
                    status=VFolderOperationStatus.READY,
                )
            )
            # user_a's non-cloneable vfolder
            db_sess.add(
                VFolderRow(
                    id=vf_noclone_1,
                    name="noclone-1",
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
            # user_b's cloneable vfolder (shared to user_a)
            db_sess.add(
                VFolderRow(
                    id=vf_shared_clone,
                    name="shared-clone",
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
                    cloneable=True,
                    status=VFolderOperationStatus.READY,
                )
            )
            # user_b's non-cloneable vfolder (NOT shared)
            db_sess.add(
                VFolderRow(
                    id=vf_noclone_b,
                    name="noclone-b",
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

            # Grant user_a permission on user_b's cloneable vfolder
            db_sess.add(
                VFolderPermissionRow(
                    permission=VFolderMountPermission.READ_ONLY,
                    vfolder=vf_shared_clone,
                    user=user_a_id,
                )
            )
            await db_sess.flush()

        yield {
            "user_a_id": user_a_id,
            "user_b_id": user_b_id,
            "vf_clone_1": vf_clone_1,
            "vf_clone_2": vf_clone_2,
            "vf_noclone_1": vf_noclone_1,
            "vf_shared_clone": vf_shared_clone,
            "vf_noclone_b": vf_noclone_b,
        }

    async def test_cloneable_true_returns_only_cloneable_vfolders(
        self,
        vfolder_repository: VfolderRepository,
        cloneable_data: dict[str, uuid.UUID],
    ) -> None:
        """cloneable={eq: true} returns only cloneable=true vfolders (owned + shared)."""
        scope = UserVFolderSearchScope(user_id=cloneable_data["user_a_id"])
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[VFolderConditions.by_cloneable(True)],
            orders=[],
        )

        result = await vfolder_repository.search_user_vfolders(querier, scope)

        returned_ids = {item.id for item in result.items}
        assert returned_ids == {
            cloneable_data["vf_clone_1"],
            cloneable_data["vf_clone_2"],
            cloneable_data["vf_shared_clone"],
        }
        assert result.total_count == 3

    async def test_cloneable_false_returns_only_non_cloneable_vfolders(
        self,
        vfolder_repository: VfolderRepository,
        cloneable_data: dict[str, uuid.UUID],
    ) -> None:
        """cloneable={eq: false} returns only cloneable=false vfolders."""
        scope = UserVFolderSearchScope(user_id=cloneable_data["user_a_id"])
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[VFolderConditions.by_cloneable(False)],
            orders=[],
        )

        result = await vfolder_repository.search_user_vfolders(querier, scope)

        returned_ids = {item.id for item in result.items}
        assert returned_ids == {cloneable_data["vf_noclone_1"]}
        assert result.total_count == 1

    async def test_no_cloneable_filter_returns_all_vfolders(
        self,
        vfolder_repository: VfolderRepository,
        cloneable_data: dict[str, uuid.UUID],
    ) -> None:
        """No cloneable filter returns all visible vfolders (owned + shared)."""
        scope = UserVFolderSearchScope(user_id=cloneable_data["user_a_id"])
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await vfolder_repository.search_user_vfolders(querier, scope)

        returned_ids = {item.id for item in result.items}
        assert returned_ids == {
            cloneable_data["vf_clone_1"],
            cloneable_data["vf_clone_2"],
            cloneable_data["vf_noclone_1"],
            cloneable_data["vf_shared_clone"],
        }
        assert result.total_count == 4

    async def test_cloneable_filter_with_pagination(
        self,
        vfolder_repository: VfolderRepository,
        cloneable_data: dict[str, uuid.UUID],
    ) -> None:
        """cloneable filter works with pagination (correct total_count and has_next_page)."""
        scope = UserVFolderSearchScope(user_id=cloneable_data["user_a_id"])
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=2, offset=0),
            conditions=[VFolderConditions.by_cloneable(True)],
            orders=[],
        )

        result = await vfolder_repository.search_user_vfolders(querier, scope)

        assert result.total_count == 3
        assert len(result.items) == 2
        assert result.has_next_page is True

    async def test_cloneable_filter_combines_with_usage_mode(
        self,
        vfolder_repository: VfolderRepository,
        cloneable_data: dict[str, uuid.UUID],
    ) -> None:
        """cloneable filter combines correctly with other conditions (usage_mode)."""
        scope = UserVFolderSearchScope(user_id=cloneable_data["user_a_id"])
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                VFolderConditions.by_cloneable(True),
                VFolderConditions.by_usage_mode_in([VFolderUsageMode.GENERAL]),
            ],
            orders=[],
        )

        result = await vfolder_repository.search_user_vfolders(querier, scope)

        returned_ids = {item.id for item in result.items}
        # Only GENERAL + cloneable: clone-1 and shared-clone (clone-2 is DATA)
        assert returned_ids == {
            cloneable_data["vf_clone_1"],
            cloneable_data["vf_shared_clone"],
        }
        assert result.total_count == 2
