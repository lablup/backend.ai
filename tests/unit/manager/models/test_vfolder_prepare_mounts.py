"""Tests for ``prepare_vfolder_mounts`` subpath handling."""

from __future__ import annotations

import enum
import uuid
from collections.abc import AsyncGenerator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.vfolder import VFolderEntityType, VFolderUUID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.types import (
    BinarySize,
    MountPermission,
    QuotaScopeID,
    ResourceSlot,
    VFolderMount,
    VFolderMountOptions,
    VFolderMountPolicy,
    VFolderMountRequest,
)
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.data.vfolder.types import VFolderOwnershipType
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.storage import VFolderNotFound, VFolderPermissionError
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.rbac_models import RoleRow, UserRoleRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_group import ResourceGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRole, UserRow, UserStatus
from ai.backend.manager.models.vfolder import (
    VFolderRow,
    VFolderUserMountPolicyRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.vfolder.mount import prepare_vfolder_mounts
from ai.backend.manager.types import UserScope
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class _VFolderOwner(enum.Enum):
    USER = enum.auto()
    SESSION_PROJECT = enum.auto()


@dataclass(frozen=True)
class _MountOfOwner:
    owner: _VFolderOwner
    mount_destination: str | None


@dataclass(frozen=True)
class _SameNamedVFoldersCase:
    name: str
    vfolder_name: str
    requested_mounts: list[_MountOfOwner]
    expected_mounts: list[_MountOfOwner]


@dataclass(frozen=True)
class _SameNamedVFolders:
    user_scope: UserScope
    vfolder_ids: dict[_VFolderOwner, UUID]


@dataclass(frozen=True)
class _UnmanagedMountPathCase:
    requested_mount_path: str
    expected_kernel_path: PurePosixPath


@dataclass(frozen=True)
class _UnmanagedVFolderOfUser:
    user_scope: UserScope
    vfolder_id: UUID


async def _held_in_full(
    vfolder_ids: Sequence[VFolderUUID],
) -> Mapping[EntityIdentifier, Permission]:
    """Every bit on every folder: what is resolved is under test, not the permission."""
    return dict.fromkeys(vfolder_ids, Permission.full())


def _password_info() -> PasswordInfo:
    return PasswordInfo(
        password="dummy",
        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
        rounds=100_000,
        salt_size=32,
    )


class TestPrepareVFolderMountsSubpathValidation:
    """Subpath escape validation happens before any DB query, so we can
    drive it with bare mocks. These cases lock in that ``..``, absolute
    paths, and otherwise-escaping inputs raise ``InvalidAPIParameters``
    regardless of vfolder availability."""

    @pytest.mark.parametrize(
        "bad_subpath",
        [
            pytest.param("..", id="parent-traversal"),
            pytest.param("/etc/passwd", id="absolute-path"),
            pytest.param("a/../../b", id="normalizes-above-root"),
        ],
    )
    async def test_root_escaping_subpath_is_rejected(self, bad_subpath: str) -> None:
        vfolder_uuid = uuid4()
        with pytest.raises(InvalidAPIParameters, match="must not escape"):
            await prepare_vfolder_mounts(
                conn=AsyncMock(),
                storage_manager=MagicMock(),
                allowed_vfolder_types=["user"],
                user_scope=UserScope(
                    domain_name="default",
                    group_id=uuid4(),
                    user_uuid=uuid4(),
                    user_role=UserRole.USER,
                ),
                resource_policy={},
                mount_requests=[
                    VFolderMountRequest(
                        ref=vfolder_uuid,
                        dst_path="/home/work/extra",
                        options=VFolderMountOptions(subpath=bad_subpath),
                    ),
                ],
                held_permissions=AsyncMock(),
            )


class TestPrepareVFolderMountsSubpathFlow:
    """End-to-end test of subpath plumbing — a request carrying ``subpath``
    must surface as ``VFolderMount.vfsubpath`` (and join correctly into
    ``host_path``) on the resolved mount."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
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
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def fixture_vfolder(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[tuple[UUID, str, UUID, UUID], None]:
        """Provision the minimum row chain (domain → policies → user → group → vfolder)
        with a host name whose volume part matches ``NOOP_STORAGE_VOLUME_NAME``
        so ``ensure_host_permission_allowed`` short-circuits.

        Yields ``(user_uuid, domain_name, group_id, vfolder_id)``.
        """
        domain_id = DomainID(uuid.uuid4())
        domain_name = f"test-domain-{uuid4().hex[:8]}"
        user_policy_name = f"test-user-pol-{uuid4().hex[:8]}"
        project_policy_name = f"test-proj-pol-{uuid4().hex[:8]}"
        user_uuid = uuid4()
        group_id = uuid4()
        personal_project_id = uuid4()
        vfolder_id = uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                DomainRow(
                    id=domain_id,
                    name=domain_name,
                    description="",
                    is_active=True,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={"proxy:noop": ["mount-in-session"]},
                    allowed_docker_registries=[],
                )
            )
            db_sess.add(
                UserResourcePolicyRow(
                    name=user_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=int(BinarySize.from_str("10GiB")),
                    max_session_count_per_model_session=5,
                    max_customized_image_count=3,
                )
            )
            db_sess.add(
                ProjectResourcePolicyRow(
                    name=project_policy_name,
                    max_vfolder_count=10,
                    max_quota_scope_size=int(BinarySize.from_str("100GiB")),
                    max_network_count=5,
                )
            )
            await db_sess.flush()
            db_sess.add(
                UserRow(
                    uuid=user_uuid,
                    username=f"u-{user_uuid.hex[:6]}",
                    email=f"{user_uuid.hex[:6]}@example.com",
                    password=_password_info(),
                    need_password_change=False,
                    full_name="Test User",
                    domain_name=domain_name,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                    status_info="active",
                    resource_policy=user_policy_name,
                    domain_id=domain_id,
                )
            )
            db_sess.add(
                ProjectRow(
                    id=group_id,
                    name=f"g-{group_id.hex[:6]}",
                    description="",
                    is_active=True,
                    domain_name=domain_name,
                    resource_policy=project_policy_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={"proxy:noop": ["mount-in-session"]},
                )
            )
            await db_sess.flush()
            db_sess.add(
                VFolderRow(
                    id=vfolder_id,
                    host="proxy:noop",
                    domain_name=domain_name,
                    quota_scope_id=QuotaScopeID.parse(
                        f"user:{user_uuid}",
                    ),
                    name=f"vf-{vfolder_id.hex[:6]}",
                    creator=f"{user_uuid.hex[:6]}@example.com",
                    user=user_uuid,
                )
            )
            db_sess.add(
                ProjectRow(
                    id=personal_project_id,
                    name=f"personal-{personal_project_id.hex[:6]}",
                    description="",
                    is_active=True,
                    domain_name=domain_name,
                    resource_policy=project_policy_name,
                    total_resource_slots=ResourceSlot(),
                    allowed_vfolder_hosts={},
                    type=ProjectType.PERSONAL,
                    creator_id=user_uuid,
                )
            )
            await db_sess.flush()
            await VirtualEntitySeeder().create_in(
                db_sess,
                VFolderEntityType(),
                vfolder_id,
                [(ProjectEntityType(), personal_project_id)],
            )

        yield user_uuid, domain_name, group_id, vfolder_id

    @pytest.fixture
    def mock_storage_manager(self) -> MagicMock:
        """``get_proxy_and_volume`` returns a dummy pair; the manager-facing
        client returns a deterministic mount base path. The host path that
        ``prepare_vfolder_mounts`` constructs joins this base with the
        subpath, so we can assert subpath wiring through ``host_path`` too.
        """
        client = MagicMock()
        client.get_mount_path = AsyncMock(return_value={"path": "/data/mount-base"})
        client.mkdir = AsyncMock()
        sm = MagicMock()
        sm.get_proxy_and_volume = MagicMock(return_value=("proxy", "volume"))
        sm.get_manager_facing_client = MagicMock(return_value=client)
        return sm

    async def test_subpath_propagates_to_vfsubpath_and_host_path(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fixture_vfolder: tuple[UUID, str, UUID, UUID],
        mock_storage_manager: MagicMock,
    ) -> None:
        user_uuid, domain_name, group_id, vfolder_id = fixture_vfolder
        async with db_with_cleanup.connect() as conn:
            mounts = await prepare_vfolder_mounts(
                conn=conn,
                storage_manager=mock_storage_manager,
                allowed_vfolder_types=["user"],
                user_scope=UserScope(
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    user_role=UserRole.USER,
                ),
                resource_policy={
                    "allowed_vfolder_hosts": {"proxy:noop": ["mount-in-session"]},
                },
                held_permissions=_held_in_full,
                mount_requests=[
                    VFolderMountRequest(
                        ref=vfolder_id,
                        dst_path="/home/work/dataset",
                        options=VFolderMountOptions(subpath="train/v2"),
                    ),
                ],
            )

        assert len(mounts) == 1
        mount = mounts[0]
        assert mount.vfsubpath == PurePosixPath("train/v2")
        # Host path joins the storage-side base with the requested subpath.
        assert mount.host_path == PurePosixPath("/data/mount-base/train/v2")
        # And the storage proxy was asked to resolve the subpath, not "."
        client = mock_storage_manager.get_manager_facing_client.return_value
        client.get_mount_path.assert_awaited_once()
        assert client.get_mount_path.call_args.args[-1] == "train/v2"

    async def test_subpath_omitted_falls_back_to_vfolder_root(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fixture_vfolder: tuple[UUID, str, UUID, UUID],
        mock_storage_manager: MagicMock,
    ) -> None:
        """No subpath in options → ``vfsubpath == PurePosixPath('.')`` —
        the storage-proxy-facing default."""
        user_uuid, domain_name, group_id, vfolder_id = fixture_vfolder
        async with db_with_cleanup.connect() as conn:
            mounts = await prepare_vfolder_mounts(
                conn=conn,
                storage_manager=mock_storage_manager,
                allowed_vfolder_types=["user"],
                user_scope=UserScope(
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    user_role=UserRole.USER,
                ),
                resource_policy={
                    "allowed_vfolder_hosts": {"proxy:noop": ["mount-in-session"]},
                },
                held_permissions=_held_in_full,
                mount_requests=[
                    VFolderMountRequest(
                        ref=vfolder_id,
                        dst_path="/home/work/dataset",
                        options=VFolderMountOptions(),
                    ),
                ],
            )

        assert len(mounts) == 1
        assert mounts[0].vfsubpath == PurePosixPath(".")

    async def test_same_vfolder_multiple_subpaths_yield_distinct_mounts(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fixture_vfolder: tuple[UUID, str, UUID, UUID],
        mock_storage_manager: MagicMock,
    ) -> None:
        """One vfolder referenced by UUID several times — each with a distinct
        subpath and destination — must resolve to one mount per request rather
        than collapsing to a single mount (lablup/backend.ai#11936)."""
        user_uuid, domain_name, group_id, vfolder_id = fixture_vfolder
        async with db_with_cleanup.connect() as conn:
            mounts = await prepare_vfolder_mounts(
                conn=conn,
                storage_manager=mock_storage_manager,
                allowed_vfolder_types=["user"],
                user_scope=UserScope(
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    user_role=UserRole.USER,
                ),
                resource_policy={
                    "allowed_vfolder_hosts": {"proxy:noop": ["mount-in-session"]},
                },
                held_permissions=_held_in_full,
                mount_requests=[
                    VFolderMountRequest(
                        ref=vfolder_id,
                        dst_path="/home/work/in1",
                        options=VFolderMountOptions(subpath="shards/a"),
                    ),
                    VFolderMountRequest(
                        ref=vfolder_id,
                        dst_path="/home/work/in2",
                        options=VFolderMountOptions(subpath="shards/b"),
                    ),
                ],
            )

        assert len(mounts) == 2
        by_dst = {str(m.kernel_path): m for m in mounts}
        assert set(by_dst) == {"/home/work/in1", "/home/work/in2"}
        # Both mounts point at the same vfolder but at their own subpath.
        assert {m.vfid.folder_id for m in mounts} == {vfolder_id}
        assert by_dst["/home/work/in1"].vfsubpath == PurePosixPath("shards/a")
        assert by_dst["/home/work/in2"].vfsubpath == PurePosixPath("shards/b")
        assert by_dst["/home/work/in1"].host_path == PurePosixPath("/data/mount-base/shards/a")
        assert by_dst["/home/work/in2"].host_path == PurePosixPath("/data/mount-base/shards/b")

    async def test_same_vfolder_duplicate_subpath_is_deduplicated(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fixture_vfolder: tuple[UUID, str, UUID, UUID],
        mock_storage_manager: MagicMock,
    ) -> None:
        """Two requests for the identical ``(vfolder, subpath)`` collapse to a
        single mount — ``is_mount_duplicate`` still guards overlapping sources
        even though the per-request keys are distinct."""
        user_uuid, domain_name, group_id, vfolder_id = fixture_vfolder
        async with db_with_cleanup.connect() as conn:
            mounts = await prepare_vfolder_mounts(
                conn=conn,
                storage_manager=mock_storage_manager,
                allowed_vfolder_types=["user"],
                user_scope=UserScope(
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    user_role=UserRole.USER,
                ),
                resource_policy={
                    "allowed_vfolder_hosts": {"proxy:noop": ["mount-in-session"]},
                },
                held_permissions=_held_in_full,
                mount_requests=[
                    VFolderMountRequest(
                        ref=vfolder_id,
                        dst_path="/home/work/in1",
                        options=VFolderMountOptions(subpath="shards/a"),
                    ),
                    VFolderMountRequest(
                        ref=vfolder_id,
                        dst_path="/home/work/in2",
                        options=VFolderMountOptions(subpath="shards/a"),
                    ),
                ],
            )

        assert len(mounts) == 1
        assert mounts[0].vfsubpath == PurePosixPath("shards/a")

    @pytest.fixture
    async def same_named_vfolders(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fixture_vfolder: tuple[UUID, str, UUID, UUID],
        case: _SameNamedVFoldersCase,
    ) -> _SameNamedVFolders:
        user_uuid, domain_name, session_project_id, personal_vfolder_id = fixture_vfolder
        project_vfolder_id = uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(
                sa.update(VFolderRow)
                .where(VFolderRow.id == personal_vfolder_id)
                .values(name=case.vfolder_name)
            )
            db_sess.add(
                VFolderRow(
                    id=project_vfolder_id,
                    host="proxy:noop",
                    domain_name=domain_name,
                    quota_scope_id=QuotaScopeID.parse(f"project:{session_project_id}"),
                    name=case.vfolder_name,
                    ownership_type=VFolderOwnershipType.GROUP,
                    user=None,
                    group=session_project_id,
                    default_mount_permission=VFolderMountPolicy.READ_WRITE,
                )
            )
            await db_sess.flush()
            seeder = VirtualEntitySeeder()
            await seeder.enroll_user_in_project(db_sess, session_project_id, user_uuid)
            await seeder.create_in(
                db_sess,
                VFolderEntityType(),
                project_vfolder_id,
                [(ProjectEntityType(), session_project_id)],
            )
        return _SameNamedVFolders(
            user_scope=UserScope(
                domain_name=domain_name,
                group_id=session_project_id,
                user_uuid=user_uuid,
                user_role=UserRole.USER,
            ),
            vfolder_ids={
                _VFolderOwner.USER: personal_vfolder_id,
                _VFolderOwner.SESSION_PROJECT: project_vfolder_id,
            },
        )

    @pytest.mark.parametrize(
        "case",
        [
            _SameNamedVFoldersCase(
                name="both-requested",
                vfolder_name="data",
                requested_mounts=[
                    _MountOfOwner(_VFolderOwner.USER, "/home/work/in1"),
                    _MountOfOwner(_VFolderOwner.SESSION_PROJECT, "/home/work/in2"),
                ],
                expected_mounts=[
                    _MountOfOwner(_VFolderOwner.USER, "/home/work/in1"),
                    _MountOfOwner(_VFolderOwner.SESSION_PROJECT, "/home/work/in2"),
                ],
            ),
            _SameNamedVFoldersCase(
                name="neither-requested",
                vfolder_name=".local",
                requested_mounts=[],
                expected_mounts=[_MountOfOwner(_VFolderOwner.SESSION_PROJECT, "/home/work/.local")],
            ),
            _SameNamedVFoldersCase(
                name="requested-where-the-other-is-auto-mounted",
                vfolder_name=".local",
                requested_mounts=[_MountOfOwner(_VFolderOwner.USER, None)],
                expected_mounts=[_MountOfOwner(_VFolderOwner.USER, "/home/work/.local")],
            ),
            _SameNamedVFoldersCase(
                name="requested-away-from-where-the-other-is-auto-mounted",
                vfolder_name=".local",
                requested_mounts=[_MountOfOwner(_VFolderOwner.USER, "/home/work/in1")],
                expected_mounts=[
                    _MountOfOwner(_VFolderOwner.USER, "/home/work/in1"),
                    _MountOfOwner(_VFolderOwner.SESSION_PROJECT, "/home/work/.local"),
                ],
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_a_request_mounts_the_vfolder_of_its_own_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        mock_storage_manager: MagicMock,
        same_named_vfolders: _SameNamedVFolders,
        case: _SameNamedVFoldersCase,
    ) -> None:
        async with db_with_cleanup.connect() as conn:
            mounts = await prepare_vfolder_mounts(
                conn=conn,
                storage_manager=mock_storage_manager,
                allowed_vfolder_types=["user", "group"],
                user_scope=same_named_vfolders.user_scope,
                resource_policy={
                    "allowed_vfolder_hosts": {"proxy:noop": ["mount-in-session"]},
                },
                held_permissions=_held_in_full,
                mount_requests=[
                    VFolderMountRequest(
                        ref=same_named_vfolders.vfolder_ids[requested.owner],
                        dst_path=requested.mount_destination,
                    )
                    for requested in case.requested_mounts
                ],
            )

        assert {str(mount.kernel_path): mount.vfid.folder_id for mount in mounts} == {
            expected.mount_destination: same_named_vfolders.vfolder_ids[expected.owner]
            for expected in case.expected_mounts
        }
        assert len(mounts) == len(case.expected_mounts)

    async def test_inaccessible_uuid_request_raises_not_found(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fixture_vfolder: tuple[UUID, str, UUID, UUID],
        mock_storage_manager: MagicMock,
    ) -> None:
        """A UUID-referenced request that matches no accessible vfolder must
        raise ``VFolderNotFound`` rather than being silently dropped — even
        when it is bundled with a resolvable request for another subpath of an
        accessible vfolder (lablup/backend.ai#11936)."""
        user_uuid, domain_name, group_id, vfolder_id = fixture_vfolder
        missing_vfolder_id = uuid4()
        with pytest.raises(VFolderNotFound, match=str(missing_vfolder_id)):
            async with db_with_cleanup.connect() as conn:
                await prepare_vfolder_mounts(
                    conn=conn,
                    storage_manager=mock_storage_manager,
                    allowed_vfolder_types=["user"],
                    user_scope=UserScope(
                        domain_name=domain_name,
                        group_id=group_id,
                        user_uuid=user_uuid,
                        user_role=UserRole.USER,
                    ),
                    resource_policy={
                        "allowed_vfolder_hosts": {"proxy:noop": ["mount-in-session"]},
                    },
                    held_permissions=_held_in_full,
                    mount_requests=[
                        VFolderMountRequest(
                            ref=vfolder_id,
                            dst_path="/home/work/in1",
                            options=VFolderMountOptions(subpath="shards/a"),
                        ),
                        VFolderMountRequest(
                            ref=missing_vfolder_id,
                            dst_path="/home/work/in2",
                            options=VFolderMountOptions(subpath="shards/b"),
                        ),
                    ],
                )

    @pytest.fixture
    async def unmanaged_vfolder_of_user(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fixture_vfolder: tuple[UUID, str, UUID, UUID],
    ) -> _UnmanagedVFolderOfUser:
        user_uuid, domain_name, group_id, vfolder_id = fixture_vfolder
        async with db_with_cleanup.begin_session() as db_sess:
            await db_sess.execute(
                sa.update(VFolderRow)
                .where(VFolderRow.id == vfolder_id)
                .values(unmanaged_path="/mnt/unmanaged/data")
            )
        return _UnmanagedVFolderOfUser(
            user_scope=UserScope(
                domain_name=domain_name,
                group_id=group_id,
                user_uuid=user_uuid,
                user_role=UserRole.USER,
            ),
            vfolder_id=vfolder_id,
        )

    @pytest.mark.parametrize(
        "case",
        [
            _UnmanagedMountPathCase(
                requested_mount_path="data",
                expected_kernel_path=PurePosixPath("/home/work/data"),
            ),
            _UnmanagedMountPathCase(
                requested_mount_path="/opt/data",
                expected_kernel_path=PurePosixPath("/opt/data"),
            ),
        ],
        ids=lambda case: case.requested_mount_path,
    )
    async def test_an_unmanaged_vfolder_mounts_at_the_requested_path(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        mock_storage_manager: MagicMock,
        unmanaged_vfolder_of_user: _UnmanagedVFolderOfUser,
        case: _UnmanagedMountPathCase,
    ) -> None:
        async with db_with_cleanup.connect() as conn:
            mounts = await prepare_vfolder_mounts(
                conn=conn,
                storage_manager=mock_storage_manager,
                allowed_vfolder_types=["user"],
                user_scope=unmanaged_vfolder_of_user.user_scope,
                resource_policy={
                    "allowed_vfolder_hosts": {"proxy:noop": ["mount-in-session"]},
                },
                held_permissions=_held_in_full,
                mount_requests=[
                    VFolderMountRequest(
                        ref=unmanaged_vfolder_of_user.vfolder_id,
                        dst_path=case.requested_mount_path,
                    ),
                ],
            )

        assert [mount.kernel_path for mount in mounts] == [case.expected_kernel_path]


class TestPrepareVFolderMountsPolicy(TestPrepareVFolderMountsSubpathFlow):
    """The level a folder mounts at comes from its mount policy: the folder's default,
    or the user's own row over it. Access itself is held in full here."""

    @pytest.fixture
    async def project_vfolder(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fixture_vfolder: tuple[UUID, str, UUID, UUID],
    ) -> tuple[UUID, UUID]:
        """A read-only project folder the user reaches as a member; yields
        ``(user_uuid, vfolder_id)``."""
        user_uuid, domain_name, group_id, _ = fixture_vfolder
        vfolder_id = uuid4()
        async with db_with_cleanup.begin_session() as db_sess:
            db_sess.add(
                VFolderRow(
                    id=vfolder_id,
                    host="proxy:noop",
                    domain_name=domain_name,
                    quota_scope_id=QuotaScopeID.parse(f"project:{group_id}"),
                    name=f"shared-{vfolder_id.hex[:6]}",
                    ownership_type=VFolderOwnershipType.GROUP,
                    user=None,
                    group=group_id,
                    default_mount_permission=VFolderMountPolicy.READ_ONLY,
                )
            )
            await db_sess.flush()
            seeder = VirtualEntitySeeder()
            await seeder.enroll_user_in_project(db_sess, group_id, user_uuid)
            await seeder.create_in(
                db_sess, VFolderEntityType(), vfolder_id, [(ProjectEntityType(), group_id)]
            )
        return user_uuid, vfolder_id

    async def _set_policy(
        self,
        db: ExtendedAsyncSAEngine,
        vfolder_id: UUID,
        user_id: UUID,
        level: VFolderMountPolicy,
    ) -> None:
        async with db.begin_session() as db_sess:
            db_sess.add(
                VFolderUserMountPolicyRow(vfolder_id=vfolder_id, user_id=user_id, permission=level)
            )

    async def _mount(
        self,
        db: ExtendedAsyncSAEngine,
        storage_manager: MagicMock,
        fixture_vfolder: tuple[UUID, str, UUID, UUID],
        vfolder_id: UUID,
        requested: MountPermission | None,
    ) -> Sequence[VFolderMount]:
        user_uuid, domain_name, group_id, _ = fixture_vfolder
        async with db.connect() as conn:
            return await prepare_vfolder_mounts(
                conn=conn,
                storage_manager=storage_manager,
                allowed_vfolder_types=["user", "group"],
                user_scope=UserScope(
                    domain_name=domain_name,
                    group_id=group_id,
                    user_uuid=user_uuid,
                    user_role=UserRole.USER,
                ),
                resource_policy={
                    "allowed_vfolder_hosts": {"proxy:noop": ["mount-in-session"]},
                },
                held_permissions=_held_in_full,
                mount_requests=[
                    VFolderMountRequest(
                        ref=vfolder_id,
                        dst_path=None,
                        options=VFolderMountOptions(permission=requested),
                    ),
                ],
            )

    async def test_the_default_answers_without_a_row(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fixture_vfolder: tuple[UUID, str, UUID, UUID],
        project_vfolder: tuple[UUID, UUID],
        mock_storage_manager: MagicMock,
    ) -> None:
        _, vfolder_id = project_vfolder

        mounts = await self._mount(
            db_with_cleanup, mock_storage_manager, fixture_vfolder, vfolder_id, None
        )

        assert [m.mount_perm for m in mounts if m.vfid.folder_id == vfolder_id] == [
            MountPermission.READ_ONLY
        ]

    async def test_a_request_wider_than_the_level_is_refused(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fixture_vfolder: tuple[UUID, str, UUID, UUID],
        project_vfolder: tuple[UUID, UUID],
        mock_storage_manager: MagicMock,
    ) -> None:
        _, vfolder_id = project_vfolder

        with pytest.raises(VFolderPermissionError):
            await self._mount(
                db_with_cleanup,
                mock_storage_manager,
                fixture_vfolder,
                vfolder_id,
                MountPermission.READ_WRITE,
            )

    async def test_the_users_row_raises_the_level(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fixture_vfolder: tuple[UUID, str, UUID, UUID],
        project_vfolder: tuple[UUID, UUID],
        mock_storage_manager: MagicMock,
    ) -> None:
        user_uuid, vfolder_id = project_vfolder
        await self._set_policy(
            db_with_cleanup, vfolder_id, user_uuid, VFolderMountPolicy.READ_WRITE
        )

        mounts = await self._mount(
            db_with_cleanup,
            mock_storage_manager,
            fixture_vfolder,
            vfolder_id,
            MountPermission.READ_WRITE,
        )

        assert [m.mount_perm for m in mounts if m.vfid.folder_id == vfolder_id] == [
            MountPermission.READ_WRITE
        ]

    async def test_a_folder_that_mounts_to_nobody_is_refused(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        fixture_vfolder: tuple[UUID, str, UUID, UUID],
        project_vfolder: tuple[UUID, UUID],
        mock_storage_manager: MagicMock,
    ) -> None:
        user_uuid, vfolder_id = project_vfolder
        await self._set_policy(db_with_cleanup, vfolder_id, user_uuid, VFolderMountPolicy.NONE)

        with pytest.raises(VFolderPermissionError):
            await self._mount(
                db_with_cleanup, mock_storage_manager, fixture_vfolder, vfolder_id, None
            )
