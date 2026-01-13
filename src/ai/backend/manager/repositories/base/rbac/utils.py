from collections.abc import Collection
from typing import TypeVar

from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.manager.models.base import Base

TRow = TypeVar("TRow", bound=Base)


async def insert_on_conflict_do_nothing(
    db_sess: SASession,
    row: TRow,
) -> TRow:
    """Insert the given row, ignoring conflicts."""
    mapper = inspect(type(row))
    column_keys = {c.key for c in mapper.columns}
    values = {k: v for k, v in row.__dict__.items() if k in column_keys}
    stmt = pg_insert(type(row)).values(**values).on_conflict_do_nothing()
    await db_sess.execute(stmt)
    await db_sess.flush()
    return row


async def bulk_insert_on_conflict_do_nothing(
    db_sess: SASession,
    rows: Collection[TRow],
) -> None:
    """Insert the given rows, ignoring conflicts."""
    if not rows:
        return
    row_cls = type(next(iter(rows)))
    mapper = inspect(row_cls)
    column_keys = {c.key for c in mapper.columns}
    values_list = [{k: v for k, v in row.__dict__.items() if k in column_keys} for row in rows]
    stmt = pg_insert(row_cls).values(values_list).on_conflict_do_nothing()
    await db_sess.execute(stmt)
    await db_sess.flush()
