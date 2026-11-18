from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType, VFolderUUID
from ai.backend.common.types import BinarySize, ResourceSlot, VFolderMountPolicy, VFolderUsageMode
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.data.vfolder.types import VFolderOperationStatus, VFolderOwnershipType
from ai.backend.manager.errors.repository import AmbiguousEntityKeyError
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.models.vfolder.scopes import ProjectVFolderTarget, UserVFolderTarget
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder

_DOMAIN_NAME = "test-domain"
_OWNER_EMAIL = "owner@example.com"


@dataclass(frozen=True)
class _OwnerWithAPersonalAndAJoinedProject:
    user_id: UserID
    personal_project_id: ProjectID
    joined_project_id: ProjectID


@dataclass(frozen=True)
class _NameOfADeletedAndAReadyPersonalFolder:
    repository: VfolderRepository
    scopes: Sequence[OperationScope]
    name: str
    ready_vfolder_id: VFolderUUID


@dataclass(frozen=True)
class _NameOfAPersonalAndAJoinedProjectFolder:
    repository: VfolderRepository
    scopes: Sequence[OperationScope]
    name: str


class TestResolveVFolderIdByName:
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
                VirtualEntityRow,
                EntityMembershipRow,
                ScopeBindingRow,
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
    async def owner_with_a_personal_and_a_joined_project(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> _OwnerWithAPersonalAndAJoinedProject:
        user_id = UserID(uuid.uuid4())
        personal_project_id = ProjectID(uuid.uuid4())
        joined_project_id = ProjectID(uuid.uuid4())
        async with db_with_cleanup.begin_session() as db_sess:
            domain_id = DomainID(uuid.uuid4())
            db_sess.add(
                DomainRow(
                    id=domain_id,
                    name=_DOMAIN_NAME,
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
            await db_sess.flush()
            db_sess.add(
                UserRow(
                    uuid=user_id,
                    username="owner",
                    email=_OWNER_EMAIL,
                    password=None,
                    need_password_change=False,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    domain_name=_DOMAIN_NAME,
                    role=UserRole.USER,
                    resource_policy="default",
                    domain_id=domain_id,
                )
            )
            await db_sess.flush()
            db_sess.add(
                ProjectRow(
                    id=personal_project_id,
                    name=f"personal-{user_id.hex[:8]}",
                    domain_name=_DOMAIN_NAME,
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    resource_policy="default",
                    type=ProjectType.PERSONAL,
                    creator_id=user_id,
                )
            )
            db_sess.add(
                ProjectRow(
                    id=joined_project_id,
                    name="joined-project",
                    domain_name=_DOMAIN_NAME,
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    resource_policy="default",
                    type=ProjectType.GENERAL,
                )
            )
        return _OwnerWithAPersonalAndAJoinedProject(
            user_id=user_id,
            personal_project_id=personal_project_id,
            joined_project_id=joined_project_id,
        )

    @pytest.fixture
    async def name_of_a_deleted_and_a_ready_personal_folder(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        owner_with_a_personal_and_a_joined_project: _OwnerWithAPersonalAndAJoinedProject,
    ) -> _NameOfADeletedAndAReadyPersonalFolder:
        owner = owner_with_a_personal_and_a_joined_project
        async with db_with_cleanup.begin_session() as db_sess:
            await self._insert_vfolder_held_by_scope(
                db_sess,
                name="notes",
                status=VFolderOperationStatus.DELETE_COMPLETE,
                ownership_type=VFolderOwnershipType.USER,
                owner_id=owner.user_id,
                project_id=owner.personal_project_id,
                holder_scope=(UserEntityType(), owner.user_id),
            )
            ready_vfolder_id = await self._insert_vfolder_held_by_scope(
                db_sess,
                name="notes",
                status=VFolderOperationStatus.READY,
                ownership_type=VFolderOwnershipType.USER,
                owner_id=owner.user_id,
                project_id=owner.personal_project_id,
                holder_scope=(UserEntityType(), owner.user_id),
            )
        return _NameOfADeletedAndAReadyPersonalFolder(
            repository=vfolder_repository,
            scopes=[UserVFolderTarget(user_id=owner.user_id)],
            name="notes",
            ready_vfolder_id=ready_vfolder_id,
        )

    @pytest.fixture
    async def name_of_a_personal_and_a_joined_project_folder(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        vfolder_repository: VfolderRepository,
        owner_with_a_personal_and_a_joined_project: _OwnerWithAPersonalAndAJoinedProject,
    ) -> _NameOfAPersonalAndAJoinedProjectFolder:
        owner = owner_with_a_personal_and_a_joined_project
        async with db_with_cleanup.begin_session() as db_sess:
            await self._insert_vfolder_held_by_scope(
                db_sess,
                name="data",
                status=VFolderOperationStatus.READY,
                ownership_type=VFolderOwnershipType.USER,
                owner_id=owner.user_id,
                project_id=owner.personal_project_id,
                holder_scope=(UserEntityType(), owner.user_id),
            )
            await self._insert_vfolder_held_by_scope(
                db_sess,
                name="data",
                status=VFolderOperationStatus.READY,
                ownership_type=VFolderOwnershipType.GROUP,
                owner_id=None,
                project_id=owner.joined_project_id,
                holder_scope=(ProjectEntityType(), owner.joined_project_id),
            )
        return _NameOfAPersonalAndAJoinedProjectFolder(
            repository=vfolder_repository,
            scopes=[
                UserVFolderTarget(user_id=owner.user_id),
                ProjectVFolderTarget(project_id=owner.joined_project_id),
            ],
            name="data",
        )

    async def _insert_vfolder_held_by_scope(
        self,
        db_sess: AsyncSession,
        *,
        name: str,
        status: VFolderOperationStatus,
        ownership_type: VFolderOwnershipType,
        owner_id: UserID | None,
        project_id: ProjectID,
        holder_scope: tuple[EntityType, uuid.UUID],
    ) -> VFolderUUID:
        vfolder_id = VFolderUUID(uuid.uuid4())
        db_sess.add(
            VFolderRow(
                id=vfolder_id,
                name=name,
                host="local:volume1",
                domain_name=_DOMAIN_NAME,
                quota_scope_id=f"project:{project_id}",
                usage_mode=VFolderUsageMode.GENERAL,
                default_mount_permission=VFolderMountPolicy.READ_WRITE,
                max_files=0,
                max_size=None,
                num_files=0,
                cur_size=0,
                creator=_OWNER_EMAIL,
                unmanaged_path=None,
                ownership_type=ownership_type,
                user=owner_id,
                group=project_id,
                cloneable=False,
                status=status,
            )
        )
        await db_sess.flush()
        await VirtualEntitySeeder().create_in(
            db_sess, VFolderEntityType(), vfolder_id, [holder_scope]
        )
        return vfolder_id

    async def test_a_name_left_by_a_deleted_folder_resolves_to_the_ready_folder(
        self,
        name_of_a_deleted_and_a_ready_personal_folder: _NameOfADeletedAndAReadyPersonalFolder,
    ) -> None:
        situation = name_of_a_deleted_and_a_ready_personal_folder

        resolved = await situation.repository.resolve_vfolder_id_by_name(
            situation.scopes, situation.name
        )

        assert resolved == situation.ready_vfolder_id

    async def test_a_name_held_by_a_personal_and_a_joined_project_folder_is_ambiguous(
        self,
        name_of_a_personal_and_a_joined_project_folder: _NameOfAPersonalAndAJoinedProjectFolder,
    ) -> None:
        situation = name_of_a_personal_and_a_joined_project_folder

        with pytest.raises(AmbiguousEntityKeyError):
            await situation.repository.resolve_vfolder_id_by_name(situation.scopes, situation.name)
