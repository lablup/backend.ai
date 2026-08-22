"""Workload data types for scheduling."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from functools import cached_property
from typing import NewType
from uuid import UUID

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    ArchName,
    ClusterMode,
    KernelId,
    PreemptionVictimScope,
    SessionId,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.data.session_group.types import (
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)


@dataclass(frozen=True)
class ResourceRequest:
    """Requested slot amounts of one workload (kernel-level granularity)."""

    slots: Mapping[ResourceSlotName, Decimal]


@dataclass(frozen=True)
class SessionResourceRequest(ResourceRequest):
    """Session-level request: slot amounts plus the session itself.

    Exactly one of the session counts is 1 (sftp for private sessions),
    so folding a request into an allocation advances both the slot
    reservation and the session count.
    """

    session_count: int
    sftp_session_count: int


@dataclass(frozen=True)
class SessionDependencyInfo:
    """Information about a session dependency."""

    depends_on: SessionId
    dependency_name: str
    dependency_status: SessionStatus
    dependency_result: SessionResult


@dataclass(frozen=True)
class KernelWorkload:
    """Represents a kernel workload within a session."""

    # Unique identifier of the kernel
    kernel_id: KernelId
    # Architecture required for the kernel
    architecture: ArchName
    # Resource requirements for this kernel
    requested_slots: ResourceRequest


@dataclass(frozen=True)
class WorkloadOwner:
    """Owner-scope keys: fairness ordering and quota validation."""

    access_key: AccessKey
    user_uuid: UserID
    project_id: ProjectID
    domain_id: DomainID


PreemptionScopeKey = NewType("PreemptionScopeKey", UUID)
"""Id of the scope entity one victim-candidate group belongs to: the user /
project / domain id, or the resource group's own id for the RESOURCE_GROUP
scope (one key for the whole snapshot, since scheduling runs per group)."""


@dataclass(frozen=True)
class WorkloadMeta:
    """Identity of one schedulable workload."""

    session_id: SessionId
    resource_group_id: ResourceGroupID
    owner: WorkloadOwner

    def preemption_scope_key(self, scope: PreemptionVictimScope) -> PreemptionScopeKey:
        """Key of the scope entity this workload belongs to under the scope.

        The single derivation shared by the candidate loader's grouping and
        the snapshot's lookup."""
        match scope:
            case PreemptionVictimScope.USER:
                return PreemptionScopeKey(self.owner.user_uuid)
            case PreemptionVictimScope.PROJECT:
                return PreemptionScopeKey(self.owner.project_id)
            case PreemptionVictimScope.DOMAIN:
                return PreemptionScopeKey(self.owner.domain_id)
            case PreemptionVictimScope.RESOURCE_GROUP:
                return PreemptionScopeKey(self.resource_group_id)


@dataclass(frozen=True)
class SessionGroupPolicy:
    """The placement policy of the session group this session belongs to.

    Direction and enforcement are orthogonal: the direction says how members
    sit relative to each other, the enforcement decides which pipeline stage
    applies it (PREFERRED narrows, STRICT excludes).
    """

    group_id: SessionGroupID
    direction: SessionGroupPlacementDirection
    enforcement: SessionGroupPlacementEnforcement


@dataclass(frozen=True)
class SessionPlacement:
    """Selection-facing part of the workload: what must land on agents."""

    cluster_mode: ClusterMode
    kernels: list[KernelWorkload]
    # How designated agents are enforced (STRICT fails, PREFERRED falls back)
    agent_selection_policy: AgentSelectionPolicy
    # Manually designated agents (user's explicit choice takes precedence)
    designated_agent_ids: list[AgentId] | None
    # Placement policy of the session's group (None when the session has no
    # group, or its group is gone — either way it is placed unconstrained)
    session_group: SessionGroupPolicy | None


@dataclass
class SessionWorkload:
    """Represents a session workload for scheduling."""

    meta: WorkloadMeta
    placement: SessionPlacement
    # Priority level for sequencing (higher value = higher priority)
    priority: int
    # Scope-local preemption priority among the owner's own sessions
    # (higher preempts lower; decoupled from the global scheduler ``priority``)
    job_priority: int
    # Session type (INTERACTIVE, BATCH, INFERENCE)
    session_type: SessionTypes
    # Reserved start time requested at enqueue (batch sessions); the
    # scheduler holds the session until this time
    requested_starts_at: datetime | None
    # Whether this session can be preempted
    is_preemptible: bool

    @property
    def is_private(self) -> bool:
        """Private (SFTP) sessions count against the sftp session quota."""
        return self.session_type in SessionTypes.private_types()

    @cached_property
    def requested_slots(self) -> SessionResourceRequest:
        """Session-level request: per-slot sums of the kernels plus the
        session count of the requested kind."""
        slots: dict[ResourceSlotName, Decimal] = {}
        for kernel in self.placement.kernels:
            for slot_name, amount in kernel.requested_slots.slots.items():
                slots[slot_name] = slots.get(slot_name, Decimal(0)) + amount
        is_private = self.is_private
        return SessionResourceRequest(
            slots=slots,
            session_count=0 if is_private else 1,
            sftp_session_count=1 if is_private else 0,
        )
