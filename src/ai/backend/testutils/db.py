from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from typing import Protocol

from sqlalchemy import Table, text
from sqlalchemy.ext.asyncio import AsyncEngine


class HasTable(Protocol):
    """Protocol for SQLAlchemy ORM model classes with __table__ attribute."""

    __table__: Table


@asynccontextmanager
async def with_tables(
    engine: AsyncEngine,
    orms: Sequence[type[HasTable]],
) -> AsyncGenerator[None, None]:
    """
    Create specified tables on enter, TRUNCATE CASCADE on exit.

    ORM classes should be ordered by FK dependencies (parents first).
    This context manager is designed for selective table loading in tests,
    allowing each test file to create only the tables it needs.

    Args:
        engine: SQLAlchemy async engine
        orms: Sequence of SQLAlchemy ORM model classes (ordered by FK dependencies)

    Example:
        async def test_something(database_connection):
            async with with_tables(database_connection, [DomainRow, UserRow, GroupRow]):
                ...
    """
    tables = [orm.__table__ for orm in orms]

    # Create tables
    async with engine.begin() as conn:
        for table in tables:
            await conn.run_sync(table.create, checkfirst=True)

    try:
        yield
    finally:
        # Cleanup via TRUNCATE CASCADE
        async with engine.begin() as conn:
            table_names = ", ".join(f'"{t.name}"' for t in tables)
            await conn.execute(text(f"TRUNCATE {table_names} CASCADE"))
