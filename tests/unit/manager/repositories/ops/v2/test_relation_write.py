"""Relations between two entities, against a real database.

What these tests pin down:

- Linking writes the relation row, has the scope govern the target under READ, and
  shares the scope to the target under READ.
- Linking again restates the share: a cap narrowed in between comes back to READ.
- Unlinking removes the row, the govern and the share, and is silent on a pair never
  linked.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence
from typing import Any, override

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.membership import EntityGrant
from ai.backend.manager.models.specs.relation import RelationCreator, RelationPurger
from ai.backend.manager.models.specs.types import ConflictCheck, IntegrityErrorCheck
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

_SCOPE_TYPE = EntityType("project")
_TARGET_TYPE = EntityType("resource_group")


class _ScopeID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return _SCOPE_TYPE


class _TargetID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return _TARGET_TYPE


class RelationTestRow(Base):
    __tablename__ = "relation_write_test"
    __table_args__ = (sa.UniqueConstraint("scope_id", "target_id", name="uq_relation_write_test"),)

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    scope_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, nullable=False)


class _Creator(RelationCreator[RelationTestRow]):
    @override
    def row_class(self) -> type[RelationTestRow]:
        return RelationTestRow

    @override
    def build_row(self, scope: EntityIdentifier, target: EntityIdentifier) -> RelationTestRow:
        return RelationTestRow(
            id=uuid.uuid4(), scope_id=uuid.UUID(str(scope)), target_id=uuid.UUID(str(target))
        )

    @override
    def index_elements(self) -> list[str]:
        return ["scope_id", "target_id"]

    @override
    def build_conflict_values(self) -> dict[str, Any] | None:
        return None

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()


class _Purger(RelationPurger[RelationTestRow]):
    @override
    def row_class(self) -> type[RelationTestRow]:
        return RelationTestRow

    @override
    def conditions(
        self, scope: EntityIdentifier, target: EntityIdentifier
    ) -> Sequence[QueryCondition]:
        return (
            lambda: RelationTestRow.scope_id == uuid.UUID(str(scope)),
            lambda: RelationTestRow.target_id == uuid.UUID(str(target)),
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


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
            RelationTestRow,
        ],
    ):
        yield database_connection


@pytest.fixture
def provider(database: ExtendedAsyncSAEngine) -> V2DBOpsProvider:
    return V2DBOpsProvider(database)


@pytest.fixture
async def pair(database: ExtendedAsyncSAEngine) -> tuple[_ScopeID, _TargetID]:
    scope = _ScopeID(uuid.uuid4())
    target = _TargetID(uuid.uuid4())
    async with database.begin_session() as sess:
        sess.add(VirtualEntityRow(entity_type=_SCOPE_TYPE, entity_id=scope))
        sess.add(VirtualEntityRow(entity_type=_TARGET_TYPE, entity_id=target))
    return scope, target


async def _row_count(database: ExtendedAsyncSAEngine) -> int:
    async with database.begin_readonly_session() as sess:
        return (await sess.scalar(sa.select(sa.func.count()).select_from(RelationTestRow))) or 0


def _node(entity: EntityIdentifier) -> sa.ScalarSelect[Any]:
    return (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == entity.entity_type(),
            VirtualEntityRow.entity_id == entity,
        )
        .scalar_subquery()
    )


async def _govern_cap(
    database: ExtendedAsyncSAEngine, scope: EntityIdentifier, entity: EntityIdentifier
) -> Permission | None | bool:
    """The cap under which the scope governs the entity; ``False`` when it does not."""
    async with database.begin_readonly_session() as sess:
        row = (
            await sess.execute(
                sa.select(ScopeBindingRow.permission_cap).where(
                    ScopeBindingRow.virtual_entity_id == _node(entity),
                    ScopeBindingRow.scope_entity_id == _node(scope),
                )
            )
        ).one_or_none()
        return False if row is None else row.permission_cap


async def _share_cap(
    database: ExtendedAsyncSAEngine, scope: EntityIdentifier, member: EntityIdentifier
) -> Permission | None:
    """The cap under which the scope owns the member; ``None`` when it does not."""
    scope_node = (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == scope.entity_type(),
            VirtualEntityRow.entity_id == scope,
        )
        .scalar_subquery()
    )
    member_node = (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == member.entity_type(),
            VirtualEntityRow.entity_id == member,
        )
        .scalar_subquery()
    )
    async with database.begin_readonly_session() as sess:
        edge_id = await sess.scalar(
            sa.select(EntityMembershipRow.id).where(
                EntityMembershipRow.virtual_entity_id == scope_node,
                EntityMembershipRow.member_entity_id == member_node,
            )
        )
        if edge_id is None:
            return None
        bits = await sess.scalars(
            sa.select(EntityMembershipCapRow.permission).where(
                EntityMembershipCapRow.membership_id == edge_id
            )
        )
        cap = Permission.NONE
        for bit in bits:
            cap |= bit
        return cap


class TestCreateRelation:
    async def test_link_writes_the_row_the_govern_and_the_share(
        self,
        database: ExtendedAsyncSAEngine,
        provider: V2DBOpsProvider,
        pair: tuple[_ScopeID, _TargetID],
    ) -> None:
        scope, target = pair
        async with provider.write_ops() as ops:
            await ops.create_relation(_Creator(), scope, target)

        assert await _row_count(database) == 1
        assert await _govern_cap(database, scope, target) == Permission.READ
        assert await _share_cap(database, target, scope) == Permission.READ
        assert await _share_cap(database, scope, target) is None

    async def test_linking_again_keeps_one_row_and_restates_read(
        self,
        database: ExtendedAsyncSAEngine,
        provider: V2DBOpsProvider,
        pair: tuple[_ScopeID, _TargetID],
    ) -> None:
        scope, target = pair
        async with provider.write_ops() as ops:
            await ops.create_relation(_Creator(), scope, target)
            await ops.grant_entities([
                EntityGrant(entity=scope, grantee=target, permission_cap=Permission.NONE)
            ])
            await ops.create_relation(_Creator(), scope, target)

        assert await _row_count(database) == 1
        assert await _share_cap(database, target, scope) == Permission.READ


class TestPurgeRelation:
    async def test_unlink_removes_the_row_the_govern_and_the_share(
        self,
        database: ExtendedAsyncSAEngine,
        provider: V2DBOpsProvider,
        pair: tuple[_ScopeID, _TargetID],
    ) -> None:
        scope, target = pair
        async with provider.write_ops() as ops:
            await ops.create_relation(_Creator(), scope, target)
        async with provider.write_ops() as ops:
            await ops.purge_relation(_Purger(), scope, target)

        assert await _row_count(database) == 0
        assert await _govern_cap(database, scope, target) is False
        assert await _share_cap(database, target, scope) is None

    async def test_unlinking_a_pair_never_linked_is_silent(
        self,
        database: ExtendedAsyncSAEngine,
        provider: V2DBOpsProvider,
        pair: tuple[_ScopeID, _TargetID],
    ) -> None:
        scope, target = pair
        async with provider.write_ops() as ops:
            await ops.purge_relation(_Purger(), scope, target)

        assert await _row_count(database) == 0
