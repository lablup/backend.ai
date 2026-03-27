"""Test fixtures for Resource Slot repository tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest

from ai.backend.manager.models.resource_slot import (
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.resource_slot import ResourceSlotRepository
from ai.backend.manager.repositories.resource_slot.db_source import ResourceSlotDBSource
from ai.backend.testutils.db import with_tables


@pytest.fixture
async def database_with_resource_slot_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    """Set up tables required for resource slot repository tests."""
    async with with_tables(
        database_connection,
        [
            ResourceSlotTypeRow,
        ],
    ):
        yield database_connection


@pytest.fixture
async def slot_types(
    database_with_resource_slot_tables: ExtendedAsyncSAEngine,
) -> AsyncGenerator[list[str], None]:
    """Register resource slot types required for FK constraints."""
    names = ["cpu", "mem"]
    async with database_with_resource_slot_tables.begin_session() as db_sess:
        for name in names:
            db_sess.add(
                ResourceSlotTypeRow(
                    slot_name=name,
                    slot_type="count" if name == "cpu" else "bytes",
                    display_name=name.upper(),
                    rank=0 if name == "cpu" else 1,
                )
            )
    yield names


@pytest.fixture
async def db_source(
    database_with_resource_slot_tables: ExtendedAsyncSAEngine,
) -> ResourceSlotDBSource:
    return ResourceSlotDBSource(database_with_resource_slot_tables)


@pytest.fixture
async def resource_slot_repo(
    database_with_resource_slot_tables: ExtendedAsyncSAEngine,
) -> ResourceSlotRepository:
    # ResourceSlotRepository wraps db_source with resilience policies.
    # Uses the same DB engine as db_source — tables are already created by the outer fixture.
    return ResourceSlotRepository(database_with_resource_slot_tables)
