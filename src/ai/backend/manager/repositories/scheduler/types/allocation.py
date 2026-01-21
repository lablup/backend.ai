"""Allocation-related types for schedule repository."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
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
class SchedulingPredicate:
    """Represents a scheduling predicate (validation or selection phase)."""

    name: str
    msg: str

    def serialize(self) -> dict:
        """Serialize the predicate for storage."""
        return {"name": self.name, "msg": self.msg}


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
    """Represents a failed scheduling attempt for a session."""

    # Session that failed to schedule
    session_id: SessionId
    # Predicates that passed before failure
    passed_phases: list[SchedulingPredicate]
    # Predicates that caused the failure
    failed_phases: list[SchedulingPredicate]
    # Error message describing the failure
    msg: str
    # Timestamp of the last scheduling attempt
    last_try: Optional[datetime] = None

    def to_status_data(self, current_retries: int) -> dict:
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
