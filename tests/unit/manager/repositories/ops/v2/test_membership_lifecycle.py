"""The v2 write specs run against a real database, family by family.

What these tests pin down:

- Scoped: a create registers the row in its parent's virtual scope and dual-writes
  the legacy association; a purge removes both with the row; an upsert registers
  idempotently. The parent's virtual scope is resolved, never created —
  ``VirtualScopeNotFound`` persists nothing.
- Global: plain writes, nothing registered.
- Field: a row is buildable only under its owner's identifier; its purge is a plain
  delete.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.types import EntityType, ScopeRef, ScopeType
from ai.backend.common.exception import RBACTypeConversionError
from ai.backend.common.identifier.entity import EntityID
from ai.backend.manager.data.permission.types import EntityType as LegacyEntityType
from ai.backend.manager.data.permission.types import ScopeType as LegacyScopeType
from ai.backend.manager.errors.permission import VirtualScopeNotFound
from ai.backend.manager.errors.repository import EntityNotFoundError
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.specs.creator import (
    FieldEntityCreator,
    GlobalEntityCreator,
    ScopedEntityCreator,
)
from ai.backend.manager.models.specs.membership import ScopedMembership
from ai.backend.manager.models.specs.purger import (
    FieldEntityPurger,
    GlobalEntityPurger,
    ScopedEntityPurger,
)
from ai.backend.manager.models.specs.types import ConflictCheck, IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import ScopedEntityUpserter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import TableOrORM, with_tables

# =============================================================================
# A test entity: single UUID PK, owned by a user scope through its `owner_id`.
# =============================================================================


class MemberedEntityTestRow(Base):
    __tablename__ = "test_v2_membered_entity"
    __table_args__ = (
        sa.UniqueConstraint("name", name="uq_test_v2_membered_entity_name"),
        {"extend_existing": True},
    )

    id: Mapped[UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    owner_id: Mapped[UUID] = mapped_column(GUID, nullable=False)


@dataclass(frozen=True)
class _MemberedData:
    id: UUID
    name: str
    owner_id: UUID


# "vfolder" exists in the legacy enums, so the transitional dual-write can convert it.
_ENTITY_TYPE = EntityType("vfolder")
_USER_SCOPE = ScopeType("user")


class _OwnerScopedMembership(ScopedMembership[MemberedEntityTestRow]):
    @override
    def entity_type(self) -> EntityType:
        return _ENTITY_TYPE

    @override
    def entity_id(self, row: MemberedEntityTestRow) -> EntityID:
        return row.id

    @override
    def parent_scope(self, row: MemberedEntityTestRow) -> ScopeRef:
        return ScopeRef(scope_type=_USER_SCOPE, scope_id=row.owner_id)


class _UnconvertibleMembership(_OwnerScopedMembership):
    """A type outside the legacy enum, so the dual-write cannot convert it."""

    @override
    def entity_type(self) -> EntityType:
        return EntityType("not_a_legacy_entity_type")


@dataclass
class _ScopedCreator(ScopedEntityCreator[MemberedEntityTestRow, _MemberedData]):
    name: str
    owner_id: UUID

    @override
    def membership(self) -> ScopedMembership[MemberedEntityTestRow]:
        return _OwnerScopedMembership()

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> MemberedEntityTestRow:
        return MemberedEntityTestRow(name=self.name, owner_id=self.owner_id)

    @override
    def to_data(self, row: MemberedEntityTestRow) -> _MemberedData:
        return _MemberedData(id=row.id, name=row.name, owner_id=row.owner_id)


@dataclass
class _UnconvertibleCreator(_ScopedCreator):
    @override
    def membership(self) -> ScopedMembership[MemberedEntityTestRow]:
        return _UnconvertibleMembership()


@dataclass
class _GlobalCreator(GlobalEntityCreator[MemberedEntityTestRow, _MemberedData]):
    name: str
    owner_id: UUID

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> MemberedEntityTestRow:
        return MemberedEntityTestRow(name=self.name, owner_id=self.owner_id)

    @override
    def to_data(self, row: MemberedEntityTestRow) -> _MemberedData:
        return _MemberedData(id=row.id, name=row.name, owner_id=row.owner_id)


@dataclass
class _FieldCreator(FieldEntityCreator[UUID, MemberedEntityTestRow, _MemberedData]):
    """Receives the owner id at execution time, the way a child row receives a
    just-created parent's id."""

    name: str

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: UUID) -> MemberedEntityTestRow:
        return MemberedEntityTestRow(name=self.name, owner_id=owner_id)

    @override
    def to_data(self, row: MemberedEntityTestRow) -> _MemberedData:
        return _MemberedData(id=row.id, name=row.name, owner_id=row.owner_id)


