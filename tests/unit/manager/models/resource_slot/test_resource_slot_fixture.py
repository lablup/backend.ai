"""Regression tests for BA-4597: resource_slot_types fixture loading.

Verifies that:
1. populate_fixture correctly handles PydanticColumn (number_format) when
   loading resource_slot_types from JSON fixture data.
2. AgentResourceRow insertion succeeds after loading the fixture (FK satisfied).
"""

from __future__ import annotations

from decimal import Decimal

from ai.backend.manager.models.base import populate_fixture
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    NumberFormat,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class TestPopulateFixtureWithPydanticColumn:
    """Regression tests for populate_fixture handling PydanticColumn (BA-4597)."""

    async def test_populate_resource_slot_types_with_dict_number_format(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
    ) -> None:
        """populate_fixture must accept dict for PydanticColumn columns (number_format).

        Before the fix, passing a raw dict for a PydanticColumn caused
        AttributeError: 'dict' object has no attribute 'model_dump' because
        process_bind_param called .model_dump() on the dict.
        """
        fixture_data: dict[str, list[dict[str, object]]] = {
            "resource_slot_types": [
                {
                    "slot_name": "cpu",
                    "slot_type": "count",
                    "display_name": "CPU",
                    "description": "CPU",
                    "display_unit": "Core",
                    "display_icon": "cpu",
                    "number_format": {"binary": False, "round_length": 0},
                    "rank": 100,
                },
                {
                    "slot_name": "mem",
                    "slot_type": "bytes",
                    "display_name": "RAM",
                    "description": "Memory",
                    "display_unit": "GiB",
                    "display_icon": "ram",
                    "number_format": {"binary": True, "round_length": 0},
                    "rank": 200,
                },
            ]
        }

        # Should not raise AttributeError for dict number_format
        await populate_fixture(database_with_resource_slot_tables, fixture_data)

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            cpu = await db_sess.get(ResourceSlotTypeRow, "cpu")
            mem = await db_sess.get(ResourceSlotTypeRow, "mem")

        assert cpu is not None
        assert cpu.number_format == NumberFormat(binary=False, round_length=0)
        assert cpu.rank == 100

        assert mem is not None
        assert mem.number_format == NumberFormat(binary=True, round_length=0)

    async def test_agent_resource_insert_succeeds_after_fixture_load(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
        agent_id: str,
    ) -> None:
        """FK on agent_resources(slot_name) is satisfied after loading resource_slot_types fixture.

        Regression: before the fix, oneshot DB creation left resource_slot_types
        empty, causing ForeignKeyViolationError on agent heartbeat.
        """
        fixture_data: dict[str, list[dict[str, object]]] = {
            "resource_slot_types": [
                {
                    "slot_name": "cpu",
                    "slot_type": "count",
                    "number_format": {"binary": False, "round_length": 0},
                },
            ]
        }
        await populate_fixture(database_with_resource_slot_tables, fixture_data)

        # Inserting an agent_resource with slot_name='cpu' must succeed (FK satisfied)
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(
                AgentResourceRow(
                    agent_id=agent_id,
                    slot_name="cpu",
                    capacity=Decimal("4"),
                )
            )
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            row = await db_sess.get(AgentResourceRow, (agent_id, "cpu"))
        assert row is not None
        assert row.capacity == Decimal("4.000000")
