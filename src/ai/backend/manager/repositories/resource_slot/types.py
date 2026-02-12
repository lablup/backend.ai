"""Domain types for resource slot repository operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from ai.backend.common.types import (
    AgentId,
    ResourceSlot,
    SlotQuantity,
)


@dataclass(frozen=True)
class AgentOccupiedSlots:
    """Per-agent occupied slot quantities."""

    agent_id: AgentId
    slots: list[SlotQuantity] = field(default_factory=list)


def resource_slot_to_quantities(slot: ResourceSlot) -> list[SlotQuantity]:
    """Convert a ResourceSlot dict to a list of SlotQuantity entries.

    Skips entries with falsy (zero/None) values.
    """
    return [SlotQuantity(slot_name=k, quantity=Decimal(str(v))) for k, v in slot.items() if v]
