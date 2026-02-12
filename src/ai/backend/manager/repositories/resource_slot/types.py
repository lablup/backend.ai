"""Domain types for resource slot repository operations."""

from __future__ import annotations

import json
from decimal import Decimal

from ai.backend.common.types import (
    ResourceSlot,
    SlotQuantity,
)


def resource_slot_to_quantities(slot: ResourceSlot) -> list[SlotQuantity]:
    """Convert a ResourceSlot dict to a list of SlotQuantity entries.

    Skips entries with falsy (zero/None) values.
    """
    return [SlotQuantity(slot_name=k, quantity=Decimal(str(v))) for k, v in slot.items() if v]


def add_quantities(a: list[SlotQuantity], b: list[SlotQuantity]) -> list[SlotQuantity]:
    """Element-wise addition preserving a's order. Slots only in b are appended."""
    b_map = {sq.slot_name: sq.quantity for sq in b}
    a_names = {sq.slot_name for sq in a}
    result = [
        SlotQuantity(sq.slot_name, sq.quantity + b_map.get(sq.slot_name, Decimal(0))) for sq in a
    ]
    result.extend(sq for sq in b if sq.slot_name not in a_names)
    return result


def subtract_quantities(a: list[SlotQuantity], b: list[SlotQuantity]) -> list[SlotQuantity]:
    """Element-wise subtraction (a - b) preserving a's order."""
    b_map = {sq.slot_name: sq.quantity for sq in b}
    return [
        SlotQuantity(sq.slot_name, sq.quantity - b_map.get(sq.slot_name, Decimal(0))) for sq in a
    ]


def min_quantities(*lists: list[SlotQuantity]) -> list[SlotQuantity]:
    """Element-wise minimum across multiple lists, using first list's order."""
    if not lists:
        return []
    first = lists[0]
    maps = [{sq.slot_name: sq.quantity for sq in lst} for lst in lists[1:]]
    return [
        SlotQuantity(
            sq.slot_name,
            min(sq.quantity, *(m.get(sq.slot_name, sq.quantity) for m in maps)),
        )
        for sq in first
    ]


def quantities_ge(a: list[SlotQuantity], b: list[SlotQuantity]) -> bool:
    """Check if every slot in b has a corresponding slot in a with >= quantity."""
    a_map = {sq.slot_name: sq.quantity for sq in a}
    return all(a_map.get(sq.slot_name, Decimal(0)) >= sq.quantity for sq in b)


def get_quantity(
    quantities: list[SlotQuantity], slot_name: str, default: Decimal = Decimal(0)
) -> Decimal:
    """Get quantity for a specific slot name."""
    for sq in quantities:
        if sq.slot_name == slot_name:
            return sq.quantity
    return default


def quantities_to_json(quantities: list[SlotQuantity]) -> str:
    """Serialize list[SlotQuantity] to JSON string (order preserved)."""
    return json.dumps({sq.slot_name: str(sq.quantity) for sq in quantities})


def quantities_from_json(data: str) -> list[SlotQuantity]:
    """Deserialize JSON string to list[SlotQuantity]."""
    parsed = json.loads(data)
    return [SlotQuantity(slot_name=k, quantity=Decimal(v)) for k, v in parsed.items()]


def accumulate_to_quantities(
    accum: dict[str, Decimal],
    rank_map: dict[str, int],
) -> list[SlotQuantity]:
    """Convert dict-based accumulation to rank-sorted list[SlotQuantity]."""
    return sorted(
        [SlotQuantity(k, v) for k, v in accum.items()],
        key=lambda sq: rank_map.get(sq.slot_name, 9999),
    )
