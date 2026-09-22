"""The guard an update or a purge spec carries runs against a real database.

What these tests pin down:

- The id names exactly one row: a guarded write never reaches a second row, even
  when the guard alone would match several.
- The guard is a precondition, not a selection. A row failing it is left untouched
  and the write answers with the error the failing check declared.
- Guard and write travel in one statement, so nothing can change the row between
  the check and the write.
- A row that is gone answers ``None``; a row that refused raises. The two misses are
  told apart by one read of the named row after the write touched nothing.
- With several guards, the first failing one answers.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from aiohttp import web
from sqlalchemy.orm import InstrumentedAttribute, Mapped, mapped_column

from ai.backend.common.data.entity.types import (
    DanglingFieldType,
    EntityIdentifier,
    EntityType,
    FieldData,
    FieldIdentifier,
    FieldType,
    RuntimeEntityID,
)
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.specs.purger import GuardedFieldPurger
from ai.backend.manager.models.specs.types import ConflictCheck, GuardCheck, IntegrityErrorCheck
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
class _RowData(FieldData):
    id: UUID
    status: str
    note: str | None


class _Refusal(BackendAIError, web.HTTPConflict):
    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.CONFLICT,
        )


class _Terminal(_Refusal):
    error_type = "https://api.backend.ai/probs/test-terminal"
    error_title = "Row is terminal."


class _Pinned(_Refusal):
    error_type = "https://api.backend.ai/probs/test-pinned"
    error_title = "Row is pinned."


_TERMINAL = "terminal"
_PINNED_NOTE = "pinned"


class _RowEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "guarded_row"

    @override
    @classmethod
    def description(cls) -> str:
        return "A row the guarded write tests operate on."


class _RowFieldType(DanglingFieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "guarded_row_field"

    @override
    @classmethod
    def description(cls) -> str:
        return "The same row reached as a field row."


class _RowFieldID(FieldIdentifier):
    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return _RowFieldType()


@dataclass
class _StatusUpdater(GuardedDataUpdater[GuardedUpdateTestRow, _RowData]):
    """Writes a row's status unless it already reached the terminal one, or is pinned."""

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
    def target_id_value(self) -> EntityIdentifier:
        return RuntimeEntityID(_RowEntityType(), self.row_id)

    @override
    def guard_checks(self) -> Sequence[GuardCheck]:
        return (
            GuardCheck(
                condition=lambda: GuardedUpdateTestRow.status != _TERMINAL,
                error=_Terminal(),
            ),
            GuardCheck(
                condition=lambda: sa.or_(
                    GuardedUpdateTestRow.note.is_(None),
                    GuardedUpdateTestRow.note != _PINNED_NOTE,
                ),
                error=_Pinned(),
            ),
        )

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


