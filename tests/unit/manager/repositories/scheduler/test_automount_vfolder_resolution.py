"""The auto-mounts a session gets, resolved through ``SchedulerRepository``."""

from __future__ import annotations

import enum
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.common.auth.password import PasswordHashAlgorithm, PasswordInfo
from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType, VFolderUUID
from ai.backend.common.data.vfolder_auto_mount.types import VFolderAutoMountScopeType
from ai.backend.common.types import (
    BinarySize,
    MountInfoEntry,
    MountPermission,
    QuotaScopeID,
    ResourceSlot,
    VFolderMountPolicy,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.data.session.draft import (
    KernelExecutionSpecDraft,
    KernelGroupDraft,
    ResourceSpecDraft,
    SessionIdentityDraft,
    SessionOptionsDraft,
    SessionResourceSpecDraft,
    SessionScopeDraft,
    SessionSpecDraft,
)
from ai.backend.manager.data.vfolder.types import VFolderMountPermission, VFolderOwnershipType
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy.row import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.user.row import UserRole, UserRow, UserStatus
from ai.backend.manager.models.vfolder.row import (
    VFolderRow,
    VFolderUserMountPolicyRow,
)
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# Volume part matches ``NOOP_STORAGE_VOLUME_NAME`` so
# ``ensure_host_permission_allowed`` short-circuits.
NOOP_VFOLDER_HOST = "proxy:noop"


def _password_info() -> PasswordInfo:
    return PasswordInfo(
        password="dummy",
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


class _Project(enum.Enum):
    """The projects of the session owner."""

    PERSONAL = enum.auto()
    OF_THE_SESSION = enum.auto()
    ANOTHER_JOINED = enum.auto()


@dataclass(frozen=True)
class _Folder:
    name: str
    project: _Project
    ownership_type: VFolderOwnershipType
    default_mount_permission: VFolderMountPolicy = VFolderMountPolicy.READ_WRITE
    vfolder_name: str | None = None


@dataclass(frozen=True)
class _AutoMount:
    folder_name: str
    scope_type: VFolderAutoMountScopeType
    mount_destination: str
    scope_project: _Project | None = None
    mount_permission: VFolderMountPermission = VFolderMountPermission.READ_WRITE
    deleted: bool = False


@dataclass(frozen=True)
class _RequestedMount:
    folder_name: str
    mount_destination: str


@dataclass(frozen=True)
class _ResolvedMount:
    folder_name: str
    kernel_path: str
    mount_permission: MountPermission = MountPermission.READ_WRITE


@dataclass(frozen=True)
class _SessionMountsCase:
    name: str
    folders: list[_Folder]
    auto_mounts: list[_AutoMount] = field(default_factory=list)
    requested_mounts: list[_RequestedMount] = field(default_factory=list)
    expected_mounts: list[_ResolvedMount] = field(default_factory=list)


@dataclass(frozen=True)
class _SessionOwner:
    user_id: UserID
    domain_name: DomainName
    project_ids: dict[_Project, ProjectID]


@dataclass(frozen=True)
class _ResolvingSessionMounts:
    repository: SchedulerRepository
    draft: SessionSpecDraft
    owner_id: UserID
    folder_names_by_id: dict[UUID, str]


class TestAutoMountVFolderResolution:
    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine]:
        async with with_tables(
            database_connection,
            [
                ResourceSlotTypeRow,
                DomainRow,
                ResourceGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                ProjectRow,
                AgentRow,
                VFolderRow,
                VFolderUserMountPolicyRow,
                ContainerRegistryRow,
                ImageRow,
                ResourcePresetRow,
                RuntimeVariantRow,
                EndpointRow,
                DeploymentRevisionPresetRow,
                DeploymentRevisionRow,
                DeploymentAutoScalingPolicyRow,
                DeploymentPolicyRow,
                SessionRow,
                KernelRow,
                ReplicaGroupRow,
                RoutingRow,
                VirtualEntityRow,
                EntityMembershipRow,
                ScopeBindingRow,
                VFolderAutoMountRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def session_owner(self, db_with_cleanup: ExtendedAsyncSAEngine) -> _SessionOwner:
        domain_id = DomainID(uuid.uuid4())
        domain_name = DomainName(f"test-domain-{uuid4().hex[:8]}")
        user_id = UserID(uuid.uuid4())
        project_ids = {project: ProjectID(uuid.uuid4()) for project in _Project}
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    id=domain_id,
                    name=domain_name,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={NOOP_VFOLDER_HOST: ["mount-in-session"]},
                    allowed_docker_registries=[],
                )
            )
            db_sess.add(
                UserResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=int(BinarySize.from_str("10GiB")),
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name="default",
                    max_vfolder_count=10,
                    max_quota_scope_size=int(BinarySize.from_str("100GiB")),
                    max_network_count=5,
                )
            )
            await db_sess.flush()
            db_sess.add(
                UserRow(
                    uuid=user_id,
                    username="owner",
                    email="owner@example.com",
                    password=_password_info(),
                    need_password_change=False,
                    full_name="Test User",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    resource_policy="default",
                    domain_id=domain_id,
                )
            )
            await db_sess.flush()
            for project, project_id in project_ids.items():
                db_sess.add(
                    ProjectRow(
                        id=project_id,
                        name=f"project-{project_id.hex[:6]}",
                        description="",
                        is_active=True,
                        domain_name=domain_name,
                        resource_policy="default",
                        total_resource_slots=ResourceSlot(),
                        allowed_vfolder_hosts={},
                        type=(
                            ProjectType.PERSONAL
                            if project is _Project.PERSONAL
                            else ProjectType.GENERAL
                        ),
                        creator_id=user_id if project is _Project.PERSONAL else None,
                    )
                )
            await db_sess.flush()
            seeder = VirtualEntitySeeder()
            for project_id in project_ids.values():
                await seeder.enroll_user_in_project(db_sess, project_id, user_id)
        return _SessionOwner(user_id=user_id, domain_name=domain_name, project_ids=project_ids)

    @pytest.fixture
    async def folder_ids(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        session_owner: _SessionOwner,
        case: _SessionMountsCase,
    ) -> dict[str, VFolderUUID]:
        folder_ids = {folder.name: VFolderUUID(uuid.uuid4()) for folder in case.folders}
        async with db_with_cleanup.begin_session() as db_sess:
            for folder in case.folders:
                project_id = session_owner.project_ids[folder.project]
                db_sess.add(
                    VFolderRow(
                        id=folder_ids[folder.name],
                        host=NOOP_VFOLDER_HOST,
                        domain_name=session_owner.domain_name,
                        quota_scope_id=QuotaScopeID.parse(f"project:{project_id}"),
                        name=folder.vfolder_name or folder.name,
                        creator="owner@example.com",
                        ownership_type=folder.ownership_type,
                        user=(
                            session_owner.user_id
                            if folder.ownership_type == VFolderOwnershipType.USER
                            else None
                        ),
                        group=project_id,
                        default_mount_permission=folder.default_mount_permission,
                    )
                )
                await db_sess.flush()
                await VirtualEntitySeeder().create_in(
                    db_sess,
                    VFolderEntityType(),
                    folder_ids[folder.name],
                    [(ProjectEntityType(), project_id)],
                )
        return folder_ids

    @pytest.fixture
    async def auto_mounts(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        session_owner: _SessionOwner,
        folder_ids: dict[str, VFolderUUID],
        case: _SessionMountsCase,
    ) -> None:
        async with db_with_cleanup.begin_session() as db_sess:
            for auto_mount in case.auto_mounts:
                db_sess.add(
                    VFolderAutoMountRow(
                        scope_type=auto_mount.scope_type,
                        scope_id=(
                            session_owner.user_id
                            if auto_mount.scope_project is None
                            else session_owner.project_ids[auto_mount.scope_project]
                        ),
                        vfolder_id=folder_ids[auto_mount.folder_name],
                        mount_destination=auto_mount.mount_destination,
                        mount_permission=auto_mount.mount_permission,
                        deleted_at=datetime.now(UTC) if auto_mount.deleted else None,
                    )
                )

    @pytest.fixture
    def mock_storage_manager(self) -> MagicMock:
        client = MagicMock()
        client.get_mount_path = AsyncMock(return_value={"path": "/data/mount-base"})
        client.mkdir = AsyncMock()
        storage_manager = MagicMock()
        storage_manager.get_proxy_and_volume = MagicMock(return_value=("proxy", "volume"))
        storage_manager.get_manager_facing_client = MagicMock(return_value=client)
        return storage_manager

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        config_provider = MagicMock(spec=ManagerConfigProvider)
        config_provider.legacy_etcd_config_loader.get_vfolder_types = AsyncMock(
            return_value=["user", "group"]
        )
        # What is resolved is under test, not the owner's permission on it.
        config_provider.config.manager.rbac.enforcement_enabled = False
        return config_provider

    @pytest.fixture
    def resolving_session_mounts(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        mock_config_provider: MagicMock,
        mock_storage_manager: MagicMock,
        session_owner: _SessionOwner,
        folder_ids: dict[str, VFolderUUID],
        auto_mounts: None,
        case: _SessionMountsCase,
    ) -> _ResolvingSessionMounts:
        return _ResolvingSessionMounts(
            repository=SchedulerRepository(
                db_with_cleanup,
                ReconcileOpsProvider(db_with_cleanup),
                AsyncMock(spec=ValkeyStatClient),
                AsyncMock(spec=ValkeyScheduleClient),
                mock_config_provider,
                mock_storage_manager,
                RbacPermissionCheckRepository(
                    PermissionOpsProvider(db_with_cleanup), mock_config_provider
                ),
                key_provider_pool=KeyProviderPool(
                    providers=[], write_provider_type=KeyProviderType.PLAIN
                ),
            ),
            draft=SessionSpecDraft(
                resource_spec=SessionResourceSpecDraft(
                    identity=SessionIdentityDraft(
                        creation_id="auto-mount",
                        session_name="auto-mount",
                        user_uuid=session_owner.user_id,
                    ),
                    resource=ResourceSpecDraft(
                        options=SessionOptionsDraft(
                            kernel_groups=(
                                KernelGroupDraft(
                                    role="main",
                                    replica_count=1,
                                    execution_spec=KernelExecutionSpecDraft(
                                        mounts=tuple(
                                            MountInfoEntry(
                                                vfolder_id=folder_ids[requested.folder_name],
                                                mount_destination=requested.mount_destination,
                                            )
                                            for requested in case.requested_mounts
                                        )
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
                scope=SessionScopeDraft(
                    domain_name=session_owner.domain_name,
                    project_id=session_owner.project_ids[_Project.OF_THE_SESSION],
                    resource_group_name=None,
                ),
            ),
            owner_id=session_owner.user_id,
            folder_names_by_id={folder_id: name for name, folder_id in folder_ids.items()},
        )

    @pytest.mark.parametrize(
        "case",
        [
            _SessionMountsCase(
                name="user-auto-mount",
                folders=[_Folder("data", _Project.PERSONAL, VFolderOwnershipType.USER)],
                auto_mounts=[_AutoMount("data", VFolderAutoMountScopeType.USER, "/opt-data/data")],
                expected_mounts=[_ResolvedMount("data", "/opt-data/data")],
            ),
            _SessionMountsCase(
                name="user-auto-mount-of-a-project-folder-in-the-personal-project",
                folders=[_Folder("data", _Project.PERSONAL, VFolderOwnershipType.GROUP)],
                auto_mounts=[_AutoMount("data", VFolderAutoMountScopeType.USER, "/home/work/data")],
                expected_mounts=[_ResolvedMount("data", "/home/work/data")],
            ),
            _SessionMountsCase(
                name="auto-mount-of-the-session-project",
                folders=[_Folder("data", _Project.OF_THE_SESSION, VFolderOwnershipType.GROUP)],
                auto_mounts=[
                    _AutoMount(
                        "data",
                        VFolderAutoMountScopeType.PROJECT,
                        "/home/work/data",
                        scope_project=_Project.OF_THE_SESSION,
                    )
                ],
                expected_mounts=[_ResolvedMount("data", "/home/work/data")],
            ),
            _SessionMountsCase(
                name="auto-mount-of-another-joined-project",
                folders=[_Folder("data", _Project.ANOTHER_JOINED, VFolderOwnershipType.GROUP)],
                auto_mounts=[
                    _AutoMount(
                        "data",
                        VFolderAutoMountScopeType.PROJECT,
                        "/home/work/data",
                        scope_project=_Project.ANOTHER_JOINED,
                    )
                ],
            ),
            _SessionMountsCase(
                name="deleted-auto-mount",
                folders=[_Folder("data", _Project.PERSONAL, VFolderOwnershipType.USER)],
                auto_mounts=[
                    _AutoMount(
                        "data", VFolderAutoMountScopeType.USER, "/home/work/data", deleted=True
                    )
                ],
            ),
            _SessionMountsCase(
                name="dot-name-without-an-auto-mount",
                folders=[_Folder(".config", _Project.PERSONAL, VFolderOwnershipType.USER)],
            ),
            _SessionMountsCase(
                name="mount-policy-none",
                folders=[
                    _Folder(
                        "data",
                        _Project.OF_THE_SESSION,
                        VFolderOwnershipType.GROUP,
                        default_mount_permission=VFolderMountPolicy.NONE,
                    )
                ],
                auto_mounts=[
                    _AutoMount(
                        "data",
                        VFolderAutoMountScopeType.PROJECT,
                        "/home/work/data",
                        scope_project=_Project.OF_THE_SESSION,
                    )
                ],
            ),
            _SessionMountsCase(
                name="mount-policy-narrower-than-the-auto-mount",
                folders=[
                    _Folder(
                        "data",
                        _Project.OF_THE_SESSION,
                        VFolderOwnershipType.GROUP,
                        default_mount_permission=VFolderMountPolicy.READ_ONLY,
                    )
                ],
                auto_mounts=[
                    _AutoMount(
                        "data",
                        VFolderAutoMountScopeType.PROJECT,
                        "/home/work/data",
                        scope_project=_Project.OF_THE_SESSION,
                    )
                ],
                expected_mounts=[
                    _ResolvedMount("data", "/home/work/data", MountPermission.READ_ONLY)
                ],
            ),
            _SessionMountsCase(
                name="auto-mount-narrower-than-the-mount-policy",
                folders=[_Folder("data", _Project.PERSONAL, VFolderOwnershipType.USER)],
                auto_mounts=[
                    _AutoMount(
                        "data",
                        VFolderAutoMountScopeType.USER,
                        "/home/work/data",
                        mount_permission=VFolderMountPermission.READ_ONLY,
                    )
                ],
                expected_mounts=[
                    _ResolvedMount("data", "/home/work/data", MountPermission.READ_ONLY)
                ],
            ),
            _SessionMountsCase(
                name="requested-mount-above-the-auto-mount-destination",
                folders=[
                    _Folder("data", _Project.PERSONAL, VFolderOwnershipType.USER),
                    _Folder("requested", _Project.PERSONAL, VFolderOwnershipType.USER),
                ],
                auto_mounts=[
                    _AutoMount("data", VFolderAutoMountScopeType.USER, "/home/work/shared/data")
                ],
                requested_mounts=[_RequestedMount("requested", "/home/work/shared")],
                expected_mounts=[_ResolvedMount("requested", "/home/work/shared")],
            ),
            _SessionMountsCase(
                name="requested-mount-below-the-auto-mount-destination",
                folders=[
                    _Folder("data", _Project.PERSONAL, VFolderOwnershipType.USER),
                    _Folder("requested", _Project.PERSONAL, VFolderOwnershipType.USER),
                ],
                auto_mounts=[
                    _AutoMount("data", VFolderAutoMountScopeType.USER, "/home/work/shared")
                ],
                requested_mounts=[_RequestedMount("requested", "/home/work/shared/requested")],
                expected_mounts=[_ResolvedMount("requested", "/home/work/shared/requested")],
            ),
            _SessionMountsCase(
                name="auto-mounted-folder-requested-at-another-destination",
                folders=[_Folder("data", _Project.PERSONAL, VFolderOwnershipType.USER)],
                auto_mounts=[_AutoMount("data", VFolderAutoMountScopeType.USER, "/home/work/data")],
                requested_mounts=[_RequestedMount("data", "/home/work/requested")],
                expected_mounts=[
                    _ResolvedMount("data", "/home/work/requested"),
                    _ResolvedMount("data", "/home/work/data"),
                ],
            ),
            _SessionMountsCase(
                name="same-destination-in-the-user-and-the-session-project",
                folders=[
                    _Folder("of-user", _Project.PERSONAL, VFolderOwnershipType.USER),
                    _Folder("of-project", _Project.OF_THE_SESSION, VFolderOwnershipType.GROUP),
                ],
                auto_mounts=[
                    _AutoMount("of-user", VFolderAutoMountScopeType.USER, "/home/work/data"),
                    _AutoMount(
                        "of-project",
                        VFolderAutoMountScopeType.PROJECT,
                        "/home/work/data",
                        scope_project=_Project.OF_THE_SESSION,
                    ),
                ],
                expected_mounts=[_ResolvedMount("of-project", "/home/work/data")],
            ),
            _SessionMountsCase(
                name="own-local-requested-where-the-project-local-is-mounted",
                folders=[
                    _Folder(
                        "of-user",
                        _Project.PERSONAL,
                        VFolderOwnershipType.USER,
                        vfolder_name=".local",
                    ),
                    _Folder(
                        "of-project",
                        _Project.OF_THE_SESSION,
                        VFolderOwnershipType.GROUP,
                        vfolder_name=".local",
                    ),
                ],
                requested_mounts=[_RequestedMount("of-user", "/home/work/.local")],
                expected_mounts=[_ResolvedMount("of-user", "/home/work/.local")],
            ),
            _SessionMountsCase(
                name="own-local-requested-away-from-the-project-local",
                folders=[
                    _Folder(
                        "of-user",
                        _Project.PERSONAL,
                        VFolderOwnershipType.USER,
                        vfolder_name=".local",
                    ),
                    _Folder(
                        "of-project",
                        _Project.OF_THE_SESSION,
                        VFolderOwnershipType.GROUP,
                        vfolder_name=".local",
                    ),
                ],
                requested_mounts=[_RequestedMount("of-user", "/home/work/in1")],
                expected_mounts=[
                    _ResolvedMount("of-user", "/home/work/in1"),
                    _ResolvedMount("of-project", "/home/work/.local"),
                ],
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_resolves_the_requested_mounts_and_the_auto_mounts(
        self, resolving_session_mounts: _ResolvingSessionMounts, case: _SessionMountsCase
    ) -> None:
        resolving = resolving_session_mounts

        mounts_by_role = await resolving.repository._resolve_vfolder_mounts_by_role(
            resolving.draft, None
        )

        assert [
            _ResolvedMount(
                resolving.folder_names_by_id[mount.vfid.folder_id],
                str(mount.kernel_path),
                mount.mount_perm,
            )
            for mount in mounts_by_role["main"]
        ] == case.expected_mounts

    @pytest.mark.parametrize(
        "case",
        [
            _SessionMountsCase(
                name="session-project",
                folders=[_Folder(".local", _Project.OF_THE_SESSION, VFolderOwnershipType.GROUP)],
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_mounts_the_owners_directory_of_the_project_local_folder(
        self, resolving_session_mounts: _ResolvingSessionMounts
    ) -> None:
        resolving = resolving_session_mounts

        mounts_by_role = await resolving.repository._resolve_vfolder_mounts_by_role(
            resolving.draft, None
        )

        (project_local_mount,) = mounts_by_role["main"]
        assert project_local_mount.kernel_path == PurePosixPath("/home/work/.local")
        assert project_local_mount.vfsubpath == PurePosixPath(resolving.owner_id.hex)
