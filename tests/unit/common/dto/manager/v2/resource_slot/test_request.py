"""Tests for ai.backend.common.dto.manager.v2.resource_slot.request module."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.resource_slot.request import (
    CreateResourceSlotTypeInput,
    UpdateResourceSlotTypeInput,
)
from ai.backend.common.types import SlotTypes


class TestMaxPerSessionBounds:
    """max_per_session must fit the NUMERIC(24, 6) column."""

    @pytest.mark.parametrize(
        "value",
        [Decimal("1" * 19), Decimal("1.1234567")],
        ids=["too-many-integer-digits", "too-many-decimal-places"],
    )
    def test_create_rejects_out_of_range_value(self, value: Decimal) -> None:
        with pytest.raises(ValidationError):
            CreateResourceSlotTypeInput(
                slot_name="cpu", slot_type=SlotTypes.COUNT, max_per_session=value
            )

    @pytest.mark.parametrize(
        "value",
        [Decimal("1" * 19), Decimal("1.1234567")],
        ids=["too-many-integer-digits", "too-many-decimal-places"],
    )
    def test_update_rejects_out_of_range_value(self, value: Decimal) -> None:
        with pytest.raises(ValidationError):
            UpdateResourceSlotTypeInput(slot_name="cpu", max_per_session=value)

    def test_largest_column_value_is_accepted(self) -> None:
        value = Decimal("999999999999999999.999999")

        create = CreateResourceSlotTypeInput(
            slot_name="cpu", slot_type=SlotTypes.COUNT, max_per_session=value
        )
        update = UpdateResourceSlotTypeInput(slot_name="cpu", max_per_session=value)

        assert create.max_per_session == value
        assert update.max_per_session == value
