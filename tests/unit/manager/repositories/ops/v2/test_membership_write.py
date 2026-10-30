"""Adding a scope to what owns an entity, and taking one away, against a real database.

What these tests pin down:

- Adding has the scope own and govern the entity, and leaves the scopes already
  holding it alone.
- Adding the same scope twice writes nothing more, so a run split into chunks can be
  repeated from the start.
- Adding names many entities and many scopes at once, covering every pair.
- A scope that held the entity under a cap comes to own it outright.
- Removing takes both edges back and is silent on a scope that never held it.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import override

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.common.data.permission.types import Permission
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

_SCOPE_TYPE = ProjectEntityType()
_ENTITY_TYPE = ResourceGroupEntityType()


class _ScopeID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return _SCOPE_TYPE


class _EntityID(EntityIdentifier):
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


async def _add_scope(database: ExtendedAsyncSAEngine) -> _ScopeID:
    scope = _ScopeID(uuid.uuid4())
    async with database.begin_session() as sess:
        sess.add(VirtualEntityRow(entity_type=_SCOPE_TYPE, entity_id=scope))
    return scope


async def _add_entity(database: ExtendedAsyncSAEngine) -> _EntityID:
    entity = _EntityID(uuid.uuid4())
    async with database.begin_session() as sess:
        sess.add(VirtualEntityRow(entity_type=_ENTITY_TYPE, entity_id=entity))
    return entity


def _node(entity: EntityIdentifier) -> sa.ScalarSelect[VirtualEntityID]:
    return (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == entity.entity_type(),
            VirtualEntityRow.entity_id == entity,
        )
        .scalar_subquery()
    )


async def _owns(
    database: ExtendedAsyncSAEngine, scope: EntityIdentifier, entity: EntityIdentifier
) -> bool:
    """Whether the scope owns the entity outright — an own edge carries no cap."""
    async with database.begin_readonly_session() as sess:
        return (
            await sess.scalar(
                sa.select(EntityMembershipRow.id).where(
                    EntityMembershipRow.virtual_entity_id == _node(scope),
                    EntityMembershipRow.member_entity_id == _node(entity),
                    EntityMembershipRow.capped.is_(False),
                )
            )
        ) is not None


async def _governs(
    database: ExtendedAsyncSAEngine, scope: EntityIdentifier, entity: EntityIdentifier
) -> bool:
    async with database.begin_readonly_session() as sess:
        return (
            await sess.scalar(
                sa.select(ScopeBindingRow.virtual_entity_id).where(
                    ScopeBindingRow.virtual_entity_id == _node(entity),
                    ScopeBindingRow.scope_entity_id == _node(scope),
                )
            )
        ) is not None


async def _edge_counts(database: ExtendedAsyncSAEngine) -> tuple[int, int]:
    async with database.begin_readonly_session() as sess:
        memberships = await sess.scalar(sa.select(sa.func.count()).select_from(EntityMembershipRow))
        bindings = await sess.scalar(sa.select(sa.func.count()).select_from(ScopeBindingRow))
    return memberships or 0, bindings or 0


class TestAddMembership:
    async def test_the_scope_comes_to_own_and_govern_the_entity(
        self, database: ExtendedAsyncSAEngine, provider: ShareOpsProvider
    ) -> None:
        scope = await _add_scope(database)
        entity = await _add_entity(database)

        async with provider.write_ops() as w:
            await w.add_membership([scope], [entity])

        assert await _owns(database, scope, entity)
        assert await _governs(database, scope, entity)

    async def test_the_scopes_already_holding_it_are_left_alone(
        self, database: ExtendedAsyncSAEngine, provider: ShareOpsProvider
    ) -> None:
        held_by = await _add_scope(database)
        added = await _add_scope(database)
        entity = await _add_entity(database)
        async with provider.write_ops() as w:
            await w.add_membership([held_by], [entity])

        async with provider.write_ops() as w:
            await w.add_membership([added], [entity])

        assert await _owns(database, held_by, entity)
        assert await _owns(database, added, entity)

    async def test_adding_it_twice_writes_nothing_more(
        self, database: ExtendedAsyncSAEngine, provider: ShareOpsProvider
    ) -> None:
        scope = await _add_scope(database)
        entity = await _add_entity(database)
        async with provider.write_ops() as w:
            await w.add_membership([scope], [entity])
        once = await _edge_counts(database)

        async with provider.write_ops() as w:
            await w.add_membership([scope], [entity])

        assert await _edge_counts(database) == once

    async def test_every_pair_of_the_scopes_and_entities_named_is_covered(
        self, database: ExtendedAsyncSAEngine, provider: ShareOpsProvider
    ) -> None:
        scopes = [await _add_scope(database) for _ in range(2)]
        entities = [await _add_entity(database) for _ in range(3)]

        async with provider.write_ops() as w:
            await w.add_membership(scopes, entities)

        for scope in scopes:
            for entity in entities:
                assert await _owns(database, scope, entity)
                assert await _governs(database, scope, entity)

    async def test_a_share_the_scope_held_becomes_own(
        self, database: ExtendedAsyncSAEngine, provider: ShareOpsProvider
    ) -> None:
        scope = await _add_scope(database)
        entity = await _add_entity(database)
        async with provider.write_ops() as w:
            await w.replace_share(scope, entity, Permission.READ)
        assert not await _owns(database, scope, entity)

        async with provider.write_ops() as w:
            await w.add_membership([scope], [entity])

        assert await _owns(database, scope, entity)
        async with database.begin_readonly_session() as sess:
            caps = (
                await sess.scalar(sa.select(sa.func.count()).select_from(EntityMembershipCapRow))
            ) or 0
        assert caps == 0

    async def test_naming_no_scope_or_no_entity_writes_nothing(
        self, database: ExtendedAsyncSAEngine, provider: ShareOpsProvider
    ) -> None:
        scope = await _add_scope(database)
        entity = await _add_entity(database)

        async with provider.write_ops() as w:
            await w.add_membership([], [entity])
            await w.add_membership([scope], [])

        assert await _edge_counts(database) == (0, 0)


class TestRemoveMembership:
    async def test_the_scope_stops_owning_and_governing_the_entity(
        self, database: ExtendedAsyncSAEngine, provider: ShareOpsProvider
    ) -> None:
        scope = await _add_scope(database)
        entity = await _add_entity(database)
        async with provider.write_ops() as w:
            await w.add_membership([scope], [entity])

        async with provider.write_ops() as w:
            await w.remove_membership([scope], [entity])

        assert not await _owns(database, scope, entity)
        assert not await _governs(database, scope, entity)

    async def test_the_other_scopes_holding_it_stay(
        self, database: ExtendedAsyncSAEngine, provider: ShareOpsProvider
    ) -> None:
        kept = await _add_scope(database)
        removed = await _add_scope(database)
        entity = await _add_entity(database)
        async with provider.write_ops() as w:
            await w.add_membership([kept, removed], [entity])

        async with provider.write_ops() as w:
            await w.remove_membership([removed], [entity])

        assert await _owns(database, kept, entity)
        assert await _governs(database, kept, entity)
        assert not await _owns(database, removed, entity)

    async def test_a_scope_that_never_held_it_is_silent(
        self, database: ExtendedAsyncSAEngine, provider: ShareOpsProvider
    ) -> None:
        scope = await _add_scope(database)
        entity = await _add_entity(database)

        async with provider.write_ops() as w:
            await w.remove_membership([scope], [entity])

        assert await _edge_counts(database) == (0, 0)

    async def test_removing_it_twice_leaves_the_same_edges(
        self, database: ExtendedAsyncSAEngine, provider: ShareOpsProvider
    ) -> None:
        kept = await _add_scope(database)
        removed = await _add_scope(database)
        entity = await _add_entity(database)
        async with provider.write_ops() as w:
            await w.add_membership([kept, removed], [entity])
        async with provider.write_ops() as w:
            await w.remove_membership([removed], [entity])
        once = await _edge_counts(database)

        async with provider.write_ops() as w:
            await w.remove_membership([removed], [entity])

        assert await _edge_counts(database) == once
