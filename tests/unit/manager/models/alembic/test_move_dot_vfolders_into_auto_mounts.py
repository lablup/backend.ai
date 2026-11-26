"""Runs the move of dot-prefixed vfolders against a real database and reads the auto-mounts
back with their graph rows."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from sqlalchemy import Table
from sqlalchemy.orm import aliased

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.data.entity.vfolder_auto_mount import (
    VFolderAutoMountEntityType,
    VFolderAutoMountID,
)
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.vfolder_auto_mount.types import VFolderAutoMountScopeType
from ai.backend.common.types import QuotaScopeID, QuotaScopeType
from ai.backend.manager.data.vfolder.types import (
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.models.alembic.versions import (
    ae624fa26235_move_dot_vfolders_into_auto_mounts as revision,
)
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_policy.row import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.db import HasTable, with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder

_TABLES: list[Table | type[HasTable]] = [
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
]


@dataclass(frozen=True, kw_only=True)
class _VFolderCase:
    name: str = ".cache"
    ownership_type: VFolderOwnershipType = VFolderOwnershipType.USER
    status: VFolderOperationStatus = VFolderOperationStatus.READY
    scope_in_graph: bool = True


@dataclass(frozen=True, kw_only=True)
class _MovedVFolderCase(_VFolderCase):
    expected_scope_type: VFolderAutoMountScopeType
    expected_mount_destination: str


@dataclass(frozen=True, kw_only=True)
class _VFolderStatusCase(_VFolderCase):
    expected_moved: bool


@dataclass(frozen=True)
class _RegisteredAutoMountCase:
    vfolder_name: str
    mount_destination: str


@dataclass(frozen=True)
class _VFolderWithScopes:
    vfolder_id: VFolderUUID
    scope_ids: Mapping[VFolderAutoMountScopeType, uuid.UUID]


@dataclass(frozen=True)
class _OwnEdge:
    owner_type: str
    owner_id: uuid.UUID
    capped: bool


@dataclass(frozen=True)
class _GovernEdge:
    scope_type: str
    scope_id: uuid.UUID
    permission_cap: Permission | None


@dataclass(frozen=True)
class _StoredAutoMount:
    id: VFolderAutoMountID
    scope_type: VFolderAutoMountScopeType
    scope_id: uuid.UUID
    vfolder_id: VFolderUUID
    mount_destination: str
    subpath: str
    mount_permission: VFolderMountPermission
    own_edges: frozenset[_OwnEdge]
    govern_edges: frozenset[_GovernEdge]


@dataclass(frozen=True)
class _StoredAutoMountsAndNodes:
    auto_mounts: frozenset[_StoredAutoMount]
    node_entity_ids: frozenset[uuid.UUID]


def _vfolder_row(
    vfolder_id: VFolderUUID,
    name: str,
    user_id: UserID,
    project_id: ProjectID | None,
    ownership_type: VFolderOwnershipType = VFolderOwnershipType.USER,
    status: VFolderOperationStatus = VFolderOperationStatus.READY,
) -> VFolderRow:
    return VFolderRow(
        id=vfolder_id,
        name=name,
        host="local",
        domain_name="default",
        quota_scope_id=QuotaScopeID(QuotaScopeType.USER, user_id),
        ownership_type=ownership_type,
        user=user_id,
        group=project_id,
        status=status,
    )


async def _stored_auto_mounts_and_nodes(db: ExtendedAsyncSAEngine) -> _StoredAutoMountsAndNodes:
    auto_mount_node = aliased(VirtualEntityRow)
    owner_node = aliased(VirtualEntityRow)
    async with db.begin_readonly_session() as session:
        auto_mounts = (await session.scalars(sa.select(VFolderAutoMountRow))).all()
        node_entity_ids = (
            await session.scalars(
                sa.select(VirtualEntityRow.entity_id).where(
                    VirtualEntityRow.entity_type == VFolderAutoMountEntityType()
                )
            )
        ).all()
        own_edges = (
            await session.execute(
                sa.select(
                    auto_mount_node.entity_id.label("auto_mount_id"),
                    owner_node.entity_type.label("owner_type"),
                    owner_node.entity_id.label("owner_id"),
                    EntityMembershipRow.capped,
                )
                .select_from(EntityMembershipRow)
                .join(auto_mount_node, auto_mount_node.id == EntityMembershipRow.member_entity_id)
                .join(owner_node, owner_node.id == EntityMembershipRow.virtual_entity_id)
            )
        ).all()
        govern_edges = (
            await session.execute(
                sa.select(
                    auto_mount_node.entity_id.label("auto_mount_id"),
                    owner_node.entity_type.label("scope_type"),
                    owner_node.entity_id.label("scope_id"),
                    ScopeBindingRow.permission_cap,
                )
                .select_from(ScopeBindingRow)
                .join(auto_mount_node, auto_mount_node.id == ScopeBindingRow.virtual_entity_id)
                .join(owner_node, owner_node.id == ScopeBindingRow.scope_entity_id)
            )
        ).all()
    return _StoredAutoMountsAndNodes(
        auto_mounts=frozenset(
            _StoredAutoMount(
                id=auto_mount.id,
                scope_type=auto_mount.scope_type,
                scope_id=auto_mount.scope_id,
                vfolder_id=auto_mount.vfolder_id,
                mount_destination=auto_mount.mount_destination,
                subpath=auto_mount.subpath,
                mount_permission=auto_mount.mount_permission,
                own_edges=frozenset(
                    _OwnEdge(edge.owner_type, edge.owner_id, edge.capped)
                    for edge in own_edges
                    if edge.auto_mount_id == auto_mount.id
                ),
                govern_edges=frozenset(
                    _GovernEdge(edge.scope_type, edge.scope_id, edge.permission_cap)
                    for edge in govern_edges
                    if edge.auto_mount_id == auto_mount.id
                ),
            )
            for auto_mount in auto_mounts
        ),
        node_entity_ids=frozenset(node_entity_ids),
    )


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncIterator[ExtendedAsyncSAEngine]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


@pytest.fixture
async def vfolder_with_scopes(db: ExtendedAsyncSAEngine, case: _VFolderCase) -> _VFolderWithScopes:
    vfolder_id = VFolderUUID(uuid.uuid4())
    user_id = UserID(uuid.uuid4())
    project_id = ProjectID(uuid.uuid4())
    scope_ids: dict[VFolderAutoMountScopeType, uuid.UUID] = {
        VFolderAutoMountScopeType.USER: user_id,
        VFolderAutoMountScopeType.PROJECT: project_id,
    }
    async with db.begin_session() as session:
        session.add(
            _vfolder_row(
                vfolder_id, case.name, user_id, project_id, case.ownership_type, case.status
            )
        )
        if case.scope_in_graph:
            session.add_all([
                VirtualEntityRow(entity_type=EntityType(scope_type), entity_id=scope_id)
                for scope_type, scope_id in scope_ids.items()
            ])
    return _VFolderWithScopes(vfolder_id=vfolder_id, scope_ids=scope_ids)


@pytest.fixture
async def dot_vfolder_conflicting_with_a_registered_auto_mount(
    db: ExtendedAsyncSAEngine, case: _RegisteredAutoMountCase
) -> None:
    user_id = UserID(uuid.uuid4())
    vfolder_ids = {name: VFolderUUID(uuid.uuid4()) for name in (".cache", "data")}
    async with db.begin_session() as session:
        session.add(VirtualEntityRow(entity_type=EntityType("user"), entity_id=user_id))
        session.add_all([
            _vfolder_row(vfolder_id, name, user_id, project_id=None)
            for name, vfolder_id in vfolder_ids.items()
        ])
        await session.flush()
        registered_auto_mount = VFolderAutoMountRow(
            scope_type=VFolderAutoMountScopeType.USER,
            scope_id=user_id,
            vfolder_id=vfolder_ids[case.vfolder_name],
            mount_destination=case.mount_destination,
            subpath="sub",
            mount_permission=VFolderMountPermission.READ_ONLY,
        )
        session.add(registered_auto_mount)
        await session.flush()
        await VirtualEntitySeeder().create_in(
            session,
            VFolderAutoMountEntityType(),
            registered_auto_mount.id,
            [(UserEntityType(), user_id)],
        )


@pytest.fixture
async def dot_vfolder_and_a_registered_auto_mount(db: ExtendedAsyncSAEngine) -> None:
    user_id = UserID(uuid.uuid4())
    registered_vfolder_id = VFolderUUID(uuid.uuid4())
    async with db.begin_session() as session:
        session.add(VirtualEntityRow(entity_type=EntityType("user"), entity_id=user_id))
        session.add_all([
            _vfolder_row(VFolderUUID(uuid.uuid4()), ".cache", user_id, project_id=None),
            _vfolder_row(registered_vfolder_id, "data", user_id, project_id=None),
        ])
        await session.flush()
        registered_auto_mount = VFolderAutoMountRow(
            scope_type=VFolderAutoMountScopeType.USER,
            scope_id=user_id,
            vfolder_id=registered_vfolder_id,
            mount_destination="/home/work/data",
            subpath=".",
            mount_permission=VFolderMountPermission.READ_WRITE,
        )
        session.add(registered_auto_mount)
        await session.flush()
        await VirtualEntitySeeder().create_in(
            session,
            VFolderAutoMountEntityType(),
            registered_auto_mount.id,
            [(UserEntityType(), user_id)],
        )


class TestMoveDotVFolders:
    @pytest.mark.parametrize(
        "case",
        [
            _MovedVFolderCase(
                ownership_type=VFolderOwnershipType.USER,
                expected_scope_type=VFolderAutoMountScopeType.USER,
                expected_mount_destination="/home/work/.cache",
            ),
            _MovedVFolderCase(
                ownership_type=VFolderOwnershipType.GROUP,
                expected_scope_type=VFolderAutoMountScopeType.PROJECT,
                expected_mount_destination="/home/work/.cache",
            ),
            _MovedVFolderCase(
                name=".local",
                ownership_type=VFolderOwnershipType.USER,
                expected_scope_type=VFolderAutoMountScopeType.USER,
                expected_mount_destination="/home/work/.local",
            ),
        ],
        ids=lambda case: f"{case.ownership_type.value}{case.name}",
    )
    async def test_a_dot_vfolder_becomes_an_auto_mount_its_scope_owns_and_governs(
        self,
        db: ExtendedAsyncSAEngine,
        vfolder_with_scopes: _VFolderWithScopes,
        case: _MovedVFolderCase,
    ) -> None:
        async with db.begin() as conn:
            await conn.run_sync(revision.move_dot_vfolders)

        [auto_mount] = (await _stored_auto_mounts_and_nodes(db)).auto_mounts
        scope_id = vfolder_with_scopes.scope_ids[case.expected_scope_type]
        assert auto_mount == _StoredAutoMount(
            id=auto_mount.id,
            scope_type=case.expected_scope_type,
            scope_id=scope_id,
            vfolder_id=vfolder_with_scopes.vfolder_id,
            mount_destination=case.expected_mount_destination,
            subpath=".",
            mount_permission=VFolderMountPermission.READ_WRITE,
            own_edges=frozenset({
                _OwnEdge("vfolder_auto_mount", auto_mount.id, capped=False),
                _OwnEdge(case.expected_scope_type.value, scope_id, capped=False),
            }),
            govern_edges=frozenset({
                _GovernEdge("vfolder_auto_mount", auto_mount.id, permission_cap=None),
                _GovernEdge(case.expected_scope_type.value, scope_id, permission_cap=None),
            }),
        )

    @pytest.mark.parametrize(
        "case",
        [
            _VFolderStatusCase(status=VFolderOperationStatus.READY, expected_moved=True),
            _VFolderStatusCase(status=VFolderOperationStatus.CREATING, expected_moved=True),
            _VFolderStatusCase(status=VFolderOperationStatus.PERFORMING, expected_moved=True),
            _VFolderStatusCase(status=VFolderOperationStatus.CLONING, expected_moved=True),
            _VFolderStatusCase(status=VFolderOperationStatus.MOUNTED, expected_moved=True),
            _VFolderStatusCase(status=VFolderOperationStatus.ERROR, expected_moved=True),
            _VFolderStatusCase(status=VFolderOperationStatus.DELETE_PENDING, expected_moved=False),
            _VFolderStatusCase(status=VFolderOperationStatus.DELETE_ONGOING, expected_moved=False),
            _VFolderStatusCase(status=VFolderOperationStatus.DELETE_COMPLETE, expected_moved=False),
            _VFolderStatusCase(status=VFolderOperationStatus.DELETE_ERROR, expected_moved=False),
        ],
        ids=lambda case: case.status.value,
    )
    @pytest.mark.usefixtures("vfolder_with_scopes")
    async def test_a_vfolder_in_the_trash_or_past_it_is_not_moved(
        self, db: ExtendedAsyncSAEngine, case: _VFolderStatusCase
    ) -> None:
        async with db.begin() as conn:
            await conn.run_sync(revision.move_dot_vfolders)

        assert bool((await _stored_auto_mounts_and_nodes(db)).auto_mounts) is case.expected_moved

    @pytest.mark.parametrize(
        "case",
        [
            _VFolderCase(name="cache"),
            _VFolderCase(name=".local", ownership_type=VFolderOwnershipType.GROUP),
            _VFolderCase(scope_in_graph=False),
        ],
        ids=["no_dot", "project_local", "scope_without_node"],
    )
    @pytest.mark.usefixtures("vfolder_with_scopes")
    async def test_a_vfolder_that_is_not_moved_leaves_no_row_and_no_node(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        async with db.begin() as conn:
            await conn.run_sync(revision.move_dot_vfolders)

        assert await _stored_auto_mounts_and_nodes(db) == _StoredAutoMountsAndNodes(
            auto_mounts=frozenset(), node_entity_ids=frozenset()
        )

    @pytest.mark.parametrize(
        "case",
        [
            _RegisteredAutoMountCase(vfolder_name=".cache", mount_destination="/mnt/cache"),
            _RegisteredAutoMountCase(vfolder_name="data", mount_destination="/home/work/.cache"),
        ],
        ids=["same_vfolder", "same_mount_destination"],
    )
    @pytest.mark.usefixtures("dot_vfolder_conflicting_with_a_registered_auto_mount")
    async def test_a_registered_auto_mount_is_left_alone(self, db: ExtendedAsyncSAEngine) -> None:
        before_move = await _stored_auto_mounts_and_nodes(db)

        async with db.begin() as conn:
            await conn.run_sync(revision.move_dot_vfolders)

        assert await _stored_auto_mounts_and_nodes(db) == before_move

    @pytest.mark.usefixtures("dot_vfolder_and_a_registered_auto_mount")
    async def test_moving_again_changes_nothing(self, db: ExtendedAsyncSAEngine) -> None:
        async with db.begin() as conn:
            await conn.run_sync(revision.move_dot_vfolders)
        after_first_move = await _stored_auto_mounts_and_nodes(db)

        async with db.begin() as conn:
            await conn.run_sync(revision.move_dot_vfolders)

        assert await _stored_auto_mounts_and_nodes(db) == after_first_move


class TestRemoveMovedAutoMounts:
    @pytest.mark.usefixtures("dot_vfolder_and_a_registered_auto_mount")
    async def test_only_the_moved_auto_mounts_and_their_nodes_are_removed(
        self, db: ExtendedAsyncSAEngine
    ) -> None:
        before_move = await _stored_auto_mounts_and_nodes(db)
        async with db.begin() as conn:
            await conn.run_sync(revision.move_dot_vfolders)

        async with db.begin() as conn:
            await conn.run_sync(revision.remove_moved_auto_mounts)

        assert await _stored_auto_mounts_and_nodes(db) == before_move
