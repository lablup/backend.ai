from __future__ import annotations

import enum
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.types import BinarySize, ResourceSlot, VFolderMountPolicy, VFolderUsageMode
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.data.vfolder.types import (
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountSpec
from ai.backend.manager.errors.vfolder_auto_mount import VFolderAutoMountVFolderOutsideScope
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.models.vfolder_auto_mount.creators import VFolderAutoMountCreator
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.vfolder_auto_mount.repository import (
    VFolderAutoMountRepository,
)
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder

_DOMAIN_NAME = "test-domain"


class _FolderLocation(enum.Enum):
    PERSONAL_PROJECT_OF_THE_USER = enum.auto()
    GENERAL_PROJECT_CREATED_BY_THE_USER = enum.auto()
    PERSONAL_PROJECT_OF_ANOTHER_USER = enum.auto()


@dataclass(frozen=True)
class _FolderRegisteredToUserCase:
    name: str
    location: _FolderLocation
    ownership_type: VFolderOwnershipType


@dataclass(frozen=True)
class _ProjectsByFolderLocation:
    user_id: UserID
    project_ids: dict[_FolderLocation, ProjectID]


@dataclass(frozen=True)
class _RegisteringAFolderToAUser:
    repository: VFolderAutoMountRepository
    creator: VFolderAutoMountCreator


class TestRegisteringAFolderToAUser:
    @pytest.fixture
    async def database(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine]:
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
                VFolderRow,
                VirtualEntityRow,
                EntityMembershipRow,
                EntityMembershipCapRow,
                ScopeBindingRow,
                VFolderAutoMountRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def projects_by_folder_location(
        self, database: ExtendedAsyncSAEngine
    ) -> _ProjectsByFolderLocation:
        domain_id = DomainID(uuid.uuid4())
        user_id = UserID(uuid.uuid4())
        another_user_id = UserID(uuid.uuid4())
        personal_project_id = ProjectID(uuid.uuid4())
        general_project_id = ProjectID(uuid.uuid4())
        another_personal_project_id = ProjectID(uuid.uuid4())
        async with database.begin_session() as db_sess:
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
            for owner_id, username in ((user_id, "user"), (another_user_id, "another-user")):
                db_sess.add(
                    UserRow(
                        uuid=owner_id,
                        username=username,
                        email=f"{username}@example.com",
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
            for project_id, project_type, creator_id in (
                (personal_project_id, ProjectType.PERSONAL, user_id),
                (general_project_id, ProjectType.GENERAL, user_id),
                (another_personal_project_id, ProjectType.PERSONAL, another_user_id),
            ):
                db_sess.add(
                    ProjectRow(
                        id=project_id,
                        name=f"project-{project_id.hex[:8]}",
                        domain_name=_DOMAIN_NAME,
                        is_active=True,
                        total_resource_slots=ResourceSlot(),
                        allowed_vfolder_hosts={},
                        resource_policy="default",
                        type=project_type,
                        creator_id=creator_id,
                    )
                )
            await VirtualEntitySeeder().seed_user_scope(db_sess, user_id)
        return _ProjectsByFolderLocation(
            user_id=user_id,
            project_ids={
                _FolderLocation.PERSONAL_PROJECT_OF_THE_USER: personal_project_id,
                _FolderLocation.GENERAL_PROJECT_CREATED_BY_THE_USER: general_project_id,
                _FolderLocation.PERSONAL_PROJECT_OF_ANOTHER_USER: another_personal_project_id,
            },
        )

    @pytest.fixture
    async def registering_a_folder_to_a_user(
        self,
        database: ExtendedAsyncSAEngine,
        projects_by_folder_location: _ProjectsByFolderLocation,
        case: _FolderRegisteredToUserCase,
    ) -> _RegisteringAFolderToAUser:
        user_id = projects_by_folder_location.user_id
        project_id = projects_by_folder_location.project_ids[case.location]
        vfolder_id = VFolderUUID(uuid.uuid4())
        async with database.begin_session() as db_sess:
            db_sess.add(
                VFolderRow(
                    id=vfolder_id,
                    name="data",
                    host="local:volume1",
                    domain_name=_DOMAIN_NAME,
                    quota_scope_id=f"project:{project_id}",
                    usage_mode=VFolderUsageMode.GENERAL,
                    default_mount_permission=VFolderMountPolicy.READ_WRITE,
                    ownership_type=case.ownership_type,
                    user=user_id if case.ownership_type == VFolderOwnershipType.USER else None,
                    group=project_id,
                    creator="user@example.com",
                    creator_id=user_id,
                    status=VFolderOperationStatus.READY,
                )
            )
        return _RegisteringAFolderToAUser(
            repository=VFolderAutoMountRepository(V2DBOpsProvider(database)),
            creator=VFolderAutoMountCreator(
                scope=user_id,
                spec=VFolderAutoMountSpec(
                    vfolder_id=vfolder_id,
                    mount_destination="/home/work/data",
                    subpath=".",
                    mount_permission=VFolderMountPermission.READ_WRITE,
                ),
            ),
        )

    @pytest.mark.parametrize(
        "case",
        [
            _FolderRegisteredToUserCase(
                name="personal-folder",
                location=_FolderLocation.PERSONAL_PROJECT_OF_THE_USER,
                ownership_type=VFolderOwnershipType.USER,
            ),
            _FolderRegisteredToUserCase(
                name="project-folder-of-the-personal-project",
                location=_FolderLocation.PERSONAL_PROJECT_OF_THE_USER,
                ownership_type=VFolderOwnershipType.GROUP,
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_registers_a_folder_of_the_users_personal_project(
        self, registering_a_folder_to_a_user: _RegisteringAFolderToAUser
    ) -> None:
        registering = registering_a_folder_to_a_user

        created = await registering.repository.create(registering.creator)

        assert created.vfolder_id == registering.creator.spec.vfolder_id

    @pytest.mark.parametrize(
        "case",
        [
            _FolderRegisteredToUserCase(
                name="general-project",
                location=_FolderLocation.GENERAL_PROJECT_CREATED_BY_THE_USER,
                ownership_type=VFolderOwnershipType.GROUP,
            ),
            _FolderRegisteredToUserCase(
                name="personal-project-of-another-user",
                location=_FolderLocation.PERSONAL_PROJECT_OF_ANOTHER_USER,
                ownership_type=VFolderOwnershipType.GROUP,
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_rejects_a_folder_outside_the_users_personal_project(
        self, registering_a_folder_to_a_user: _RegisteringAFolderToAUser
    ) -> None:
        registering = registering_a_folder_to_a_user

        with pytest.raises(VFolderAutoMountVFolderOutsideScope):
            await registering.repository.create(registering.creator)
