"""The guarded update of the v2 write specs runs against a real database.

What these tests pin down:

- The id names exactly one row: a guarded update never reaches a second row, even
  when the guard alone would match several.
- The guard is a precondition, not a selection. A row failing it is left untouched
  and the operation reports that it wrote nothing.
- Guard and write travel in one statement, so nothing can change the row between
  the check and the write.
- Both misses answer ``None`` — a row that is gone and a row the guard refused are
  the same answer, which is what the single return value means.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute, Mapped, mapped_column

from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import GuardedDataUpdater
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables


class GuardedUpdateTestRow(Base):
    __tablename__ = "test_v2_guarded_update"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    status: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    note: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)


@dataclass(frozen=True)
class _RowData:
    id: UUID
    status: str
    note: str | None


_TERMINAL = "terminal"


@dataclass
class _StatusUpdater(GuardedDataUpdater[GuardedUpdateTestRow, _RowData]):
    """Writes a row's status unless it already reached the terminal one."""

    row_id: UUID
    status: str
    note: str | None = None

    @property
    @override
    def row_class(self) -> type[GuardedUpdateTestRow]:
        return GuardedUpdateTestRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return GuardedUpdateTestRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.row_id

    @override
    def guard_conditions(self) -> list[QueryCondition]:
        return [lambda: GuardedUpdateTestRow.status != _TERMINAL]

    @override
    def build_values(self) -> dict[str, Any]:
        return {"status": self.status, "note": self.note}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: GuardedUpdateTestRow) -> _RowData:
        return _RowData(id=row.id, status=row.status, note=row.note)


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, [GuardedUpdateTestRow]):
        yield database_connection


@pytest.fixture
def ops(database: ExtendedAsyncSAEngine) -> V2DBOpsProvider:
    return V2DBOpsProvider(database)


async def _insert(database: ExtendedAsyncSAEngine, status: str) -> UUID:
    row_id = uuid4()
    async with database.begin_session() as sess:
        sess.add(GuardedUpdateTestRow(id=row_id, status=status, note=None))
    return row_id


async def _read(database: ExtendedAsyncSAEngine, row_id: UUID) -> _RowData:
    async with database.begin_readonly_session() as sess:
        row = await sess.get(GuardedUpdateTestRow, row_id)
        assert row is not None
        return _RowData(id=row.id, status=row.status, note=row.note)


class TestGuardedUpdate:
    async def test_writes_and_returns_the_row_when_the_guard_holds(
        self, database: ExtendedAsyncSAEngine, ops: V2DBOpsProvider
    ) -> None:
        row_id = await _insert(database, "alive")

        async with ops.write_ops() as w:
            written = await w.update_guarded_data(
                _StatusUpdater(row_id=row_id, status=_TERMINAL, note="gone")
            )

        assert written == _RowData(id=row_id, status=_TERMINAL, note="gone")
        assert await _read(database, row_id) == written

    async def test_refuses_and_leaves_the_row_untouched_when_the_guard_fails(
        self, database: ExtendedAsyncSAEngine, ops: V2DBOpsProvider
    ) -> None:
        row_id = await _insert(database, _TERMINAL)

        async with ops.write_ops() as w:
            written = await w.update_guarded_data(
                _StatusUpdater(row_id=row_id, status="alive", note="revived")
            )

        assert written is None
        assert await _read(database, row_id) == _RowData(id=row_id, status=_TERMINAL, note=None)

    async def test_answers_none_for_an_id_that_names_no_row(self, ops: V2DBOpsProvider) -> None:
        async with ops.write_ops() as w:
            written = await w.update_guarded_data(_StatusUpdater(row_id=uuid4(), status="alive"))

        assert written is None

    async def test_reaches_only_the_row_the_id_names(
        self, database: ExtendedAsyncSAEngine, ops: V2DBOpsProvider
    ) -> None:
        """The guard alone matches both rows; the id is what keeps the write to one."""
        target = await _insert(database, "alive")
        bystander = await _insert(database, "alive")

        async with ops.write_ops() as w:
            await w.update_guarded_data(_StatusUpdater(row_id=target, status=_TERMINAL))

        assert (await _read(database, target)).status == _TERMINAL
        assert (await _read(database, bystander)).status == "alive"

    async def test_only_one_of_two_racing_writes_lands(
        self, database: ExtendedAsyncSAEngine, ops: V2DBOpsProvider
    ) -> None:
        """Guard and write share one statement, so the second finds the guard closed."""
        row_id = await _insert(database, "alive")

        async def write(note: str) -> _RowData | None:
            async with ops.write_ops() as w:
                return await w.update_guarded_data(
                    _StatusUpdater(row_id=row_id, status=_TERMINAL, note=note)
                )

        results = await asyncio.gather(write("first"), write("second"))

        written = [r for r in results if r is not None]
        assert len(written) == 1
        assert (await _read(database, row_id)).note == written[0].note
