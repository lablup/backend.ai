"""Allocation write-boundary values for scheduling results.

These carry exactly what the allocation write persists (kernel-to-agent
bindings and the derived session agent list); everything else about the
session is already recorded at enqueue. The same values are the intended
contract for a future sokovan reconciler applier that performs the
allocation together with the status transition.
"""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.types import AgentId, KernelId, SessionId


@dataclass
class KernelAllocation:
    """Binding of one kernel to its selected agent."""

    # Kernel whose row is updated (PENDING -> SCHEDULED gate)
    kernel_id: KernelId
    # Selected agent
    agent_id: AgentId
    # Network address of the agent
    agent_addr: str


@dataclass
class SessionAllocation:
    """Allocation decision for a session: its kernel-to-agent bindings."""

    session_id: SessionId
    kernel_allocations: list[KernelAllocation]

    def unique_agent_ids(self) -> list[AgentId]:
        """Distinct agents this session lands on (``sessions.agent_ids``)."""
        return list({kernel_alloc.agent_id for kernel_alloc in self.kernel_allocations})


@dataclass
class SchedulingFailure:
    """A failed scheduling attempt of a session."""

    session_id: SessionId
    # Human-readable failure reason (transition reason / pending queue)
    msg: str