@dataclass
class _NonTerminalPurger(GuardedFieldPurger[GuardedUpdateTestRow, _RowData]):
    """Removes a row unless it reached the terminal status."""

    row_id: UUID

    @override
    def row_class(self) -> type[GuardedUpdateTestRow]:
        return GuardedUpdateTestRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return GuardedUpdateTestRow.id

    @override
    def target_id_value(self) -> FieldIdentifier:
        return _RowFieldID(self.row_id)

    @override
    def guard_checks(self) -> Sequence[GuardCheck]:
        return (
            GuardCheck(
                condition=lambda: GuardedUpdateTestRow.status != _TERMINAL,
                error=_Terminal(),
            ),
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
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


async def _insert(database: ExtendedAsyncSAEngine, status: str, note: str | None = None) -> UUID:
    row_id = uuid4()
    async with database.begin_session() as sess:
        sess.add(GuardedUpdateTestRow(id=row_id, status=status, note=note))
    return row_id


async def _read(database: ExtendedAsyncSAEngine, row_id: UUID) -> _RowData | None:
    async with database.begin_readonly_session() as sess:
        row = await sess.get(GuardedUpdateTestRow, row_id)
        if row is None:
            return None
        return _RowData(id=row.id, status=row.status, note=row.note)


class TestGuardedUpdate:
    async def test_writes_and_returns_the_row_when_the_guard_holds(
        self, database: ExtendedAsyncSAEngine, ops: V2DBOpsProvider
    ) -> None:
        row_id = await _insert(database, "alive")

        async with ops.write_ops() as w:
            written = await w.update_data(
                _StatusUpdater(row_id=row_id, status=_TERMINAL, note="gone")
            )

        assert written == _RowData(id=row_id, status=_TERMINAL, note="gone")
        assert await _read(database, row_id) == written

    async def test_raises_the_declared_error_and_leaves_the_row_untouched(
        self, database: ExtendedAsyncSAEngine, ops: V2DBOpsProvider
    ) -> None:
        row_id = await _insert(database, _TERMINAL)

        with pytest.raises(_Terminal):
            async with ops.write_ops() as w:
                await w.update_data(_StatusUpdater(row_id=row_id, status="alive", note="revived"))

        assert await _read(database, row_id) == _RowData(id=row_id, status=_TERMINAL, note=None)

    async def test_the_first_failing_guard_answers(
        self, database: ExtendedAsyncSAEngine, ops: V2DBOpsProvider
    ) -> None:
        pinned = await _insert(database, "alive", note=_PINNED_NOTE)
        both = await _insert(database, _TERMINAL, note=_PINNED_NOTE)

        with pytest.raises(_Pinned):
            async with ops.write_ops() as w:
                await w.update_data(_StatusUpdater(row_id=pinned, status=_TERMINAL))
        with pytest.raises(_Terminal):
            async with ops.write_ops() as w:
                await w.update_data(_StatusUpdater(row_id=both, status="alive"))

    async def test_answers_none_for_an_id_that_names_no_row(self, ops: V2DBOpsProvider) -> None:
        async with ops.write_ops() as w:
            written = await w.update_data(_StatusUpdater(row_id=uuid4(), status="alive"))

        assert written is None

    async def test_reaches_only_the_row_the_id_names(
        self, database: ExtendedAsyncSAEngine, ops: V2DBOpsProvider
    ) -> None:
        """The guard alone matches both rows; the id is what keeps the write to one."""
        target = await _insert(database, "alive")
        bystander = await _insert(database, "alive")

        async with ops.write_ops() as w:
            await w.update_data(_StatusUpdater(row_id=target, status=_TERMINAL))

        target_row = await _read(database, target)
        bystander_row = await _read(database, bystander)
        assert target_row is not None and target_row.status == _TERMINAL
        assert bystander_row is not None and bystander_row.status == "alive"

    async def test_only_one_of_two_racing_writes_lands(
        self, database: ExtendedAsyncSAEngine, ops: V2DBOpsProvider
    ) -> None:
        """Guard and write share one statement, so the second finds the guard closed."""
        row_id = await _insert(database, "alive")

        async def write(note: str) -> _RowData | None:
            async with ops.write_ops() as w:
                return await w.update_data(
                    _StatusUpdater(row_id=row_id, status=_TERMINAL, note=note)
                )

        results = await asyncio.gather(write("first"), write("second"), return_exceptions=True)

        written = [r for r in results if isinstance(r, _RowData)]
        refused = [r for r in results if isinstance(r, _Terminal)]
        assert len(written) == 1
        assert len(refused) == 1
        row = await _read(database, row_id)
        assert row is not None and row.note == written[0].note


class TestGuardedPurge:
    async def test_removes_and_returns_the_row_when_the_guard_holds(
        self, database: ExtendedAsyncSAEngine, ops: V2DBOpsProvider
    ) -> None:
        row_id = await _insert(database, "alive")

        async with ops.write_ops() as w:
            removed = await w.purge_field_entity(_NonTerminalPurger(row_id=row_id))

        assert removed == _RowData(id=row_id, status="alive", note=None)
        assert await _read(database, row_id) is None

    async def test_raises_the_declared_error_and_keeps_the_row(
        self, database: ExtendedAsyncSAEngine, ops: V2DBOpsProvider
    ) -> None:
        row_id = await _insert(database, _TERMINAL)

        with pytest.raises(_Terminal):
            async with ops.write_ops() as w:
                await w.purge_field_entity(_NonTerminalPurger(row_id=row_id))

        assert await _read(database, row_id) == _RowData(id=row_id, status=_TERMINAL, note=None)

    async def test_answers_none_for_an_id_that_names_no_row(self, ops: V2DBOpsProvider) -> None:
        async with ops.write_ops() as w:
            removed = await w.purge_field_entity(_NonTerminalPurger(row_id=uuid4()))

        assert removed is None
