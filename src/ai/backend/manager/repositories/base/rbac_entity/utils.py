from collections.abc import Collection
from typing import TypeVar

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.manager.models.base import Base

TRow = TypeVar("TRow", bound=Base)


async def insert_on_conflict_do_nothing(
    db_sess: SASession,
    row: TRow,
) -> TRow:
    """Insert the given row, ignoring conflicts."""
    # TODO: Use SQLAlchemy 2.0 native upsert when available

    stmt = pg_insert(type(row)).values(**row.__dict__).on_conflict_do_nothing()
    await db_sess.execute(stmt)
    await db_sess.flush()
    return row


async def bulk_insert_on_conflict_do_nothing(
    db_sess: SASession,
    rows: Collection[TRow],
) -> None:
    """Insert the given row, ignoring conflicts."""
    # TODO: Use SQLAlchemy 2.0 native upsert when available

    if not rows:
        return
    row_cls = type(next(iter(rows)))
    stmt = pg_insert(row_cls).values([row.__dict__ for row in rows]).on_conflict_do_nothing()
    await db_sess.execute(stmt)
    await db_sess.flush()