@dataclass
class _ScopedPurger(ScopedEntityPurger[MemberedEntityTestRow, _MemberedData]):
    target: UUID

    @override
    def membership(self) -> ScopedMembership[MemberedEntityTestRow]:
        return _OwnerScopedMembership()

    @override
    def row_class(self) -> type[MemberedEntityTestRow]:
        return MemberedEntityTestRow

    @override
    def pk_value(self) -> UUID:
        return self.target

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: MemberedEntityTestRow) -> _MemberedData:
        return _MemberedData(id=row.id, name=row.name, owner_id=row.owner_id)


@dataclass
class _GlobalPurger(GlobalEntityPurger[MemberedEntityTestRow, _MemberedData]):
    target: UUID

    @override
    def row_class(self) -> type[MemberedEntityTestRow]:
        return MemberedEntityTestRow

    @override
    def pk_value(self) -> UUID:
        return self.target

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: MemberedEntityTestRow) -> _MemberedData:
        return _MemberedData(id=row.id, name=row.name, owner_id=row.owner_id)


@dataclass
class _FieldPurger(FieldEntityPurger[MemberedEntityTestRow, _MemberedData]):
    target: UUID

    @override
    def row_class(self) -> type[MemberedEntityTestRow]:
        return MemberedEntityTestRow

    @override
    def pk_value(self) -> UUID:
        return self.target

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: MemberedEntityTestRow) -> _MemberedData:
        return _MemberedData(id=row.id, name=row.name, owner_id=row.owner_id)


@dataclass
class _ScopedUpserter(ScopedEntityUpserter[MemberedEntityTestRow, _MemberedData]):
    name: str
    owner_id: UUID

    @override
    def membership(self) -> ScopedMembership[MemberedEntityTestRow]:
        return _OwnerScopedMembership()

    @override
    def row_class(self) -> type[MemberedEntityTestRow]:
        return MemberedEntityTestRow

    @override
    def index_elements(self) -> list[str]:
        return ["name"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"name": self.name, "owner_id": self.owner_id}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"owner_id": self.owner_id}

    @override
    def to_data(self, row: MemberedEntityTestRow) -> _MemberedData:
        return _MemberedData(id=row.id, name=row.name, owner_id=row.owner_id)


# =============================================================================
# Fixtures and probes
# =============================================================================

_TABLES: Sequence[TableOrORM] = [
    MemberedEntityTestRow,
    VirtualScopeRow,
    EntityMembershipRow,
    AssociationScopesEntitiesRow,
]


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


@pytest.fixture
def provider(database: ExtendedAsyncSAEngine) -> V2DBOpsProvider:
    return V2DBOpsProvider(database)


@pytest.fixture
async def owner_id(database: ExtendedAsyncSAEngine) -> UUID:
    """A user scope whose virtual scope node exists — the parent scoped rows declare."""
    owner = uuid.uuid4()
    async with database.begin_session() as sess:
        sess.add(VirtualScopeRow(scope_type=_USER_SCOPE, scope_id=owner))
    return owner


