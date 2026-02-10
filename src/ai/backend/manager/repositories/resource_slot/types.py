"""Domain types for resource slot repository operations."""

from __future__ import annotations

from dataclasses import dataclass, field

from ai.backend.common.types import AgentId, SlotQuantity


@dataclass(frozen=True)
class AgentOccupiedSlots:
    """Per-agent occupied slot quantities."""

    agent_id: AgentId
    slots: list[SlotQuantity] = field(default_factory=list)
