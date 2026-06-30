"""Value types for agent-selection remediation suggestions.

Kept separate from ``selector.py`` (selection logic) and ``exceptions.py``
(error classes) so the error classes can return a RemediationHint without
importing the selection logic. These types depend only on common value types.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ai.backend.common.types import AgentId, KernelId, ResourceSlot


@dataclass
class ResourceRequirements:
    """Resource requirements for allocation."""

    # Resource slots required
    requested_slots: ResourceSlot
    # Architecture required
    required_architecture: str
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
    required_reduction: ResourceSlot | None = None
    required_container_reduction: int | None = None
