"""Batch-scoped agent state tracking for agent selection.

``build_agent_trackers`` is the single construction point shared by the
scheduling pass and the compute-schedule fitting check.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from ai.backend.common.types import SessionId, SlotName
from ai.backend.manager.views.sokovan.agent import AgentInfo, ResourceGroupResource
from ai.backend.manager.views.sokovan.workload import ResourceRequest


@dataclass
class AgentStateTracker:
    """Tracks in-batch allocations for one agent during a scheduling pass.

    The agent observation (``AgentInfo``) is immutable; every in-batch state
    change lives here. ``committed`` holds allocations from earlier sessions
    of this pass, ``pending`` holds the session currently being placed —
    the all-or-nothing per-session semantics come from commit()/rollback().
    """

    original_agent: AgentInfo
    # Sessions that previously failed on this agent (retry deprioritization hint)
    failed_session_ids: frozenset[SessionId] = frozenset()
    committed_slots: dict[SlotName, Decimal] = field(default_factory=dict)
    committed_containers: int = 0
    pending_slots: dict[SlotName, Decimal] = field(default_factory=dict)
    pending_containers: int = 0

    def remaining_slots(self) -> dict[SlotName, Decimal]:
        """Per-slot remaining = capacity - reserved - used - in-batch allocations."""
        remaining: dict[SlotName, Decimal] = {}
        for slot_name, resource in self.original_agent.resources.slots.items():
            remaining[slot_name] = (
                resource.capacity
                - resource.reserved
                - resource.used
                - self.committed_slots.get(slot_name, Decimal(0))
                - self.pending_slots.get(slot_name, Decimal(0))
            )
        return remaining

    def current_container_count(self) -> int:
        """Get current container count including in-batch allocations."""
        return (
            self.original_agent.container_count
            + self.committed_containers
            + self.pending_containers
        )

    def apply_diff(self, request: ResourceRequest, containers: int) -> None:
        """Apply an in-flight allocation of the session being placed."""
        for slot_name, amount in request.slots.items():
            self.pending_slots[slot_name] = self.pending_slots.get(slot_name, Decimal(0)) + amount
        self.pending_containers += containers

    def commit(self) -> None:
        """Fold the in-flight allocation into the batch state (session placed)."""
        for slot_name, amount in self.pending_slots.items():
            self.committed_slots[slot_name] = (
                self.committed_slots.get(slot_name, Decimal(0)) + amount
            )
        self.committed_containers += self.pending_containers
        self.rollback()

    def rollback(self) -> None:
        """Discard the in-flight allocation (session placement failed)."""
        self.pending_slots = {}
        self.pending_containers = 0


def build_agent_trackers(resources: ResourceGroupResource) -> list[AgentStateTracker]:
    """Build the per-agent selection trackers from the observed resources."""
    return [
        AgentStateTracker(
            original_agent=agent.to_agent_info(),
            failed_session_ids=frozenset(
                resources.failed_sessions_by_agent.get(agent.id, frozenset())
            ),
        )
        for agent in resources.agents
    ]
