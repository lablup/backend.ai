"""
Tests for VfolderRepository.search_user_vfolders() with cloneable filter.
Verifies that the cloneable condition correctly filters vfolders.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy import Row

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.vfolder.types import VFolderUsageModeFilter
from ai.backend.common.types import BinarySize, ResourceSlot, VFolderMountPolicy, VFolderUsageMode
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.data.vfolder.types import (
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import (
    VFolderRow,
    VFolderUserMountPolicyRow,
)
from ai.backend.manager.models.vfolder.scopes import UserVFolderTarget
from ai.backend.manager.models.vfolder.searchable_fields import VFolderSearchableFields
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import EntityMembershipCapRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.filter_adapter import BaseFilterAdapter
from ai.backend.manager.repositories.base.querier import (
    BatchQuerierResult,
    execute_batch_querier,
)
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder


async def _search_vfolders(
    db: ExtendedAsyncSAEngine, querier: BatchQuerier, scope: OperationScope
) -> BatchQuerierResult[Row[Any]]:
    """What the read does, without the repository method that used to wrap it."""
    async with db.begin_readonly_session() as sess:
        return await execute_batch_querier(sess, sa.select(VFolderRow), querier, scopes=[scope])


class TestVfolderSearchFilter:
    """Tests for search_user_vfolders with filters."""

    @pytest.fixture
    def filter_adapter(self) -> BaseFilterAdapter:
        return BaseFilterAdapter()

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
                ProjectRow,
                ContainerRegistryRow,
                ImageRow,
                VFolderRow,
                VFolderUserMountPolicyRow,
                ModelCardRow,
                VirtualEntityRow,
                EntityMembershipRow,
                ScopeBindingRow,
                EntityMembershipCapRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def vfolder_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> VfolderRepository:
        return VfolderRepository(
            db=db_with_cleanup, v2_ops_provider=ShareOpsProvider(db_with_cleanup)
        )

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
        domain_id = DomainID(uuid.uuid4())
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
                    id=domain_id,
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
                    domain_id=domain_id,
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
                    domain_id=domain_id,
                )
            )
            await db_sess.flush()

            db_sess.add(
                KeyPairRow(
                    user=user_a_id,
                    access_key="TESTKEYCLONE000A",
                    secret_key=SecretValue("test-secret-ca"),
                    is_active=True,
                    is_admin=False,
                    resource_policy="default",
                    rate_limit=1000,
                )
            )
            db_sess.add(
                KeyPairRow(
                    user=user_b_id,
                    access_key="TESTKEYCLONE000B",
                    secret_key=SecretValue("test-secret-cb"),
                    is_active=True,
                    is_admin=False,
                    resource_policy="default",
                    rate_limit=1000,
                )
            )
            await db_sess.flush()

            db_sess.add(
                ProjectRow(
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
                    default_mount_permission=VFolderMountPolicy.READ_WRITE,
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
                    default_mount_permission=VFolderMountPolicy.READ_WRITE,
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
                    default_mount_permission=VFolderMountPolicy.READ_WRITE,
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
                    default_mount_permission=VFolderMountPolicy.READ_WRITE,
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
                    default_mount_permission=VFolderMountPolicy.READ_WRITE,
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

            # Each folder lands in the project that is its owner's alone (BEP-1077);
            # user_b's cloneable one reaches user_a as a capped edge, which is a share.
            seeder = VirtualEntitySeeder()
            personal_a, personal_b = uuid.uuid4(), uuid.uuid4()
            for owner_id, personal_id in [(user_a_id, personal_a), (user_b_id, personal_b)]:
                db_sess.add(
                    ProjectRow(
                        id=personal_id,
                        name=f"personal-{personal_id.hex[:8]}",
                        domain_name=domain_name,
                        is_active=True,
                        total_resource_slots=ResourceSlot(),
                        allowed_vfolder_hosts={},
                        resource_policy="default",
                        type=ProjectType.PERSONAL,
                        creator_id=owner_id,
                    )
                )
            await db_sess.flush()
            for vid in (vf_clone_1, vf_clone_2, vf_noclone_1):
                await seeder.create_in(
                    db_sess, VFolderEntityType(), vid, [(ProjectEntityType(), personal_a)]
                )
            for vid in (vf_shared_clone, vf_noclone_b):
                await seeder.create_in(
                    db_sess, VFolderEntityType(), vid, [(ProjectEntityType(), personal_b)]
                )
            await seeder.cap_edge(
                db_sess,
                await seeder.get_or_create_scope(db_sess, ProjectEntityType(), personal_a),
                await seeder.get_or_create_node(db_sess, VFolderEntityType(), vf_shared_clone),
                Permission.READ,
            )

        yield {
            "project_id": project_id,
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
        db_with_cleanup: ExtendedAsyncSAEngine,
        cloneable_data: dict[str, uuid.UUID],
        filter_adapter: BaseFilterAdapter,
    ) -> None:
        """cloneable={eq: true} returns only cloneable=true vfolders (owned + shared)."""
        scope = UserVFolderTarget(user_id=UserID(cloneable_data["user_a_id"]))
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=filter_adapter.apply_bool_filter(
                True, VFolderSearchableFields.own.cloneable.filter
            ),
            orders=[],
        )

        result = await _search_vfolders(db_with_cleanup, querier, scope)

        returned_ids = {item.id for item in [row.VFolderRow for row in result.rows]}
        assert returned_ids == {
            cloneable_data["vf_clone_1"],
            cloneable_data["vf_clone_2"],
            cloneable_data["vf_shared_clone"],
        }
        assert result.total_count == 3

    async def test_cloneable_false_returns_only_non_cloneable_vfolders(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        cloneable_data: dict[str, uuid.UUID],
        filter_adapter: BaseFilterAdapter,
    ) -> None:
        """cloneable={eq: false} returns only cloneable=false vfolders."""
        scope = UserVFolderTarget(user_id=UserID(cloneable_data["user_a_id"]))
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=filter_adapter.apply_bool_filter(
                False, VFolderSearchableFields.own.cloneable.filter
            ),
            orders=[],
        )

        result = await _search_vfolders(db_with_cleanup, querier, scope)

        returned_ids = {item.id for item in [row.VFolderRow for row in result.rows]}
        assert returned_ids == {cloneable_data["vf_noclone_1"]}
        assert result.total_count == 1

    async def test_no_cloneable_filter_returns_all_vfolders(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        cloneable_data: dict[str, uuid.UUID],
    ) -> None:
        """No cloneable filter returns all visible vfolders (owned + shared)."""
        scope = UserVFolderTarget(user_id=UserID(cloneable_data["user_a_id"]))
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

        result = await _search_vfolders(db_with_cleanup, querier, scope)

        returned_ids = {item.id for item in [row.VFolderRow for row in result.rows]}
        assert returned_ids == {
            cloneable_data["vf_clone_1"],
            cloneable_data["vf_clone_2"],
            cloneable_data["vf_noclone_1"],
            cloneable_data["vf_shared_clone"],
        }
        assert result.total_count == 4

    async def test_cloneable_filter_with_pagination(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        cloneable_data: dict[str, uuid.UUID],
        filter_adapter: BaseFilterAdapter,
    ) -> None:
        """cloneable filter works with pagination (correct total_count and has_next_page)."""
        scope = UserVFolderTarget(user_id=UserID(cloneable_data["user_a_id"]))
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=2, offset=0),
            conditions=filter_adapter.apply_bool_filter(
                True, VFolderSearchableFields.own.cloneable.filter
            ),
            orders=[],
        )

        result = await _search_vfolders(db_with_cleanup, querier, scope)

        assert result.total_count == 3
        assert len([row.VFolderRow for row in result.rows]) == 2
        assert result.has_next_page is True

    async def test_cloneable_filter_combines_with_usage_mode(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        cloneable_data: dict[str, uuid.UUID],
        filter_adapter: BaseFilterAdapter,
    ) -> None:
        """cloneable filter combines correctly with other conditions (usage_mode)."""
        scope = UserVFolderTarget(user_id=UserID(cloneable_data["user_a_id"]))
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                *filter_adapter.apply_bool_filter(
                    True, VFolderSearchableFields.own.cloneable.filter
                ),
                *filter_adapter.apply_enum_filter(
                    VFolderUsageModeFilter(in_=[VFolderUsageMode.GENERAL]),
                    VFolderSearchableFields.own.usage_mode.filter,
                ),
            ],
            orders=[],
        )

        result = await _search_vfolders(db_with_cleanup, querier, scope)

        returned_ids = {item.id for item in [row.VFolderRow for row in result.rows]}
        # Only GENERAL + cloneable: clone-1 and shared-clone (clone-2 is DATA)
        assert returned_ids == {
            cloneable_data["vf_clone_1"],
            cloneable_data["vf_shared_clone"],
        }
        assert result.total_count == 2

    @pytest.fixture
    async def model_cards(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        cloneable_data: dict[str, uuid.UUID],
    ) -> dict[str, uuid.UUID]:
        """A card on user_a's ``vf_clone_1`` and one on user_b's unshared ``vf_noclone_b``."""
        card_a = uuid.uuid4()
        card_b = uuid.uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            for card_id, name, vfolder_id, creator in (
                (card_a, "card-a", cloneable_data["vf_clone_1"], cloneable_data["user_a_id"]),
                (card_b, "card-b", cloneable_data["vf_noclone_b"], cloneable_data["user_b_id"]),
            ):
                db_sess.add(
                    ModelCardRow(
                        id=card_id,
                        name=name,
                        vfolder=vfolder_id,
                        domain="test-domain",
                        project=cloneable_data["project_id"],
                        creator=creator,
                    )
                )
        return {"card_a": card_a, "card_b": card_b}

    async def test_used_by_returns_the_vfolder_the_card_uses(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        cloneable_data: dict[str, uuid.UUID],
        model_cards: dict[str, uuid.UUID],
    ) -> None:
        scope = UserVFolderTarget(user_id=UserID(cloneable_data["user_a_id"]))
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                VFolderSearchableFields.linked.model_cards.used_by(
                    ModelCardID(model_cards["card_a"])
                ).condition
            ],
            orders=[],
        )

        result = await _search_vfolders(db_with_cleanup, querier, scope)

        assert [row.VFolderRow.id for row in result.rows] == [cloneable_data["vf_clone_1"]]
        assert result.total_count == 1

    async def test_used_by_leaves_out_a_vfolder_outside_the_scope(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        cloneable_data: dict[str, uuid.UUID],
        model_cards: dict[str, uuid.UUID],
    ) -> None:
        # card_b uses user_b's vfolder, which user_a's scope does not reach.
        scope = UserVFolderTarget(user_id=UserID(cloneable_data["user_a_id"]))
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[
                VFolderSearchableFields.linked.model_cards.used_by(
                    ModelCardID(model_cards["card_b"])
                ).condition
            ],
            orders=[],
        )

        result = await _search_vfolders(db_with_cleanup, querier, scope)

        assert result.rows == []
        assert result.total_count == 0
