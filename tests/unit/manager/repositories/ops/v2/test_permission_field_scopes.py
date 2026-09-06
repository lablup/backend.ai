"""Role permission writes with field scopes, against a real database.

What these tests pin down:

- A READ/UPDATE grant is one of three states per operation: the row on every
  field, the row on path rows only, or nothing. Stating a bit both ways is refused,
  as is a malformed path or a bit outside READ|UPDATE.
- ``set`` states a key; ``widen`` only adds, and a bit on every field drops the
  paths it makes redundant; ``revoke`` removes an operation with its paths, or a
  path with its descendants, and never touches membership edges.
- The read composes the rows back into one entry per key, and the entry judges
  a path by prefix — a deeper UPDATE under a wider READ stays distinct.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import override
from uuid import UUID

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.permission.id import FieldPath
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import RoleSource
from ai.backend.manager.errors.permission import InvalidFieldPermission
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_field import PermissionFieldRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.specs.permission import (
    PermissionEntry,
    PermissionKey,
    PermissionRevocation,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.testutils.db import with_tables

_SCOPE_TYPE = EntityType("project")
_ENTITY_TYPE = EntityType("vfolder")

_NAME = FieldPath("name")
_DATA = FieldPath("data")
_DATA_SIZE = FieldPath("data.size")
_READ = Permission.READ
_UPDATE = Permission.UPDATE


class _ScopeID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return _SCOPE_TYPE


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        database_connection,
        [RoleRow, PermissionRow, PermissionFieldRow, VirtualEntityRow, EntityMembershipRow],
    ):
        yield database_connection


@pytest.fixture
def provider(database: ExtendedAsyncSAEngine) -> PermissionOpsProvider:
    return PermissionOpsProvider(database)


@pytest.fixture
async def role_id(database: ExtendedAsyncSAEngine) -> RoleID:
    async with database.begin_session() as sess:
        row = RoleRow(name="field-scope-role", source=RoleSource.SYSTEM, status=RoleStatus.ACTIVE)
        sess.add(row)
        await sess.flush()
        return RoleID(row.id)


@pytest.fixture
def scope() -> _ScopeID:
    return _ScopeID(uuid.uuid4())


def _entry(
    scope: _ScopeID, permission: Permission, fields: dict[FieldPath, Permission] | None = None
) -> PermissionEntry:
    return PermissionEntry(
        scope=scope, entity_type=_ENTITY_TYPE, permission=permission, fields=fields or {}
    )


def _revocation(
    scope: _ScopeID,
    permission: Permission = Permission.NONE,
    fields: dict[FieldPath, Permission] | None = None,
) -> PermissionRevocation:
    return PermissionRevocation(
        scope=scope, entity_type=_ENTITY_TYPE, permission=permission, fields=fields or {}
    )


async def _rows(
    database: ExtendedAsyncSAEngine, role_id: RoleID
) -> dict[Permission, tuple[bool, set[FieldPath]]]:
    """Per bit: whether the row covers every field, and its scoped paths."""
    async with database.begin_readonly_session() as sess:
        rows = (
            await sess.execute(
                sa.select(
                    PermissionRow.permission, PermissionRow.all_fields, PermissionFieldRow.path
                )
                .select_from(PermissionRow)
                .outerjoin(PermissionFieldRow, PermissionFieldRow.permission_id == PermissionRow.id)
                .where(PermissionRow.role_id == role_id)
            )
        ).all()
    state: dict[Permission, tuple[bool, set[FieldPath]]] = {}
    for row in rows:
        _, paths = state.setdefault(Permission(row.permission), (row.all_fields, set()))
        if row.path is not None:
            paths.add(row.path)
    return state


async def _entry_of(
    provider: PermissionOpsProvider, role_id: RoleID, scope: _ScopeID
) -> PermissionEntry | None:
    key = PermissionKey(scope=scope, entity_type=_ENTITY_TYPE)
    async with provider.read_ops() as ops:
        return (await ops.permissions(role_id, [key])).get(key)


# =============================================================================
# Validation
# =============================================================================


async def test_rejects_bit_stated_both_ways(
    provider: PermissionOpsProvider, role_id: RoleID, scope: _ScopeID
) -> None:
    async with provider.write_ops() as ops:
        with pytest.raises(InvalidFieldPermission):
            await ops.set_permissions(role_id, [_entry(scope, _READ, {_DATA: _READ})])


async def test_rejects_bits_outside_read_update(
    provider: PermissionOpsProvider, role_id: RoleID, scope: _ScopeID
) -> None:
    async with provider.write_ops() as ops:
        with pytest.raises(InvalidFieldPermission):
            await ops.set_permissions(
                role_id, [_entry(scope, Permission.NONE, {_DATA: Permission.CREATE})]
            )


async def test_rejects_malformed_path(
    provider: PermissionOpsProvider, role_id: RoleID, scope: _ScopeID
) -> None:
    async with provider.write_ops() as ops:
        with pytest.raises(InvalidFieldPermission):
            await ops.set_permissions(
                role_id, [_entry(scope, Permission.NONE, {FieldPath("data."): _READ})]
            )


# =============================================================================
# set / read / judgment
# =============================================================================


async def test_set_writes_the_three_states(
    database: ExtendedAsyncSAEngine,
    provider: PermissionOpsProvider,
    role_id: RoleID,
    scope: _ScopeID,
) -> None:
    async with provider.write_ops() as ops:
        await ops.set_permissions(
            role_id,
            [_entry(scope, _READ | Permission.CREATE, {_DATA: _UPDATE, _NAME: _UPDATE})],
        )
    assert await _rows(database, role_id) == {
        _READ: (True, set()),
        Permission.CREATE: (True, set()),
        _UPDATE: (False, {_DATA, _NAME}),
    }
    entry = await _entry_of(provider, role_id, scope)
    assert entry is not None
    assert entry.permission == _READ | Permission.CREATE
    assert entry.fields == {_DATA: _UPDATE, _NAME: _UPDATE}


async def test_set_replaces_previous_state(
    database: ExtendedAsyncSAEngine,
    provider: PermissionOpsProvider,
    role_id: RoleID,
    scope: _ScopeID,
) -> None:
    async with provider.write_ops() as ops:
        await ops.set_permissions(role_id, [_entry(scope, Permission.full())])
    async with provider.write_ops() as ops:
        await ops.set_permissions(role_id, [_entry(scope, Permission.NONE, {_NAME: _READ})])
    assert await _rows(database, role_id) == {_READ: (False, {_NAME})}


async def test_entry_judges_by_prefix_per_operation(scope: _ScopeID) -> None:
    entry = _entry(scope, _READ, {_DATA_SIZE: _UPDATE})
    assert entry.allows(_READ)
    assert entry.allows(_READ, _DATA)
    assert not entry.allows(_UPDATE)
    assert not entry.allows(_UPDATE, _DATA)
    assert entry.allows(_UPDATE, _DATA_SIZE)
    assert entry.allows(_UPDATE, FieldPath("data.size.unit"))
    assert not entry.allows(_UPDATE, FieldPath("data.sizes"))
    assert not _entry(scope, Permission.NONE).allows(_READ, _NAME)


async def test_read_is_absent_for_a_key_holding_nothing(
    provider: PermissionOpsProvider, role_id: RoleID, scope: _ScopeID
) -> None:
    assert await _entry_of(provider, role_id, scope) is None


# =============================================================================
# widen
# =============================================================================


async def test_widen_adds_paths_and_operations(
    database: ExtendedAsyncSAEngine,
    provider: PermissionOpsProvider,
    role_id: RoleID,
    scope: _ScopeID,
) -> None:
    async with provider.write_ops() as ops:
        await ops.set_permissions(role_id, [_entry(scope, Permission.NONE, {_DATA: _READ})])
    async with provider.write_ops() as ops:
        await ops.widen_permissions(
            role_id, [_entry(scope, Permission.CREATE, {_NAME: _READ | _UPDATE})]
        )
    assert await _rows(database, role_id) == {
        _READ: (False, {_DATA, _NAME}),
        _UPDATE: (False, {_NAME}),
        Permission.CREATE: (True, set()),
    }


async def test_widen_to_every_field_drops_redundant_paths(
    database: ExtendedAsyncSAEngine,
    provider: PermissionOpsProvider,
    role_id: RoleID,
    scope: _ScopeID,
) -> None:
    async with provider.write_ops() as ops:
        await ops.set_permissions(
            role_id, [_entry(scope, Permission.NONE, {_DATA: _READ | _UPDATE})]
        )
    async with provider.write_ops() as ops:
        await ops.widen_permissions(role_id, [_entry(scope, _READ)])
    assert await _rows(database, role_id) == {
        _READ: (True, set()),
        _UPDATE: (False, {_DATA}),
    }


async def test_widen_paths_under_every_field_change_nothing(
    database: ExtendedAsyncSAEngine,
    provider: PermissionOpsProvider,
    role_id: RoleID,
    scope: _ScopeID,
) -> None:
    async with provider.write_ops() as ops:
        await ops.set_permissions(role_id, [_entry(scope, _READ)])
    async with provider.write_ops() as ops:
        await ops.widen_permissions(role_id, [_entry(scope, Permission.NONE, {_DATA: _READ})])
    assert await _rows(database, role_id) == {_READ: (True, set())}


# =============================================================================
# revoke
# =============================================================================


async def test_revoke_operation_takes_its_paths(
    database: ExtendedAsyncSAEngine,
    provider: PermissionOpsProvider,
    role_id: RoleID,
    scope: _ScopeID,
) -> None:
    async with provider.write_ops() as ops:
        await ops.set_permissions(role_id, [_entry(scope, _UPDATE, {_DATA: _READ, _NAME: _READ})])
        await ops.revoke_permissions(role_id, [_revocation(scope, _READ)])
    assert await _rows(database, role_id) == {_UPDATE: (True, set())}


async def test_revoke_path_takes_descendants_and_empties_the_row(
    database: ExtendedAsyncSAEngine,
    provider: PermissionOpsProvider,
    role_id: RoleID,
    scope: _ScopeID,
) -> None:
    async with provider.write_ops() as ops:
        await ops.set_permissions(
            role_id,
            [_entry(scope, Permission.NONE, {_DATA: _READ, _DATA_SIZE: _READ | _UPDATE})],
        )
        await ops.revoke_permissions(role_id, [_revocation(scope, fields={_DATA: _READ})])
    assert await _rows(database, role_id) == {_UPDATE: (False, {_DATA_SIZE})}


async def test_revoke_path_under_every_field_is_a_no_op(
    database: ExtendedAsyncSAEngine,
    provider: PermissionOpsProvider,
    role_id: RoleID,
    scope: _ScopeID,
) -> None:
    async with provider.write_ops() as ops:
        await ops.set_permissions(role_id, [_entry(scope, _READ)])
        await ops.revoke_permissions(role_id, [_revocation(scope, fields={_DATA: _READ})])
    assert await _rows(database, role_id) == {_READ: (True, set())}


async def test_revoke_leaves_graph_edges(
    database: ExtendedAsyncSAEngine,
    provider: PermissionOpsProvider,
    role_id: RoleID,
    scope: _ScopeID,
) -> None:
    member = uuid.uuid4()
    async with database.begin_session() as sess:
        scope_node = VirtualEntityRow(entity_type=_SCOPE_TYPE, entity_id=UUID(str(scope)))
        member_node = VirtualEntityRow(entity_type=_ENTITY_TYPE, entity_id=member)
        sess.add_all([scope_node, member_node])
        await sess.flush()
        member_node_id = member_node.id
        sess.add(
            EntityMembershipRow(
                virtual_entity_id=scope_node.id,
                member_entity_id=member_node.id,
                capped=True,
            )
        )
    async with provider.write_ops() as ops:
        await ops.set_permissions(role_id, [_entry(scope, _READ, {_DATA: _UPDATE})])
        await ops.revoke_permissions(role_id, [_revocation(scope, _READ | _UPDATE)])
    assert await _rows(database, role_id) == {}
    async with database.begin_readonly_session() as sess:
        edges = (
            await sess.scalars(
                sa.select(EntityMembershipRow).where(
                    EntityMembershipRow.member_entity_id == member_node_id
                )
            )
        ).all()
    assert len(edges) == 1
    assert edges[0].capped is True
