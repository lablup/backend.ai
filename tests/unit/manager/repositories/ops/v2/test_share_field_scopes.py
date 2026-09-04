"""Shares capped by rows, against a real database.

What these tests pin down:

- ``replace_share`` lends every field up to a cap; ``replace_share_fields`` lends READ|UPDATE on
  paths only, never a bit already lent on every field. A share is own under a cap
  with one cap row per bit; a path row hangs off the bit it scopes.
- Sharing again states what holds now: ``replace_share`` and ``replace_share_fields`` each replace
  every earlier cap row; a mixed share is ``replace_share`` then ``widen_share_fields``.
- ``widen_share`` / ``widen_share_fields`` add bits and paths, drop the paths a bit
  reaching every field makes redundant, and leave an owned entity as it is.
- ``narrow_share`` / ``narrow_share_fields`` take bits and paths back, a path with
  its descendants; a bit lent on every field cannot be narrowed by a path.
- A zero cap is own under a cap with no cap rows: listed, lent nothing, gone only
  by ``unshare``, which takes the cap rows and paths with it and leaves what the
  scope owns. Sharing what the scope owns replaces own with the share.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import override

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.permission.id import FieldPath
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.errors.permission import InvalidFieldPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.testutils.db import with_tables

_GRANTEE_TYPE = EntityType("user")
_ENTITY_TYPE = EntityType("vfolder")

_TOKEN = FieldPath("token")
_DATA = FieldPath("data")
_READ = Permission.READ
_UPDATE = Permission.UPDATE


class _GranteeID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return _GRANTEE_TYPE


class _TargetID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return _ENTITY_TYPE


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        database_connection,
        [
            VirtualEntityRow,
            EntityMembershipRow,
            EntityMembershipCapRow,
            EntityMembershipFieldRow,
            ScopeBindingRow,
        ],
    ):
        yield database_connection


@pytest.fixture
def provider(database: ExtendedAsyncSAEngine) -> ShareOpsProvider:
    return ShareOpsProvider(database)


async def _target(database: ExtendedAsyncSAEngine) -> _TargetID:
    """An entity with its virtual entity, as every create provisions."""
    entity = _TargetID(uuid.uuid4())
    async with database.begin_session() as sess:
        sess.add(VirtualEntityRow(entity_type=_ENTITY_TYPE, entity_id=entity))
    return entity


@pytest.fixture
async def grantee(database: ExtendedAsyncSAEngine) -> _GranteeID:
    grantee_id = _GranteeID(uuid.uuid4())
    async with database.begin_session() as sess:
        sess.add(VirtualEntityRow(entity_type=_GRANTEE_TYPE, entity_id=grantee_id))
    return grantee_id


async def _share_of(
    database: ExtendedAsyncSAEngine, entity: _TargetID
) -> EntityMembershipRow | None:
    """The scope's share of the entity; the provisioning self own is not one."""
    async with database.begin_readonly_session() as sess:
        node = (
            sa.select(VirtualEntityRow.id)
            .where(
                VirtualEntityRow.entity_type == _ENTITY_TYPE,
                VirtualEntityRow.entity_id == entity,
            )
            .scalar_subquery()
        )
        return (
            await sess.scalars(
                sa.select(EntityMembershipRow).where(
                    EntityMembershipRow.member_entity_id == node,
                    EntityMembershipRow.virtual_entity_id != node,
                )
            )
        ).one_or_none()


async def _caps(
    database: ExtendedAsyncSAEngine, share: EntityMembershipRow
) -> dict[Permission, tuple[bool, set[FieldPath]]]:
    """Per bit let through: whether on every field, and the paths otherwise."""
    async with database.begin_readonly_session() as sess:
        rows = (
            await sess.execute(
                sa.select(
                    EntityMembershipCapRow.permission,
                    EntityMembershipCapRow.all_fields,
                    EntityMembershipFieldRow.path,
                )
                .select_from(EntityMembershipCapRow)
                .outerjoin(
                    EntityMembershipFieldRow,
                    EntityMembershipFieldRow.cap_id == EntityMembershipCapRow.id,
                )
                .where(EntityMembershipCapRow.membership_id == share.id)
            )
        ).all()
    caps: dict[Permission, tuple[bool, set[FieldPath]]] = {}
    for row in rows:
        _, paths = caps.setdefault(Permission(row.permission), (row.all_fields, set()))
        if row.path is not None:
            paths.add(row.path)
    return caps


async def _cap_row_count(database: ExtendedAsyncSAEngine) -> int:
    async with database.begin_readonly_session() as sess:
        return (
            await sess.execute(sa.select(sa.func.count()).select_from(EntityMembershipCapRow))
        ).scalar_one()


# =============================================================================
# Validation
# =============================================================================


async def test_rejects_a_bit_outside_read_update_as_key(
    database: ExtendedAsyncSAEngine, provider: ShareOpsProvider, grantee: _GranteeID
) -> None:
    async with provider.write_ops() as ops:
        with pytest.raises(InvalidFieldPermission):
            await ops.replace_share_fields(
                grantee, await _target(database), {_READ | _UPDATE: [_TOKEN]}
            )


