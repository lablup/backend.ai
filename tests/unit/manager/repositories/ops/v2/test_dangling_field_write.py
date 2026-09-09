"""Sidecar upsert of the v2 write ops, against a real database.

What these tests pin down:

- A row is written with no owner named and nothing joined to it.
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

from ai.backend.common.data.entity.types import FieldData
from ai.backend.manager.errors.repository import RepositoryIntegrityError
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import DanglingFieldUpserter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables


class DanglingUpsertTestRow(Base):
    __tablename__ = "dangling_upsert_test"
    __table_args__ = (sa.UniqueConstraint("scope_id", "subject", name="uq_dangling_upsert_test"),)

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    scope_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, nullable=False)
    subject: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    weight: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    factor: Mapped[int] = mapped_column(sa.Integer, nullable=False)


@dataclass(frozen=True)
class _ShareData(FieldData):
    subject: str
    weight: int
    factor: int


@dataclass(frozen=True)
class _ShareUpserter(DanglingFieldUpserter[DanglingUpsertTestRow, _ShareData]):
    """The shape a fair share write has: the scope and the subject are values the row
    records, and a conflict retunes the weight alone."""

    scope_id: uuid.UUID
    subject: str
    weight: int
    factor: int = 0

    @override
    def row_class(self) -> type[DanglingUpsertTestRow]:
        return DanglingUpsertTestRow

    @override
    def index_elements(self) -> list[str]:
        return ["scope_id", "subject"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "id": uuid.uuid4(),
            "scope_id": self.scope_id,
            "subject": self.subject,
            "weight": self.weight,
            "factor": self.factor,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"weight": self.weight}

    @override
    def to_data(self, row: DanglingUpsertTestRow) -> _ShareData:
        return _ShareData(subject=row.subject, weight=row.weight, factor=row.factor)


@dataclass(frozen=True)
class _RefusedUpserter(_ShareUpserter):
    """Leaves out a column the table requires, so the database refuses the row."""

    @override
    def build_insert_values(self) -> dict[str, Any]:
        values = super().build_insert_values()
        del values["weight"]
        return values


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, [DanglingUpsertTestRow]):
        yield database_connection


@pytest.fixture
def provider(database: ExtendedAsyncSAEngine) -> V2DBOpsProvider:
    return V2DBOpsProvider(database)


@pytest.fixture
def scope() -> uuid.UUID:
    return uuid.uuid4()


async def _rows(database: ExtendedAsyncSAEngine) -> list[DanglingUpsertTestRow]:
    async with database.begin_readonly_session() as sess:
        stmt = sa.select(DanglingUpsertTestRow).order_by(DanglingUpsertTestRow.subject)
        return list(await sess.scalars(stmt))


class TestUpsertDanglingField:
    async def test_writes_the_row_with_no_owner(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, scope: uuid.UUID
    ) -> None:
        async with provider.write_ops() as w:
            data = await w.upsert_dangling_field(
                _ShareUpserter(scope_id=scope, subject="cpu", weight=2)
            )

        assert (data.subject, data.weight) == ("cpu", 2)
        assert [row.scope_id for row in await _rows(database)] == [scope]

    async def test_conflict_takes_the_update_values_alone(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, scope: uuid.UUID
    ) -> None:
        async with provider.write_ops() as w:
            await w.upsert_dangling_field(
                _ShareUpserter(scope_id=scope, subject="cpu", weight=2, factor=7)
            )
        async with provider.write_ops() as w:
            data = await w.upsert_dangling_field(
                _ShareUpserter(scope_id=scope, subject="cpu", weight=5, factor=0)
            )

        assert (data.weight, data.factor) == (5, 7)
        assert len(await _rows(database)) == 1


class TestAtomicUpsertDanglingFields:
    async def test_writes_every_row(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, scope: uuid.UUID
    ) -> None:
        async with provider.write_ops() as w:
            items = await w.atomic_upsert_dangling_fields([
                _ShareUpserter(scope_id=scope, subject="cpu", weight=2),
                _ShareUpserter(scope_id=scope, subject="mem", weight=4),
            ])

        assert [(item.subject, item.weight) for item in items] == [("cpu", 2), ("mem", 4)]
        assert len(await _rows(database)) == 2

    async def test_empty_writes_nothing(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider
    ) -> None:
        async with provider.write_ops() as w:
            assert await w.atomic_upsert_dangling_fields([]) == []

        assert await _rows(database) == []

    async def test_is_all_or_nothing(
        self, database: ExtendedAsyncSAEngine, provider: V2DBOpsProvider, scope: uuid.UUID
    ) -> None:
        with pytest.raises(RepositoryIntegrityError):
            async with provider.write_ops() as w:
                await w.atomic_upsert_dangling_fields([
                    _ShareUpserter(scope_id=scope, subject="cpu", weight=2),
                    _RefusedUpserter(scope_id=scope, subject="mem", weight=4),
                ])

        assert await _rows(database) == []
