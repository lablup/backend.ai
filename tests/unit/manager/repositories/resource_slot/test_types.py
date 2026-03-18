"""Unit tests for resource_slot/types.py utility functions."""

from __future__ import annotations

from decimal import Decimal

from ai.backend.common.types import ResourceSlot, SlotName
from ai.backend.manager.repositories.resource_slot.types import resource_slot_to_quantities


class TestResourceSlotToQuantities:
    """Tests for resource_slot_to_quantities."""

    def test_preserves_zero_valued_slots(self) -> None:
        slot = ResourceSlot({SlotName("cpu"): Decimal(0), SlotName("mem"): Decimal(100)})
        result = resource_slot_to_quantities(slot)
        by_slot = {sq.slot_name: sq.quantity for sq in result}
        assert len(result) == 2
        assert by_slot["cpu"] == Decimal(0)
        assert by_slot["mem"] == Decimal(100)

    def test_filters_none_values(self) -> None:
        slot = ResourceSlot({SlotName("cpu"): None, SlotName("mem"): Decimal(512)})
        result = resource_slot_to_quantities(slot)
        by_slot = {sq.slot_name: sq.quantity for sq in result}
        assert "cpu" not in by_slot
        assert by_slot["mem"] == Decimal(512)

    def test_preserves_positive_values(self) -> None:
        slot = ResourceSlot({SlotName("cpu"): Decimal("4"), SlotName("mem"): Decimal("2048")})
        result = resource_slot_to_quantities(slot)
        by_slot = {sq.slot_name: sq.quantity for sq in result}
        assert len(result) == 2
        assert by_slot["cpu"] == Decimal("4")
        assert by_slot["mem"] == Decimal("2048")

    def test_empty_input(self) -> None:
        slot = ResourceSlot({})
        result = resource_slot_to_quantities(slot)
        assert result == []
