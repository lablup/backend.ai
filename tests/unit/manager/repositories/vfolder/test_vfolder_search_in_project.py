"""
Tests for VfolderRepository.search_in_project() functionality.
Verifies that project-scoped vfolder search returns only vfolders belonging to the target project.
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
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.repositories.vfolder.types import ProjectVFolderSearchScope
from ai.backend.testutils.db import with_tables


class TestVfolderSearchInProject:
    """Tests for VfolderRepository.search_in_project()"""

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
        """Create two projects with vfolders: project_a has 2 vfolders, project_b has 1."""
        domain_name = "test-domain"
        user_id = uuid.uuid4()
        project_a_id = uuid.uuid4()
        project_b_id = uuid.uuid4()
        vfolder_a1_id = uuid.uuid4()
        vfolder_a2_id = uuid.uuid4()
        vfolder_b1_id = uuid.uuid4()

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
                    access_key="TESTKEY00000000",
                    secret_key="test-secret",
                    is_active=True,
                    is_admin=False,
                    resource_policy="default",
                    rate_limit=1000,
                )
            )
            await db_sess.flush()

            for gid, gname in [
                (project_a_id, "project-a"),
                (project_b_id, "project-b"),
            ]:
                db_sess.add(
                    GroupRow(
                        id=gid,
                        name=gname,
                        domain_name=domain_name,
                        description=f"Test {gname}",
                        is_active=True,
                        total_resource_slots=ResourceSlot(),
                        allowed_vfolder_hosts={},
                        resource_policy="default",
                        type=ProjectType.GENERAL,
                    )
                )
            await db_sess.flush()

            for vid, group_id, name in [
                (vfolder_a1_id, project_a_id, "vfolder-a1"),
                (vfolder_a2_id, project_a_id, "vfolder-a2"),
                (vfolder_b1_id, project_b_id, "vfolder-b1"),
            ]:
                db_sess.add(
                    VFolderRow(
                        id=vid,
                        name=name,
                        host="local:volume1",
                        domain_name=domain_name,
                        quota_scope_id=f"project:{group_id}",
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
                        group=group_id,
                        cloneable=False,
                        status=VFolderOperationStatus.READY,
                    )
                )
            await db_sess.flush()

        yield {
            "project_a_id": project_a_id,
            "project_b_id": project_b_id,
            "vfolder_a1_id": vfolder_a1_id,
            "vfolder_a2_id": vfolder_a2_id,
            "vfolder_b1_id": vfolder_b1_id,
        }

    async def test_returns_only_vfolders_in_target_project(
        self,
        vfolder_repository: VfolderRepository,
        test_data: dict[str, uuid.UUID],
    ) -> None:
        """search_in_project returns only vfolders belonging to the specified project."""
        scope = ProjectVFolderSearchScope(project_id=test_data["project_a_id"])
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await vfolder_repository.search_in_project(querier, scope)

        assert result.total_count == 2
        assert len(result.items) == 2
        returned_ids = {item.id for item in result.items}
        assert returned_ids == {test_data["vfolder_a1_id"], test_data["vfolder_a2_id"]}

    async def test_does_not_return_vfolders_from_other_project(
        self,
        vfolder_repository: VfolderRepository,
        test_data: dict[str, uuid.UUID],
    ) -> None:
        """search_in_project for project_b returns only its vfolder, not project_a's."""
        scope = ProjectVFolderSearchScope(project_id=test_data["project_b_id"])
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await vfolder_repository.search_in_project(querier, scope)

        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.items[0].id == test_data["vfolder_b1_id"]

    async def test_pagination_fields(
        self,
        vfolder_repository: VfolderRepository,
        test_data: dict[str, uuid.UUID],
    ) -> None:
        """search_in_project returns correct pagination fields."""
        scope = ProjectVFolderSearchScope(project_id=test_data["project_a_id"])
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await vfolder_repository.search_in_project(querier, scope)

        assert result.has_next_page is False
        assert result.has_previous_page is False
