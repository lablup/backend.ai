"""Fixtures serving the fixed rows and the search entry points to every scenario."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest

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
    ShelfRow,
    SpecRow,
)
from .shelf_search import ShelfSearches


@pytest.fixture
async def shelf_db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
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
