"""Agent data types for scheduling and agent selection."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.types import AgentId, ResourceSlot


@dataclass
class AgentInfo:
    """Essential information about an agent for selection."""

    # Unique identifier of the agent
    agent_id: AgentId
    # Network address of the agent
    agent_addr: str
    # Architecture of the agent (e.g., "x86_64", "aarch64")
    architecture: str
    # Available resource slots on the agent
    available_slots: ResourceSlot
    # Currently occupied resource slots
    occupied_slots: ResourceSlot
    # Scaling group the agent belongs to
    scaling_group: str
    # Number of containers currently running on the agent
    container_count: int
