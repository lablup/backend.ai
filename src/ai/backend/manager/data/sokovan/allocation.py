"""Allocation-related data types for scheduling results."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionTypes,
)


@dataclass
class SchedulingPredicate:
    """Represents a scheduling predicate (passed or failed)."""

    # Name of the component that generated this predicate
    name: str
    # Message describing the result
    msg: str

    def serialize(self) -> dict[str, str]:
        """Convert to dictionary for JSON serialization."""
        return {"name": self.name, "msg": self.msg}


@dataclass
class KernelAllocation:
    """Represents an allocation decision for a single kernel."""

    # Unique identifier of the kernel
    kernel_id: UUID
    # Identifier of the agent where this kernel will be allocated
    agent_id: AgentId
    # Network address of the agent
    agent_addr: str
    # Scaling group that the agent belongs to
    scaling_group: str
    # Host ports allocated for this kernel (empty set if none)
    allocated_host_ports: set[int] = field(default_factory=set)


@dataclass
class AgentAllocation:
    """Represents resource allocation to a specific agent."""

    # Identifier of the agent
    agent_id: AgentId
    # List of resource slots allocated to this agent
    allocated_slots: list[ResourceSlot]


@dataclass
class SessionAllocation:
    """Represents an allocation decision for a session with all its kernels."""

    # Unique identifier of the session
    session_id: SessionId
    # Type of the session (INTERACTIVE, BATCH, INFERENCE)
    session_type: SessionTypes
    # Cluster mode of the session (SINGLE_NODE or MULTI_NODE)
    cluster_mode: ClusterMode
    # Scaling group that the session belongs to
    scaling_group: str
    # List of kernel allocations for this session
    kernel_allocations: list[KernelAllocation]
    # List of agent allocations for this session
    agent_allocations: list[AgentAllocation]
    # Keypair associated with the session
    access_key: AccessKey
    # Phases that passed during scheduling
    passed_phases: list[SchedulingPredicate] = field(default_factory=list)
    # Phases that failed during scheduling (normally empty for successful allocations)
    failed_phases: list[SchedulingPredicate] = field(default_factory=list)

    def unique_agent_ids(self) -> list[AgentId]:
        """Extract unique agent IDs from kernel allocations."""
        return list({
            kernel_alloc.agent_id
            for kernel_alloc in self.kernel_allocations
            if kernel_alloc.agent_id is not None
        })


@dataclass
class SchedulingFailure:
    """Information about a scheduling failure for status updates.

    Maintains compatibility with frontend scheduler JSON structure:
    {
        failed_predicates: Array<{name: string, msg?: string}>,
        passed_predicates: Array<{name: string}>,
        retries: number,
        last_try: string,
        msg?: string
    }
    """

    session_id: SessionId
    passed_phases: list[SchedulingPredicate] = field(default_factory=list)
    failed_phases: list[SchedulingPredicate] = field(default_factory=list)
    last_try: datetime | None = None
    msg: str | None = None

    def to_status_data(self, current_retries: int) -> dict[str, Any]:
        """Convert failure to status data dictionary for storage."""
        return {
            "passed_predicates": [p.serialize() for p in self.passed_phases],
            "failed_predicates": [p.serialize() for p in self.failed_phases],
            "retries": current_retries + 1,
            "last_try": self.last_try.isoformat() if self.last_try else None,
            "msg": self.msg,
        }


@dataclass
class AllocationBatch:
    """Bundle of session allocations and scheduling failures for batch processing."""

    # Successful allocations to process
    allocations: list[SessionAllocation]
    # Failed scheduling attempts to update status for
    failures: list[SchedulingFailure]

    def get_agent_ids(self) -> set[AgentId]:
        """Extract all agent IDs from allocations for efficient pre-fetching."""
        agent_ids: set[AgentId] = set()
        for allocation in self.allocations:
            for agent_alloc in allocation.agent_allocations:
                agent_ids.add(agent_alloc.agent_id)
        return agent_ids
