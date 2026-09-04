"""Relations between two entities, against a real database.

What these tests pin down:

- Linking writes the relation row, has the scope govern the target under READ, and
  shares the scope to the target under READ.
- Linking adds READ to what the target already holds of the scope and unlinking
  takes only READ back, so a share set beside the relation survives.
- Linking a pair already linked is a unique violation.
- Switching a relation off and back on touches the row alone: both reads stay.
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
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.relation import (
    RelationCreator,
    RelationLifecycleUpdater,
    RelationPurger,
)
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
from ai.backend.manager.repositories.ops.v2.relation.provider import RelationOpsProvider
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
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
    off: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)


class _Creator(RelationCreator[_ScopeID, _TargetID, RelationTestRow]):
    @override
    def row_class(self) -> type[RelationTestRow]:
        return RelationTestRow

    @override
    def build_row(self, scope: _ScopeID, target: _TargetID) -> RelationTestRow:
        return RelationTestRow(id=uuid.uuid4(), scope_id=scope, target_id=target)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()


def _pair_conditions(scope: _ScopeID, target: _TargetID) -> Sequence[QueryCondition]:
    return (
        lambda: RelationTestRow.scope_id == scope,
        lambda: RelationTestRow.target_id == target,
    )


class _SwitchOff(RelationLifecycleUpdater[_ScopeID, _TargetID, RelationTestRow]):
    @override
    def row_class(self) -> type[RelationTestRow]:
        return RelationTestRow

    @override
    def conditions(self, scope: _ScopeID, target: _TargetID) -> Sequence[QueryCondition]:
        return _pair_conditions(scope, target)

    @override
    def build_values(self) -> dict[str, Any]:
        return {"off": True}


class _SwitchOn(_SwitchOff):
    @override
    def build_values(self) -> dict[str, Any]:
        return {"off": False}


class _Purger(RelationPurger[_ScopeID, _TargetID, RelationTestRow]):
    @override
    def row_class(self) -> type[RelationTestRow]:
        return RelationTestRow

    @override
    def conditions(self, scope: _ScopeID, target: _TargetID) -> Sequence[QueryCondition]:
        return _pair_conditions(scope, target)

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
def provider(database: ExtendedAsyncSAEngine) -> RelationOpsProvider:
    return RelationOpsProvider(database)


@pytest.fixture
async def pair(database: ExtendedAsyncSAEngine) -> tuple[_ScopeID, _TargetID]:
    scope = _ScopeID(uuid.uuid4())
    target = _TargetID(uuid.uuid4())
    async with database.begin_session() as sess:
        sess.add(VirtualEntityRow(entity_type=_SCOPE_TYPE, entity_id=scope))
        sess.add(VirtualEntityRow(entity_type=_TARGET_TYPE, entity_id=target))
    return scope, target


async def _off(database: ExtendedAsyncSAEngine) -> bool:
    async with database.begin_readonly_session() as sess:
        return (await sess.execute(sa.select(RelationTestRow.off))).scalar_one()


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
        provider: RelationOpsProvider,
        pair: tuple[_ScopeID, _TargetID],
    ) -> None:
        scope, target = pair
        async with provider.write_ops() as ops:
            await ops.create_relation(_Creator(), scope, target)

        assert await _row_count(database) == 1
        assert await _govern_cap(database, scope, target) == Permission.READ
        assert await _share_cap(database, target, scope) == Permission.READ
        assert await _share_cap(database, scope, target) is None

    async def test_linking_a_linked_pair_is_a_unique_violation(
        self,
        database: ExtendedAsyncSAEngine,
        provider: RelationOpsProvider,
        pair: tuple[_ScopeID, _TargetID],
    ) -> None:
        scope, target = pair
        async with provider.write_ops() as ops:
            await ops.create_relation(_Creator(), scope, target)
        with pytest.raises(UniqueConstraintViolationError):
            async with provider.write_ops() as ops:
                await ops.create_relation(_Creator(), scope, target)

        assert await _row_count(database) == 1

    async def test_link_and_unlink_leave_a_share_set_beside_them(
        self,
        database: ExtendedAsyncSAEngine,
        provider: RelationOpsProvider,
        pair: tuple[_ScopeID, _TargetID],
    ) -> None:
        scope, target = pair
        async with ShareOpsProvider(database).write_ops() as share_ops:
            await share_ops.replace_share(target, scope, Permission.UPDATE)
        async with provider.write_ops() as ops:
            await ops.create_relation(_Creator(), scope, target)
        assert await _share_cap(database, target, scope) == Permission.READ | Permission.UPDATE

        async with provider.write_ops() as ops:
            await ops.purge_relation(_Purger(), scope, target)
        assert await _share_cap(database, target, scope) == Permission.UPDATE
        assert await _govern_cap(database, scope, target) is False


class TestSwitchRelation:
    async def test_off_and_on_touch_the_row_alone(
        self,
        database: ExtendedAsyncSAEngine,
        provider: RelationOpsProvider,
        pair: tuple[_ScopeID, _TargetID],
    ) -> None:
        scope, target = pair
        async with provider.write_ops() as ops:
            await ops.create_relation(_Creator(), scope, target)
        async with provider.write_ops() as ops:
            await ops.delete_relation(_SwitchOff(), scope, target)

        assert await _off(database) is True
        assert await _govern_cap(database, scope, target) == Permission.READ
        assert await _share_cap(database, target, scope) == Permission.READ

        async with provider.write_ops() as ops:
            await ops.restore_relation(_SwitchOn(), scope, target)

        assert await _off(database) is False


class TestPurgeRelation:
    async def test_unlink_removes_the_row_the_govern_and_the_share(
        self,
        database: ExtendedAsyncSAEngine,
        provider: RelationOpsProvider,
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
        provider: RelationOpsProvider,
        pair: tuple[_ScopeID, _TargetID],
    ) -> None:
        scope, target = pair
        async with provider.write_ops() as ops:
            assert await ops.purge_relation(_Purger(), scope, target) is False

        assert await _row_count(database) == 0
