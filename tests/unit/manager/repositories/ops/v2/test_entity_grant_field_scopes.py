"""Entity grants capped by rows, against a real database.

What these tests pin down:

- A grant's field scope holds READ|UPDATE bits only, never a bit the cap already
  holds on every field. A share is a capped edge with one cap row per bit; a
  path row hangs off the bit it scopes.
- ``grant`` writes the edge, its cap rows and paths, and a re-grant replaces them.
- ``widen`` adds bits and paths, drops the paths a bit reaching every field makes
  redundant, and leaves a belonging edge (not capped) as it is.
- A zero cap is a capped edge with no cap rows: enrolled, granted nothing, gone
  only by an explicit revoke, which takes the cap rows and paths with the edge.
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
from ai.backend.manager.models.specs.membership import EntityGrant
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
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
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
def provider(database: ExtendedAsyncSAEngine) -> V2DBOpsProvider:
    return V2DBOpsProvider(database)


@pytest.fixture
async def grantee(database: ExtendedAsyncSAEngine) -> _GranteeID:
    grantee_id = _GranteeID(uuid.uuid4())
    async with database.begin_session() as sess:
        sess.add(VirtualEntityRow(entity_type=_GRANTEE_TYPE, entity_id=grantee_id))
    return grantee_id


def _grant(
    entity: _TargetID,
    grantee: _GranteeID,
    cap: Permission,
    fields: dict[FieldPath, Permission] | None = None,
) -> EntityGrant:
    return EntityGrant(entity=entity, grantee=grantee, permission_cap=cap, fields=fields or {})


async def _edge(database: ExtendedAsyncSAEngine, entity: _TargetID) -> EntityMembershipRow | None:
    """The entity's grant edge; the provisioning self edge is not one."""
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
    database: ExtendedAsyncSAEngine, edge: EntityMembershipRow
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
                .where(EntityMembershipCapRow.membership_id == edge.id)
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


async def test_rejects_bit_the_cap_already_holds(
    provider: V2DBOpsProvider, grantee: _GranteeID
) -> None:
    async with provider.write_ops() as ops:
        with pytest.raises(InvalidFieldPermission):
            await ops.grant_entities([
                _grant(_TargetID(uuid.uuid4()), grantee, _READ, {_TOKEN: _READ})
            ])


async def test_rejects_bits_outside_read_update(
    provider: V2DBOpsProvider, grantee: _GranteeID
) -> None:
    async with provider.write_ops() as ops:
        with pytest.raises(InvalidFieldPermission):
            await ops.grant_entities([
                _grant(
                    _TargetID(uuid.uuid4()), grantee, Permission.NONE, {_TOKEN: Permission.CREATE}
                )
            ])


# =============================================================================
# grant / widen / revoke
# =============================================================================


async def test_grant_writes_cap_rows_and_paths(
    database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, grantee: _GranteeID
) -> None:
    entity = _TargetID(uuid.uuid4())
    async with provider.write_ops() as ops:
        await ops.grant_entities([_grant(entity, grantee, _READ, {_DATA: _UPDATE})])
    edge = await _edge(database, entity)
    assert edge is not None
    assert edge.capped is True
    assert await _caps(database, edge) == {_READ: (True, set()), _UPDATE: (False, {_DATA})}


async def test_regrant_replaces_cap_rows_and_paths(
    database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, grantee: _GranteeID
) -> None:
    entity = _TargetID(uuid.uuid4())
    async with provider.write_ops() as ops:
        await ops.grant_entities([
            _grant(entity, grantee, Permission.NONE, {_DATA: _READ | _UPDATE})
        ])
    async with provider.write_ops() as ops:
        await ops.grant_entities([_grant(entity, grantee, _READ, {_TOKEN: _UPDATE})])
    edge = await _edge(database, entity)
    assert edge is not None
    assert await _caps(database, edge) == {_READ: (True, set()), _UPDATE: (False, {_TOKEN})}


async def test_widen_adds_bits_and_paths(
    database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, grantee: _GranteeID
) -> None:
    entity = _TargetID(uuid.uuid4())
    async with provider.write_ops() as ops:
        await ops.grant_entities([_grant(entity, grantee, Permission.NONE, {_DATA: _READ})])
    async with provider.write_ops() as ops:
        await ops.widen_entity_grants([
            _grant(entity, grantee, Permission.CREATE, {_TOKEN: _READ | _UPDATE})
        ])
    edge = await _edge(database, entity)
    assert edge is not None
    assert await _caps(database, edge) == {
        Permission.CREATE: (True, set()),
        _READ: (False, {_DATA, _TOKEN}),
        _UPDATE: (False, {_TOKEN}),
    }


async def test_widen_to_every_field_drops_redundant_paths(
    database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, grantee: _GranteeID
) -> None:
    entity = _TargetID(uuid.uuid4())
    async with provider.write_ops() as ops:
        await ops.grant_entities([
            _grant(entity, grantee, Permission.NONE, {_DATA: _READ | _UPDATE})
        ])
    async with provider.write_ops() as ops:
        await ops.widen_entity_grants([_grant(entity, grantee, _READ)])
    edge = await _edge(database, entity)
    assert edge is not None
    assert await _caps(database, edge) == {_READ: (True, set()), _UPDATE: (False, {_DATA})}


async def test_widen_leaves_a_belonging_edge(
    database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, grantee: _GranteeID
) -> None:
    """A belonging edge is not capped: nothing to widen, nothing to scope."""
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
        await ops.widen_entity_grants([_grant(entity, grantee, _READ, {_DATA: _UPDATE})])
    edge = await _edge(database, entity)
    assert edge is not None
    assert edge.capped is False
    assert await _caps(database, edge) == {}


async def test_widen_absent_edge_inserts_with_paths(
    database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, grantee: _GranteeID
) -> None:
    entity = _TargetID(uuid.uuid4())
    async with provider.write_ops() as ops:
        await ops.widen_entity_grants([_grant(entity, grantee, _READ, {_DATA: _UPDATE})])
    edge = await _edge(database, entity)
    assert edge is not None
    assert edge.capped is True
    assert await _caps(database, edge) == {_READ: (True, set()), _UPDATE: (False, {_DATA})}


async def test_zero_cap_enrolls_and_survives_other_writes(
    database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, grantee: _GranteeID
) -> None:
    enrolled = _TargetID(uuid.uuid4())
    other = _TargetID(uuid.uuid4())
    async with provider.write_ops() as ops:
        await ops.grant_entities([
            _grant(enrolled, grantee, Permission.NONE),
            _grant(other, grantee, _READ, {_DATA: _UPDATE}),
        ])
    async with provider.write_ops() as ops:
        await ops.widen_entity_grants([_grant(other, grantee, _UPDATE)])
        await ops.revoke_entities([other], grantee)
    edge = await _edge(database, enrolled)
    assert edge is not None
    assert edge.capped is True
    assert await _caps(database, edge) == {}
    assert await _edge(database, other) is None
    assert await _cap_row_count(database) == 0
    async with provider.write_ops() as ops:
        await ops.revoke_entities([enrolled], grantee)
    assert await _edge(database, enrolled) is None
