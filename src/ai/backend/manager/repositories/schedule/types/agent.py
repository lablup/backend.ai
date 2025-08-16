"""Agent related types."""

from dataclasses import dataclass

from ai.backend.common.types import AgentId, ResourceSlot


@dataclass
class AgentMeta:
    """Agent metadata without cached occupancy values."""

    id: AgentId
    addr: str
    architecture: str
    available_slots: ResourceSlot
    scaling_group: str