async def test_rejects_bits_outside_read_update(
    database: ExtendedAsyncSAEngine, provider: ShareOpsProvider, grantee: _GranteeID
) -> None:
    async with provider.write_ops() as ops:
        with pytest.raises(InvalidFieldPermission):
            await ops.replace_share_fields(
                grantee, await _target(database), {Permission.CREATE: [_TOKEN]}
            )


# =============================================================================
# share / widen / unshare
# =============================================================================


async def test_share_then_widen_fields_writes_cap_rows_and_paths(
    database: ExtendedAsyncSAEngine, provider: ShareOpsProvider, grantee: _GranteeID
) -> None:
    entity = await _target(database)
    async with provider.write_ops() as ops:
        await ops.replace_share(grantee, entity, _READ)
        await ops.widen_share_fields(grantee, entity, {_UPDATE: [_DATA]})
    share = await _share_of(database, entity)
    assert share is not None
    assert share.capped is True
    assert await _caps(database, share) == {_READ: (True, set()), _UPDATE: (False, {_DATA})}


async def test_share_again_replaces_cap_rows_and_paths(
    database: ExtendedAsyncSAEngine, provider: ShareOpsProvider, grantee: _GranteeID
) -> None:
    entity = await _target(database)
    async with provider.write_ops() as ops:
        await ops.replace_share_fields(grantee, entity, {_READ: [_DATA], _UPDATE: [_DATA]})
    async with provider.write_ops() as ops:
        await ops.replace_share(grantee, entity, _READ)
    share = await _share_of(database, entity)
    assert share is not None
    assert await _caps(database, share) == {_READ: (True, set())}


async def test_share_fields_replaces_every_cap_row(
    database: ExtendedAsyncSAEngine, provider: ShareOpsProvider, grantee: _GranteeID
) -> None:
    entity = await _target(database)
    async with provider.write_ops() as ops:
        await ops.replace_share(grantee, entity, Permission.CREATE)
        await ops.widen_share_fields(grantee, entity, {_READ: [_DATA]})
    async with provider.write_ops() as ops:
        await ops.replace_share_fields(grantee, entity, {_UPDATE: [_TOKEN]})
    share = await _share_of(database, entity)
    assert share is not None
    assert await _caps(database, share) == {_UPDATE: (False, {_TOKEN})}


async def test_widen_adds_bits_and_paths(
    database: ExtendedAsyncSAEngine, provider: ShareOpsProvider, grantee: _GranteeID
) -> None:
    entity = await _target(database)
    async with provider.write_ops() as ops:
        await ops.replace_share_fields(grantee, entity, {_READ: [_DATA]})
    async with provider.write_ops() as ops:
        await ops.widen_share(grantee, entity, Permission.CREATE)
        await ops.widen_share_fields(grantee, entity, {_READ: [_TOKEN], _UPDATE: [_TOKEN]})
    share = await _share_of(database, entity)
    assert share is not None
    assert await _caps(database, share) == {
        Permission.CREATE: (True, set()),
        _READ: (False, {_DATA, _TOKEN}),
        _UPDATE: (False, {_TOKEN}),
    }


async def test_widen_to_every_field_drops_redundant_paths(
    database: ExtendedAsyncSAEngine, provider: ShareOpsProvider, grantee: _GranteeID
) -> None:
    entity = await _target(database)
    async with provider.write_ops() as ops:
        await ops.replace_share_fields(grantee, entity, {_READ: [_DATA], _UPDATE: [_DATA]})
    async with provider.write_ops() as ops:
        await ops.widen_share(grantee, entity, _READ)
    share = await _share_of(database, entity)
    assert share is not None
    assert await _caps(database, share) == {_READ: (True, set()), _UPDATE: (False, {_DATA})}


async def test_widen_leaves_an_owned_entity(
    database: ExtendedAsyncSAEngine, provider: ShareOpsProvider, grantee: _GranteeID
) -> None:
    """What the scope owns is not capped: nothing to widen, nothing to scope."""
    entity = _TargetID(uuid.uuid4())
    async with database.begin_session() as sess:
        entity_node = VirtualEntityRow(entity_type=_ENTITY_TYPE, entity_id=entity)
        sess.add(entity_node)
        await sess.flush()
        grantee_node_id = (
            await sess.scalars(
                sa.select(VirtualEntityRow.id).where(VirtualEntityRow.entity_id == grantee)
            )
        ).one()
        sess.add(
            EntityMembershipRow(
                virtual_entity_id=grantee_node_id, member_entity_id=entity_node.id, capped=False
            )
        )
    async with provider.write_ops() as ops:
        await ops.widen_share(grantee, entity, _READ)
        await ops.widen_share_fields(grantee, entity, {_UPDATE: [_DATA]})
    share = await _share_of(database, entity)
    assert share is not None
    assert share.capped is False
    assert await _caps(database, share) == {}