async def _membership_entity_ids(database: ExtendedAsyncSAEngine, owner: UUID) -> set[UUID]:
    """Entity ids enrolled in the owner's virtual scope."""
    async with database.begin_readonly_session() as sess:
        rows = await sess.scalars(
            sa.select(EntityMembershipRow.entity_id)
            .join(VirtualScopeRow, EntityMembershipRow.virtual_scope_id == VirtualScopeRow.id)
            .where(
                VirtualScopeRow.scope_type == _USER_SCOPE,
                VirtualScopeRow.scope_id == owner,
                EntityMembershipRow.entity_type == _ENTITY_TYPE,
            )
        )
        return set(rows.all())


async def _association_entity_ids(database: ExtendedAsyncSAEngine, owner: UUID) -> set[str]:
    """Entity ids the legacy association records under the owner scope."""
    async with database.begin_readonly_session() as sess:
        rows = await sess.scalars(
            sa.select(AssociationScopesEntitiesRow.entity_id).where(
                AssociationScopesEntitiesRow.scope_type == LegacyScopeType.USER,
                AssociationScopesEntitiesRow.scope_id == str(owner),
                AssociationScopesEntitiesRow.entity_type == LegacyEntityType.VFOLDER,
            )
        )
        return set(rows.all())


async def _row_count(database: ExtendedAsyncSAEngine) -> int:
    async with database.begin_readonly_session() as sess:
        count = await sess.scalar(sa.select(sa.func.count()).select_from(MemberedEntityTestRow))
        return count or 0


# =============================================================================
# Scoped: create registers, purge removes, upsert registers idempotently
# =============================================================================


class TestScopedFamily:
    async def test_create_dual_writes_the_membership(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, owner_id: UUID
    ) -> None:
        async with provider.write_ops() as w:
            data = await w.create_scoped_entity(_ScopedCreator(name="a", owner_id=owner_id))

        assert data.owner_id == owner_id
        assert await _membership_entity_ids(database, owner_id) == {data.id}
        assert await _association_entity_ids(database, owner_id) == {str(data.id)}

    async def test_missing_parent_virtual_scope_fails_without_inserting(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider
    ) -> None:
        with pytest.raises(VirtualScopeNotFound):
            async with provider.write_ops() as w:
                await w.create_scoped_entity(_ScopedCreator(name="a", owner_id=uuid.uuid4()))

        assert await _row_count(database) == 0

    async def test_unconvertible_entity_type_fails_the_dual_write(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, owner_id: UUID
    ) -> None:
        with pytest.raises(RBACTypeConversionError):
            async with provider.write_ops() as w:
                await w.create_scoped_entity(_UnconvertibleCreator(name="a", owner_id=owner_id))

        assert await _row_count(database) == 0

    async def test_purge_removes_row_membership_and_association(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, owner_id: UUID
    ) -> None:
        async with provider.write_ops() as w:
            data = await w.create_scoped_entity(_ScopedCreator(name="a", owner_id=owner_id))

        async with provider.write_ops() as w:
            purged = await w.purge_scoped_entity(_ScopedPurger(target=data.id))

        assert purged is not None
        assert purged.id == data.id
        assert await _row_count(database) == 0
        assert await _membership_entity_ids(database, owner_id) == set()
        assert await _association_entity_ids(database, owner_id) == set()

    async def test_purge_of_a_missing_row_returns_none(
        self, provider: V2DBOpsProvider, owner_id: UUID
    ) -> None:
        async with provider.write_ops() as w:
            assert await w.purge_scoped_entity(_ScopedPurger(target=uuid.uuid4())) is None

    async def test_bulk_create_registers_each_membership(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, owner_id: UUID
    ) -> None:
        async with provider.write_ops() as w:
            created = await w.bulk_create_scoped_entities([
                _ScopedCreator(name="a", owner_id=owner_id),
                _ScopedCreator(name="b", owner_id=owner_id),
            ])

        assert await _membership_entity_ids(database, owner_id) == {c.id for c in created}

    async def test_bulk_create_fails_whole_batch_on_a_missing_parent(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, owner_id: UUID
    ) -> None:
        with pytest.raises(VirtualScopeNotFound):
            async with provider.write_ops() as w:
                await w.bulk_create_scoped_entities([
                    _ScopedCreator(name="a", owner_id=owner_id),
                    _ScopedCreator(name="b", owner_id=uuid.uuid4()),
                ])

        assert await _row_count(database) == 0

    async def test_bulk_purge_answers_for_each_named_entity(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, owner_id: UUID
    ) -> None:
        async with provider.write_ops() as w:
            data = await w.create_scoped_entity(_ScopedCreator(name="a", owner_id=owner_id))
        absent = uuid.uuid4()

        async with provider.write_ops() as w:
            result = await w.bulk_purge_scoped_entities({
                data.id: _ScopedPurger(target=data.id),
                absent: _ScopedPurger(target=absent),
            })

        assert set(result.successes) == {data.id}
        assert isinstance(result.errors[absent], EntityNotFoundError)
        assert await _membership_entity_ids(database, owner_id) == set()

    async def test_upsert_insert_registers_membership(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, owner_id: UUID
    ) -> None:
        async with provider.write_ops() as w:
            data = await w.upsert_scoped_entity(_ScopedUpserter(name="a", owner_id=owner_id))

        assert await _membership_entity_ids(database, owner_id) == {data.id}
        assert await _association_entity_ids(database, owner_id) == {str(data.id)}

    async def test_upsert_update_keeps_registration_single(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, owner_id: UUID
    ) -> None:
        async with provider.write_ops() as w:
            first = await w.upsert_scoped_entity(_ScopedUpserter(name="a", owner_id=owner_id))
        async with provider.write_ops() as w:
            second = await w.upsert_scoped_entity(_ScopedUpserter(name="a", owner_id=owner_id))

        assert second.id == first.id
        assert await _row_count(database) == 1
        assert await _membership_entity_ids(database, owner_id) == {first.id}

    async def test_upsert_with_a_missing_parent_fails(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider
    ) -> None:
        with pytest.raises(VirtualScopeNotFound):
            async with provider.write_ops() as w:
                await w.upsert_scoped_entity(_ScopedUpserter(name="a", owner_id=uuid.uuid4()))

        assert await _row_count(database) == 0


