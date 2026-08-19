"""Batch-scoped agent state tracking for agent selection.

``build_agent_trackers`` is the single construction point shared by the
scheduling pass and the compute-schedule fitting check.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal

from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.identifier.session_group import SessionGroupID
from ai.backend.common.types import SessionId
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
    # Observed live members this agent holds, per session group
    group_member_counts: Mapping[SessionGroupID, int] = field(default_factory=dict)
    committed_slots: dict[ResourceSlotName, Decimal] = field(default_factory=dict)
    committed_containers: int = 0
    committed_group_members: dict[SessionGroupID, int] = field(default_factory=dict)
    pending_slots: dict[ResourceSlotName, Decimal] = field(default_factory=dict)
    pending_containers: int = 0
    # Group of the session being placed, once it lands here. A session counts
    # once per agent no matter how many of its kernels land on it, so this is
    # a membership mark rather than a counter.
    pending_group_id: SessionGroupID | None = None
    # Provisional victim reclaims of the preemption probe; always cleared
    # before real placements continue (see apply_reclaim)
    reclaimed_slots: dict[ResourceSlotName, Decimal] = field(default_factory=dict)

    def remaining_slots(self) -> dict[ResourceSlotName, Decimal]:
        """Per-slot remaining = capacity - reserved - used - in-batch allocations."""
        remaining: dict[ResourceSlotName, Decimal] = {}
        for slot_name, resource in self.original_agent.resources.slots.items():
            remaining[slot_name] = (
                resource.capacity
                - resource.reserved
                - resource.used
                - self.committed_slots.get(slot_name, Decimal(0))
                - self.pending_slots.get(slot_name, Decimal(0))
                + self.reclaimed_slots.get(slot_name, Decimal(0))
            )
        return remaining

    def current_container_count(self) -> int:
        """Get current container count including in-batch allocations."""
        return (
            self.original_agent.container_count
            + self.committed_containers
            + self.pending_containers
        )

    def current_group_member_count(self, session_group_id: SessionGroupID) -> int:
        """Members of the group on this agent = observed + in-batch increments."""
        count = self.group_member_counts.get(
            session_group_id, 0
        ) + self.committed_group_members.get(session_group_id, 0)
        if self.pending_group_id == session_group_id:
            count += 1
        return count

    def apply_diff(
        self,
        request: ResourceRequest,
        containers: int,
        session_group_id: SessionGroupID | None,
    ) -> None:
        """Apply an in-flight allocation of the session being placed."""
        for slot_name, amount in request.slots.items():
            self.pending_slots[slot_name] = self.pending_slots.get(slot_name, Decimal(0)) + amount
        self.pending_containers += containers
        if session_group_id is not None:
            self.pending_group_id = session_group_id

    def commit(self) -> None:
        """Fold the in-flight allocation into the batch state (session placed)."""
        for slot_name, amount in self.pending_slots.items():
            self.committed_slots[slot_name] = (
                self.committed_slots.get(slot_name, Decimal(0)) + amount
            )
        self.committed_containers += self.pending_containers
        if self.pending_group_id is not None:
            self.committed_group_members[self.pending_group_id] = (
                self.committed_group_members.get(self.pending_group_id, 0) + 1
            )
        self.rollback()

    def rollback(self) -> None:
        """Discard the in-flight allocation (session placement failed)."""
        self.pending_slots = {}
        self.pending_containers = 0
        self.pending_group_id = None

    def apply_reclaim(self, slots: Mapping[ResourceSlotName, Decimal]) -> None:
        """Provisionally reclaim a preemption victim's allocation back onto
        this agent, adding into ``remaining_slots``.

        Probe-only: the caller must ``clear_reclaim()`` before any real
        placement runs against this tracker again.
        """
        for slot_name, amount in slots.items():
            self.reclaimed_slots[slot_name] = (
                self.reclaimed_slots.get(slot_name, Decimal(0)) + amount
            )

    def clear_reclaim(self) -> None:
        """Drop every provisional reclaim (the probe is over)."""
        self.reclaimed_slots = {}


def build_agent_trackers(resources: ResourceGroupResource) -> list[AgentStateTracker]:
    """Build the per-agent selection trackers from the observed resources."""
    return [
        AgentStateTracker(
            original_agent=agent.to_agent_info(),
            failed_session_ids=frozenset(
                resources.failed_sessions_by_agent.get(agent.id, frozenset())
            ),
            group_member_counts=resources.group_members_by_agent.get(agent.id, {}),
        )
        for agent in resources.agents
    ]
