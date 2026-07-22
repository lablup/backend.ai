"""Agent data types for scheduling and agent selection."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from ai.backend.common.identifier.architecture import ArchName
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
    architecture: ArchName
    # Per-slot capacity/reserved/used from agent_resources
    resources: AgentResource
    # Number of containers currently running on the agent
    container_count: int


@dataclass
class AgentMeta:
    """Agent metadata plus normalized per-slot resources."""

    id: AgentId
    addr: str
    architecture: ArchName
    resources: AgentResource
    container_count: int

    def to_agent_info(self) -> AgentInfo:
        return AgentInfo(
            agent_id=self.id,
            agent_addr=self.addr,
            architecture=self.architecture,
            resources=self.resources,
            container_count=self.container_count,
        )


@dataclass
class ResourceGroupResource:
    """The resource group's schedulable agents and their per-slot aggregate."""

    agents: list[AgentMeta]
    # Per-slot capacity/reserved/used summed over the group's agents
    slots: Mapping[SlotName, SlotResource]

    @classmethod
    def from_agents(cls, agents: list[AgentMeta]) -> ResourceGroupResource:
        totals: dict[SlotName, SlotResource] = {}
        for agent in agents:
            for slot_name, resource in agent.resources.slots.items():
                current = totals.get(slot_name)
                if current is None:
                    totals[slot_name] = resource
                else:
                    totals[slot_name] = SlotResource(
                        capacity=current.capacity + resource.capacity,
                        reserved=current.reserved + resource.reserved,
                        used=current.used + resource.used,
                    )
        return cls(agents=agents, slots=totals)