# =============================================================================
# Global: plain writes, nothing registered
# =============================================================================


class TestGlobalFamily:
    async def test_create_registers_nothing(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, owner_id: UUID
    ) -> None:
        async with provider.write_ops() as w:
            data = await w.create_global_entity(_GlobalCreator(name="a", owner_id=owner_id))

        assert data.id is not None
        assert await _membership_entity_ids(database, owner_id) == set()
        assert await _association_entity_ids(database, owner_id) == set()

    async def test_purge_is_a_plain_delete(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, owner_id: UUID
    ) -> None:
        async with provider.write_ops() as w:
            data = await w.create_global_entity(_GlobalCreator(name="a", owner_id=owner_id))

        async with provider.write_ops() as w:
            purged = await w.purge_global_entity(_GlobalPurger(target=data.id))

        assert purged is not None
        assert await _row_count(database) == 0


# =============================================================================
# Field: buildable only under an owner id; purge is a plain delete
# =============================================================================


class TestFieldFamily:
    async def test_create_takes_the_owner_identifier(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, owner_id: UUID
    ) -> None:
        async with provider.write_ops() as w:
            data = await w.create_field_entity(_FieldCreator(name="a"), owner_id)

        assert data.owner_id == owner_id
        assert await _membership_entity_ids(database, owner_id) == set()

    async def test_bulk_create_shares_one_owner(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, owner_id: UUID
    ) -> None:
        async with provider.write_ops() as w:
            created = await w.bulk_create_field_entities(
                [_FieldCreator(name="a"), _FieldCreator(name="b")],
                owner_id,
            )

        assert {c.owner_id for c in created} == {owner_id}
        assert await _row_count(database) == 2

    async def test_purge_is_a_plain_delete(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, owner_id: UUID
    ) -> None:
        async with provider.write_ops() as w:
            data = await w.create_field_entity(_FieldCreator(name="a"), owner_id)

        async with provider.write_ops() as w:
            purged = await w.purge_field_entity(_FieldPurger(target=data.id))

        assert purged is not None
        assert await _row_count(database) == 0
