from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from typing import Protocol, Union

from sqlalchemy import Table, text
from sqlalchemy.ext.asyncio import AsyncEngine


class HasTable(Protocol):
    """Protocol for SQLAlchemy ORM model classes with __table__ attribute."""

    __table__: Table


# Type alias for items that can be passed to with_tables
TableOrORM = Union[Table, type[HasTable]]


def _create_tables_sync(conn, tables: list[Table]) -> None:
    """
    Sync function to create tables using MetaData.create_all().

    This approach handles circular FK dependencies better than creating
    tables individually, as SQLAlchemy can sort and defer constraints.
    """
    # Use the shared metadata from the first table to create all tables
    # This handles circular FK dependencies via use_alter
    if tables:
        metadata = tables[0].metadata
        metadata.create_all(conn, tables=tables, checkfirst=True)


def _to_table(item: TableOrORM) -> Table:
    """Convert ORM class or Table to Table."""
    if isinstance(item, Table):
        return item
    return item.__table__


@asynccontextmanager
async def with_tables(
    engine: AsyncEngine,
    orms: Sequence[TableOrORM],
) -> AsyncGenerator[None, None]:
    """
    Create specified tables on enter, TRUNCATE CASCADE on exit.

    ORM classes should be ordered by FK dependencies (parents first).
    This context manager is designed for selective table loading in tests,
    allowing each test file to create only the tables it needs.

    Args:
        engine: SQLAlchemy async engine
        orms: Sequence of SQLAlchemy ORM model classes or Table objects
              (ordered by FK dependencies)

    Example:
        async def test_something(database_connection):
            async with with_tables(database_connection, [DomainRow, UserRow, GroupRow]):
                ...

        # With association tables:
        async with with_tables(database_connection, [
            DomainRow,
            ScalingGroupRow,
            sgroups_for_domains,  # raw Table object
        ]):
            ...
    """
    tables = [_to_table(item) for item in orms]

    # Create required PostgreSQL extensions and tables
    async with engine.begin() as conn:
        # Create uuid-ossp extension for uuid_generate_v4()
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.run_sync(_create_tables_sync, tables)

    try:
        yield
    finally:
        # Cleanup via TRUNCATE CASCADE
        async with engine.begin() as conn:
            table_names = ", ".join(f'"{t.name}"' for t in tables)
            await conn.execute(text(f"TRUNCATE {table_names} CASCADE"))
