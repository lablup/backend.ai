"""Agent data types for scheduling and agent selection."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from ai.backend.common.types import AgentId, SlotName


@dataclass(frozen=True)
class SlotResource:
    """Capacity/reserved/used for a single agent slot (one ``agent_resources`` row)."""

    capacity: Decimal
    reserved: Decimal
    used: Decimal


@dataclass(frozen=True)
class AgentResource:
    """Per-agent slot resources from ``agent_resources``."""

    slots: Mapping[SlotName, SlotResource]


@dataclass
class AgentInfo:
    """Essential information about an agent for selection."""

    # Unique identifier of the agent
    agent_id: AgentId
    # Network address of the agent
    agent_addr: str
    # Architecture of the agent (e.g., "x86_64", "aarch64")
    architecture: str
    # Per-slot capacity/reserved/used from agent_resources
    resources: AgentResource
    # Scaling group the agent belongs to
    scaling_group: str
    # Number of containers currently running on the agent
    container_count: int