async def test_widen_without_a_share_writes_one(
    database: ExtendedAsyncSAEngine, provider: ShareOpsProvider, grantee: _GranteeID
) -> None:
    entity = await _target(database)
    async with provider.write_ops() as ops:
        await ops.widen_share(grantee, entity, _READ)
        await ops.widen_share_fields(grantee, entity, {_UPDATE: [_DATA]})
    share = await _share_of(database, entity)
    assert share is not None
    assert share.capped is True
    assert await _caps(database, share) == {_READ: (True, set()), _UPDATE: (False, {_DATA})}


async def test_zero_cap_lists_and_survives_other_writes(
    database: ExtendedAsyncSAEngine, provider: ShareOpsProvider, grantee: _GranteeID
) -> None:
    listed = await _target(database)
    other = await _target(database)
    async with provider.write_ops() as ops:
        await ops.replace_share(grantee, listed, Permission.NONE)
        await ops.replace_share(grantee, other, _READ)
        await ops.widen_share_fields(grantee, other, {_UPDATE: [_DATA]})
    async with provider.write_ops() as ops:
        await ops.widen_share(grantee, other, _UPDATE)
        await ops.unshare(grantee, [other])
    share = await _share_of(database, listed)
    assert share is not None
    assert share.capped is True
    assert await _caps(database, share) == {}
    assert await _share_of(database, other) is None
    assert await _cap_row_count(database) == 0
    async with provider.write_ops() as ops:
        await ops.unshare(grantee, [listed])
    assert await _share_of(database, listed) is None


async def test_unshare_leaves_what_the_scope_owns(
    database: ExtendedAsyncSAEngine, provider: ShareOpsProvider, grantee: _GranteeID
) -> None:
    entity = await _target(database)
    async with provider.write_ops() as ops:
        await ops.replace_share(grantee, entity, _READ)
        await ops.transfer([], [grantee], entity)
    async with provider.write_ops() as ops:
        await ops.unshare(grantee, [entity])
    share = await _share_of(database, entity)
    assert share is not None
    assert share.capped is False
    assert await _caps(database, share) == {}


async def test_narrow_takes_bits_back_and_keeps_the_share(
    database: ExtendedAsyncSAEngine, provider: ShareOpsProvider, grantee: _GranteeID
) -> None:
    entity = await _target(database)
    async with provider.write_ops() as ops:
        await ops.replace_share(grantee, entity, _READ | Permission.CREATE)
        await ops.widen_share_fields(grantee, entity, {_UPDATE: [_DATA]})
    async with provider.write_ops() as ops:
        await ops.narrow_share(grantee, entity, Permission.CREATE | _UPDATE)
    share = await _share_of(database, entity)
    assert share is not None
    assert share.capped is True
    assert await _caps(database, share) == {_READ: (True, set())}


async def test_narrow_fields_takes_a_path_and_its_descendants(
    database: ExtendedAsyncSAEngine, provider: ShareOpsProvider, grantee: _GranteeID
) -> None:
    entity = await _target(database)
    nested = FieldPath("data.inner")
    async with provider.write_ops() as ops:
        await ops.replace_share(grantee, entity, _READ)
        await ops.widen_share_fields(grantee, entity, {_UPDATE: [_DATA, nested, _TOKEN]})
    async with provider.write_ops() as ops:
        await ops.narrow_share_fields(grantee, entity, {_UPDATE: [_DATA]})
    share = await _share_of(database, entity)
    assert share is not None
    assert await _caps(database, share) == {_READ: (True, set()), _UPDATE: (False, {_TOKEN})}
    async with provider.write_ops() as ops:
        await ops.narrow_share_fields(grantee, entity, {_UPDATE: [_TOKEN]})
    assert await _caps(database, share) == {_READ: (True, set()), _UPDATE: (False, set())}


async def test_narrow_fields_rejects_a_bit_lent_on_every_field(
    database: ExtendedAsyncSAEngine, provider: ShareOpsProvider, grantee: _GranteeID
) -> None:
    entity = await _target(database)
    async with provider.write_ops() as ops:
        await ops.replace_share(grantee, entity, _READ)
    with pytest.raises(InvalidFieldPermission):
        async with provider.write_ops() as ops:
            await ops.narrow_share_fields(grantee, entity, {_READ: [_DATA]})


async def test_share_replaces_what_the_scope_owns(
    database: ExtendedAsyncSAEngine, provider: ShareOpsProvider, grantee: _GranteeID
) -> None:
    entity = await _target(database)
    async with provider.write_ops() as ops:
        await ops.transfer([], [grantee], entity)
    async with provider.write_ops() as ops:
        await ops.replace_share(grantee, entity, _READ)
        await ops.replace_share_fields(grantee, entity, {_UPDATE: [_DATA]})
    share = await _share_of(database, entity)
    assert share is not None
    assert share.capped is True
    assert await _caps(database, share) == {_UPDATE: (False, {_DATA})}
