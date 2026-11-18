"""Test fixtures for Resource Slot repository tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest

from ai.backend.manager.models.resource_slot.row import (
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.resource_slot.db_source.db_source import ResourceSlotDBSource
from ai.backend.testutils.db import with_tables


@pytest.fixture
async def database_with_resource_slot_tables(
    global_entity_ids: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine]:
    """Set up tables required for resource slot repository tests."""
    async with with_tables(
        global_entity_ids,
        [
            VirtualEntityRow,
            EntityMembershipRow,
            ScopeBindingRow,
            ResourceSlotTypeRow,
        ],
    ):
        yield global_entity_ids


@pytest.fixture
async def slot_types(
    database_with_resource_slot_tables: ExtendedAsyncSAEngine,
) -> AsyncGenerator[list[str]]:
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
