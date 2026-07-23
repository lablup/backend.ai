"""Agent data types for scheduling and agent selection."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from functools import cached_property

from ai.backend.common.identifier.architecture import ArchName
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import AgentId, SessionId


@dataclass(frozen=True)
class SlotResource:
    """Capacity/reserved/used for a single agent slot (one ``agent_resources`` row)."""

    capacity: Decimal
    reserved: Decimal
    used: Decimal


@dataclass(frozen=True)
class AgentResource:
    """Per-agent slot resources from ``agent_resources``."""

    slots: Mapping[ResourceSlotName, SlotResource]


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


@dataclass(frozen=True)
class AgentLimit:
    """Per-agent cap enforced during selection."""

    # Maximum number of containers allowed per agent
    max_container_count: int | None


@dataclass
class ResourceGroupResource:
    """The resource group's schedulable agents plus per-agent observations.

    This is the value agent-selection trackers are built from; both the
    scheduling pass and the compute-schedule fitting check consume it.
    """

    agents: list[AgentMeta]
    # Sessions that previously failed per agent (retry deprioritization
    # hints from Valkey; empty for the fitting check)
    failed_sessions_by_agent: Mapping[AgentId, frozenset[SessionId]] = field(default_factory=dict)

    @cached_property
    def slots(self) -> Mapping[ResourceSlotName, SlotResource]:
        """Per-slot capacity/reserved/used summed over the agents.

        Computed on first use; only capacity-aware consumers (DRF) pay
        for the aggregation.
        """
        totals: dict[ResourceSlotName, SlotResource] = {}
        for agent in self.agents:
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
        return totals
