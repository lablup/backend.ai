"""Placement input of one session: what must land on agents."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.types import AgentId, ArchName, ClusterMode, KernelId
from ai.backend.sokovan_core.types.policy import (
    AgentSelectionPolicy,
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)


@dataclass(frozen=True)
class ResourceRequest:
    """Requested slot amounts of one workload (kernel-level granularity)."""

    slots: Mapping[ResourceSlotName, Decimal]


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
