"""``ReconcileWriteOps.batch_update_returning_previous`` against a real database.

What these tests pin down:

- Each updated row comes back as it was before the update and as the update left it.
- Only the rows the spec's conditions select are written and returned.
- A spec selecting no row writes nothing and returns an empty list.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataBatchUpdater
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.ops.v2.reconciler.write import UpdatedRowChange
from ai.backend.testutils.db import with_tables


class BatchUpdateReturningPreviousTestRow(Base):
    __tablename__ = "test_v2_batch_update_returning_previous"
    __table_args__ = ({"extend_existing": True},)

    id: Mapped[UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    status: Mapped[str] = mapped_column(sa.String(32), nullable=False)


@dataclass(frozen=True)
class _RowData:
    id: UUID
    status: str


@dataclass(frozen=True)
class _StatusBatchUpdater(DataBatchUpdater[BatchUpdateReturningPreviousTestRow, _RowData]):
    row_ids: Sequence[UUID]
    to_status: str

    @property
    @override
    def row_class(self) -> type[BatchUpdateReturningPreviousTestRow]:
        return BatchUpdateReturningPreviousTestRow

    @override
    def conditions(self) -> list[QueryCondition]:
        return [lambda: BatchUpdateReturningPreviousTestRow.id.in_(self.row_ids)]

    @override
    def build_values(self) -> dict[str, Any]:
        return {"status": self.to_status}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: BatchUpdateReturningPreviousTestRow) -> _RowData:
        return _RowData(id=row.id, status=row.status)


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine]:
    async with with_tables(database_connection, [BatchUpdateReturningPreviousTestRow]):
        yield database_connection


@pytest.fixture
def ops(database: ExtendedAsyncSAEngine) -> ReconcileOpsProvider:
    return ReconcileOpsProvider(database)


async def _insert(database: ExtendedAsyncSAEngine, status: str) -> UUID:
    row_id = uuid4()
    async with database.begin_session() as sess:
        sess.add(BatchUpdateReturningPreviousTestRow(id=row_id, status=status))
    return row_id


async def _status(database: ExtendedAsyncSAEngine, row_id: UUID) -> str:
    async with database.begin_readonly_session() as sess:
        row = await sess.get(BatchUpdateReturningPreviousTestRow, row_id)
    assert row is not None
    return row.status


class TestBatchUpdateReturningPrevious:
    async def test_returns_each_row_before_and_after(
        self, database: ExtendedAsyncSAEngine, ops: ReconcileOpsProvider
    ) -> None:
        pending = await _insert(database, "pending")
        running = await _insert(database, "running")

        async with ops.write_ops() as w:
            changes = await w.batch_update_returning_previous(
                _StatusBatchUpdater(row_ids=[pending, running], to_status="terminated")
            )

        assert sorted(changes, key=lambda change: change.current.id) == sorted(
            [
                UpdatedRowChange(
                    previous=_RowData(id=pending, status="pending"),
                    current=_RowData(id=pending, status="terminated"),
                ),
                UpdatedRowChange(
                    previous=_RowData(id=running, status="running"),
                    current=_RowData(id=running, status="terminated"),
                ),
            ],
            key=lambda change: change.current.id,
        )

    async def test_unselected_rows_are_left_untouched(
        self, database: ExtendedAsyncSAEngine, ops: ReconcileOpsProvider
    ) -> None:
        selected = await _insert(database, "pending")
        other = await _insert(database, "pending")

        async with ops.write_ops() as w:
            changes = await w.batch_update_returning_previous(
                _StatusBatchUpdater(row_ids=[selected], to_status="running")
            )

        assert [change.current.id for change in changes] == [selected]
        assert await _status(database, other) == "pending"

    async def test_no_selected_row_returns_empty(
        self, database: ExtendedAsyncSAEngine, ops: ReconcileOpsProvider
    ) -> None:
        async with ops.write_ops() as w:
            changes = await w.batch_update_returning_previous(
                _StatusBatchUpdater(row_ids=[uuid4()], to_status="running")
            )

        assert changes == []
