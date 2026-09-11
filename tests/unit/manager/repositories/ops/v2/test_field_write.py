"""Bulk field upsert of the v2 write ops, against a real database.

What these tests pin down:

- Every row of one owner is written under that owner's id, in the order named.
- A conflicting row takes the update values alone, so a column the spec leaves out
  of them keeps what it held.
- The batch is all-or-nothing: a row the database refuses takes the earlier ones
  with it.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from typing import Any, override

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, FieldData
from ai.backend.manager.errors.repository import RepositoryIntegrityError
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import FieldUpserter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables

_OWNER_TYPE = EntityType("agent")


class _OwnerID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return _OWNER_TYPE


class FieldWriteTestRow(Base):
    __tablename__ = "field_write_test"
    __table_args__ = (sa.UniqueConstraint("owner_id", "slot_name", name="uq_field_write_test"),)

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, nullable=False)
    slot_name: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    capacity: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    used: Mapped[int] = mapped_column(sa.Integer, nullable=False)


@dataclass(frozen=True)
class _SlotData(FieldData):
    slot_name: str
    capacity: int
    used: int


@dataclass(frozen=True)
class _SlotUpserter(FieldUpserter[_OwnerID, FieldWriteTestRow, _SlotData]):
    """The shape the agent capacity sync writes: insert carries the used amount,
    a conflict updates the capacity alone."""

    slot_name: str
    capacity: int
    used: int = 0

    @override
    def row_class(self) -> type[FieldWriteTestRow]:
        return FieldWriteTestRow

    @override
    def index_elements(self) -> list[str]:
        return ["owner_id", "slot_name"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self, owner_id: _OwnerID) -> dict[str, Any]:
        return {
            "id": uuid.uuid4(),
            "owner_id": owner_id,
            "slot_name": self.slot_name,
            "capacity": self.capacity,
            "used": self.used,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"capacity": self.capacity}

    @override
    def to_data(self, row: FieldWriteTestRow) -> _SlotData:
        return _SlotData(slot_name=row.slot_name, capacity=row.capacity, used=row.used)


@dataclass(frozen=True)
class _RefusedUpserter(_SlotUpserter):
    """Leaves out a column the table requires, so the database refuses the row."""

    @override
    def build_insert_values(self, owner_id: _OwnerID) -> dict[str, Any]:
        values = super().build_insert_values(owner_id)
        del values["capacity"]
        return values


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, [FieldWriteTestRow]):
        yield database_connection


@pytest.fixture
def provider(database: ExtendedAsyncSAEngine) -> V2DBOpsProvider:
    return V2DBOpsProvider(database)


@pytest.fixture
def owner() -> _OwnerID:
    return _OwnerID(uuid.uuid4())


async def _rows(database: ExtendedAsyncSAEngine) -> list[FieldWriteTestRow]:
    async with database.begin_readonly_session() as sess:
        stmt = sa.select(FieldWriteTestRow).order_by(FieldWriteTestRow.slot_name)
        return list(await sess.scalars(stmt))


class TestAtomicUpsertFieldEntities:
    async def test_writes_every_row_under_the_owner(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, owner: _OwnerID
    ) -> None:
        async with provider.write_ops() as w:
            items = await w.atomic_upsert_field_entities(
                owner,
                [
                    _SlotUpserter(slot_name="cpu", capacity=4),
                    _SlotUpserter(slot_name="mem", capacity=8),
                ],
            )

        assert [(item.slot_name, item.capacity) for item in items] == [("cpu", 4), ("mem", 8)]
        assert [row.owner_id for row in await _rows(database)] == [owner, owner]

    async def test_conflict_takes_the_update_values_alone(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, owner: _OwnerID
    ) -> None:
        async with provider.write_ops() as w:
            await w.atomic_upsert_field_entities(
                owner, [_SlotUpserter(slot_name="cpu", capacity=4, used=3)]
            )
        async with provider.write_ops() as w:
            items = await w.atomic_upsert_field_entities(
                owner, [_SlotUpserter(slot_name="cpu", capacity=16, used=0)]
            )

        assert [(item.capacity, item.used) for item in items] == [(16, 3)]
        assert len(await _rows(database)) == 1

    async def test_empty_writes_nothing(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, owner: _OwnerID
    ) -> None:
        async with provider.write_ops() as w:
            assert await w.atomic_upsert_field_entities(owner, []) == []

        assert await _rows(database) == []

    async def test_is_all_or_nothing(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, owner: _OwnerID
    ) -> None:
        with pytest.raises(RepositoryIntegrityError):
            async with provider.write_ops() as w:
                await w.atomic_upsert_field_entities(
                    owner,
                    [
                        _SlotUpserter(slot_name="cpu", capacity=4),
                        _RefusedUpserter(slot_name="mem", capacity=8),
                    ],
                )

        assert await _rows(database) == []
