"""Value types for agent-selection remediation suggestions.

Kept separate from ``selector.py`` (selection logic) and ``exceptions.py``
(error classes) so the error classes can return a RemediationHint without
importing the selection logic. These types depend only on common value types.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal

from ai.backend.common.identifier.architecture import ArchName
from ai.backend.common.types import AgentId, KernelId, SlotName
from ai.backend.manager.views.sokovan.workload import ResourceRequest


@dataclass
class ResourceRequirements:
    """Resource requirements for allocation."""

    # Resource slots required
    requested_slots: ResourceRequest
    # Architecture required
    required_architecture: ArchName
    # Kernel IDs that these requirements are for
    # For single-node, this includes all kernel IDs
    # For multi-node, this includes only one kernel ID
    kernel_ids: Sequence[KernelId]


@dataclass
class RemediationHint:
    """A structured remediation hint for a failed agent selection.

    There is no discriminator: any subset of fields may be populated, and each
    non-None field is an independently actionable remediation the caller can take.

    - ``available_archs`` — architectures that actually exist (change the request arch)
    - ``available_agent_ids`` — agents that are actually available (revise designation)
    - ``required_reduction`` — subtract these slots to fit the best-fitting node
    - ``required_container_reduction`` — free this many containers to admit the kernel
    """

    available_archs: list[str] | None = None
    available_agent_ids: list[AgentId] | None = None
    required_reduction: Mapping[SlotName, Decimal] | None = None
    required_container_reduction: int | None = None
