"""Integration tests for ResourceSlotDBSource with real database."""

from __future__ import annotations

import pytest

from ai.backend.manager.errors.resource_slot import (
    ResourceSlotTypeNotFound,
)
from ai.backend.manager.repositories.resource_slot.db_source import ResourceSlotDBSource


class TestSlotTypes:
    """Tests for resource_slot_types read operations."""

    async def test_all_slot_types(
        self,
        db_source: ResourceSlotDBSource,
        slot_types: list[str],
    ) -> None:
        types = await db_source.all_slot_types()
        assert len(types) == 2
        names = [t.slot_name for t in types]
        assert "cpu" in names
        assert "mem" in names

    async def test_get_slot_type_found(
        self,
        db_source: ResourceSlotDBSource,
        slot_types: list[str],
    ) -> None:
        slot_type = await db_source.get_slot_type("cpu")
        assert slot_type.slot_name == "cpu"
        assert slot_type.slot_type == "count"

    async def test_get_slot_type_not_found(
        self,
        db_source: ResourceSlotDBSource,
        slot_types: list[str],
    ) -> None:
        with pytest.raises(ResourceSlotTypeNotFound):
            await db_source.get_slot_type("nonexistent")
