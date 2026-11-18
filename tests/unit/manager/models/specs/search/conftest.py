"""Fixtures serving the fixed rows and the search entry points to every scenario."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Iterator
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables

from .shelf_fixtures import Seeded, seed_shelves
from .shelf_rows import (
    BoxRow,
    CartLineRow,
    CartRow,
    CategoryRow,
    ShelfData,
    ShelfItemRow,
    ShelfPartialData,
    ShelfRow,
    SpecRow,
)
from .shelf_search import ShelfSearches


@pytest.fixture
async def shelf_db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine]:
    async with with_tables(
        database_connection,
        [CategoryRow, ShelfRow, SpecRow, BoxRow, ShelfItemRow, CartRow, CartLineRow],
    ):
        yield database_connection


@pytest.fixture
async def seeded(shelf_db: ExtendedAsyncSAEngine) -> Seeded:
    return await seed_shelves(shelf_db)


@pytest.fixture
def searches(shelf_db: ExtendedAsyncSAEngine) -> ShelfSearches:
    return ShelfSearches(OpsRepository[ShelfData](V2DBOpsProvider(shelf_db)))


@pytest.fixture
def partial_reads(shelf_db: ExtendedAsyncSAEngine) -> OpsRepository[ShelfPartialData]:
    return OpsRepository[ShelfPartialData](V2DBOpsProvider(shelf_db))


@pytest.fixture
def shelf_select_lists(shelf_db: ExtendedAsyncSAEngine) -> Iterator[list[list[str]]]:
    """The SELECT list of each statement reading ``test_search_shelf`` columns, in run order."""
    select_lists: list[list[str]] = []

    def record(_conn: Any, _cursor: Any, statement: str, *_args: Any) -> None:
        if statement.startswith("SELECT test_search_shelf."):
            columns = statement[len("SELECT ") : statement.index("\nFROM ")]
            select_lists.append([column.strip() for column in columns.split(",")])

    sa.event.listen(shelf_db.sync_engine, "before_cursor_execute", record)
    try:
        yield select_lists
    finally:
        sa.event.remove(shelf_db.sync_engine, "before_cursor_execute", record)
