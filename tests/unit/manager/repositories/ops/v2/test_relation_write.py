"""Relations between two entities, against a real database.

What these tests pin down:

- Linking writes the relation row and makes each entity own the other under a READ
  cap, so each entity's scope sees the other and nothing more.
- Linking again restates the grants: a cap narrowed in between comes back to READ.
- Unlinking removes the row and both shares, and is silent on a pair never linked.
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

_LEFT_TYPE = EntityType("project")
_RIGHT_TYPE = EntityType("resource_group")


class _LeftID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return _LEFT_TYPE


class _RightID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return _RIGHT_TYPE


class RelationTestRow(Base):
    __tablename__ = "relation_write_test"
    __table_args__ = (sa.UniqueConstraint("left_id", "right_id", name="uq_relation_write_test"),)

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    left_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, nullable=False)
    right_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, nullable=False)


class _Creator(RelationCreator[RelationTestRow]):
    @override
    def row_class(self) -> type[RelationTestRow]:
        return RelationTestRow

    @override
    def build_row(self, left: EntityIdentifier, right: EntityIdentifier) -> RelationTestRow:
        return RelationTestRow(
            id=uuid.uuid4(), left_id=uuid.UUID(str(left)), right_id=uuid.UUID(str(right))
        )

    @override
    def index_elements(self) -> list[str]:
        return ["left_id", "right_id"]

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
        self, left: EntityIdentifier, right: EntityIdentifier
    ) -> Sequence[QueryCondition]:
        return (
            lambda: RelationTestRow.left_id == uuid.UUID(str(left)),
            lambda: RelationTestRow.right_id == uuid.UUID(str(right)),
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
async def pair(database: ExtendedAsyncSAEngine) -> tuple[_LeftID, _RightID]:
    left = _LeftID(uuid.uuid4())
    right = _RightID(uuid.uuid4())
    async with database.begin_session() as sess:
        sess.add(VirtualEntityRow(entity_type=_LEFT_TYPE, entity_id=left))
        sess.add(VirtualEntityRow(entity_type=_RIGHT_TYPE, entity_id=right))
    return left, right


async def _row_count(database: ExtendedAsyncSAEngine) -> int:
    async with database.begin_readonly_session() as sess:
        return (await sess.scalar(sa.select(sa.func.count()).select_from(RelationTestRow))) or 0


async def _cap(
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
    async def test_link_writes_the_row_and_read_each_way(
        self,
        database: ExtendedAsyncSAEngine,
        provider: V2DBOpsProvider,
        pair: tuple[_LeftID, _RightID],
    ) -> None:
        left, right = pair
        async with provider.write_ops() as ops:
            await ops.create_relation(_Creator(), left, right)

        assert await _row_count(database) == 1
        assert await _cap(database, left, right) == Permission.READ
        assert await _cap(database, right, left) == Permission.READ

    async def test_linking_again_keeps_one_row_and_restates_read(
        self,
        database: ExtendedAsyncSAEngine,
        provider: V2DBOpsProvider,
        pair: tuple[_LeftID, _RightID],
    ) -> None:
        left, right = pair
        async with provider.write_ops() as ops:
            await ops.create_relation(_Creator(), left, right)
            await ops.grant_entities([
                EntityGrant(entity=right, grantee=left, permission_cap=Permission.NONE)
            ])
            await ops.create_relation(_Creator(), left, right)

        assert await _row_count(database) == 1
        assert await _cap(database, left, right) == Permission.READ


class TestPurgeRelation:
    async def test_unlink_removes_the_row_and_both_shares(
        self,
        database: ExtendedAsyncSAEngine,
        provider: V2DBOpsProvider,
        pair: tuple[_LeftID, _RightID],
    ) -> None:
        left, right = pair
        async with provider.write_ops() as ops:
            await ops.create_relation(_Creator(), left, right)
        async with provider.write_ops() as ops:
            await ops.purge_relation(_Purger(), left, right)

        assert await _row_count(database) == 0
        assert await _cap(database, left, right) is None
        assert await _cap(database, right, left) is None

    async def test_unlinking_a_pair_never_linked_is_silent(
        self,
        database: ExtendedAsyncSAEngine,
        provider: V2DBOpsProvider,
        pair: tuple[_LeftID, _RightID],
    ) -> None:
        left, right = pair
        async with provider.write_ops() as ops:
            await ops.purge_relation(_Purger(), left, right)

        assert await _row_count(database) == 0
