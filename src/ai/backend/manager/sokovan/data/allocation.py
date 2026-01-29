"""Allocation-related data types for scheduling results."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ClusterMode,
    ResourceSlot,
    SessionId,
    SessionTypes,
)

from .workload import SessionWorkload

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
        AgentSelection,
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

    @classmethod
    def from_agent_selections(
        cls,
        session_workload: SessionWorkload,
        selections: list[AgentSelection],
        scaling_group: str,
    ) -> SessionAllocation:
        """
        Build a SessionAllocation from agent selection results.

        :param session_workload: The original session workload
        :param selections: List of agent selection results
        :param scaling_group: The scaling group name
        :param access_key: The access key associated with the session
        :return: SessionAllocation with kernel and agent allocations
        """
        kernel_allocations: list[KernelAllocation] = []
        agent_allocation_map: dict[AgentId, AgentAllocation] = {}

        for selection in selections:
            resource_req = selection.resource_requirements
            selected_agent = selection.selected_agent

            # Track resource allocation for this agent
            if selected_agent.agent_id not in agent_allocation_map:
                agent_allocation_map[selected_agent.agent_id] = AgentAllocation(
                    agent_id=selected_agent.agent_id,
                    allocated_slots=[],
                )
            agent_allocation_map[selected_agent.agent_id].allocated_slots.append(
                resource_req.requested_slots
            )

            # Create kernel allocations
            for kernel_id in resource_req.kernel_ids:
                kernel_allocations.append(
                    KernelAllocation(
                        kernel_id=kernel_id,
                        agent_id=selected_agent.agent_id,
                        agent_addr=selected_agent.agent_addr,
                        scaling_group=selected_agent.scaling_group,
                    )
                )

        # Create session allocation
        agent_allocations = list(agent_allocation_map.values())

        return cls(
            session_id=session_workload.session_id,
            session_type=session_workload.session_type,
            cluster_mode=session_workload.cluster_mode,
            scaling_group=scaling_group,
            kernel_allocations=kernel_allocations,
            agent_allocations=agent_allocations,
            access_key=session_workload.access_key,
        )

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

    def get_agent_ids(self) -> set[AgentId]:
        """Extract all agent IDs from allocations for efficient pre-fetching."""
        agent_ids: set[AgentId] = set()
        for allocation in self.allocations:
            for agent_alloc in allocation.agent_allocations:
                agent_ids.add(agent_alloc.agent_id)
        return agent_ids
