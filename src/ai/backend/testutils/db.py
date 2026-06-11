from __future__ import annotations

from collections.abc import AsyncGenerator, Callable, Sequence
from contextlib import asynccontextmanager
from typing import Any, Protocol, cast

from sqlalchemy import Table, text
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.sql.ddl import SchemaGenerator
from sqlalchemy.sql.schema import ForeignKeyConstraint


class HasTable(Protocol):
    """Protocol for SQLAlchemy ORM model classes with __table__ attribute."""

    __table__: Table


# Type alias for items that can be passed to with_tables
type TableOrORM = Table | type[HasTable]


def _make_subset_schema_generator(table_names: frozenset[str]) -> type[SchemaGenerator]:
    """
    Build a ``SchemaGenerator`` that skips deferred (``use_alter``) foreign keys
    pointing outside the requested table subset.

    ``MetaData.create_all(tables=...)`` still emits the deferred
    ``ALTER TABLE ... ADD CONSTRAINT`` for ``use_alter`` foreign keys even when the
    referenced table is absent from the subset, which fails with ``UndefinedTableError``
    (e.g. ``sessions.replica_id -> routings`` when a test loads ``sessions`` but not
    ``routings``). Suppressing only that standalone ``ALTER`` keeps selective table
    loading working without forcing every caller to pull in cycle-breaking tables.

    Inline foreign keys are rendered by the ``CREATE TABLE`` compiler, not this visitor,
    so they are unaffected; only standalone ``use_alter`` constraints flow through here.
    """

    class _SubsetSchemaGenerator(SchemaGenerator):
        def visit_foreign_key_constraint(self, constraint: ForeignKeyConstraint) -> None:
            elements = constraint.elements
            if elements:
                referred_table = elements[0].target_fullname.rsplit(".", 1)[0]
                if referred_table not in table_names:
                    return
            emit = cast(
                "Callable[[ForeignKeyConstraint], None]",
                super().visit_foreign_key_constraint,
            )
            emit(constraint)

    return _SubsetSchemaGenerator


def _create_tables_sync(conn: Any, tables: list[Table]) -> None:
    """
    Sync function to create tables, reusing ``create_all`` machinery (checkfirst,
    enum types, indexes) via a custom ``SchemaGenerator``.

    This handles circular FK dependencies via ``use_alter`` while dropping deferred
    foreign keys that reference tables outside the requested subset, so each test file
    can create only the tables it needs.
    """
    if not tables:
        return
    metadata = tables[0].metadata
    generator = _make_subset_schema_generator(frozenset(t.name for t in tables))
    conn._run_ddl_visitor(generator, metadata, checkfirst=True, tables=tables)


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
