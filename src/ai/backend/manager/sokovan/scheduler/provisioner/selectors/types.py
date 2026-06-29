"""Value types for agent-selection remediation suggestions.

Kept separate from ``selector.py`` (selection logic) and ``exceptions.py``
(error classes) so the error classes can return a Suggestion without importing
the selection logic. These types depend only on common value types.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from ai.backend.common.types import AgentId, ResourceSlot


class SuggestionKind(enum.StrEnum):
    """Which remediation a Suggestion describes (and thus which field is meaningful)."""

    REDUCE_RESOURCE = "reduce_resource"
    REDUCE_CONTAINER = "reduce_container"
    CHANGE_ARCH = "change_arch"
    CHANGE_DESIGNATED_AGENT = "change_designated_agent"
    NONE = "none"


@dataclass
class Suggestion:
    """A structured remediation hint for a failed agent selection.

    ``kind`` tells the consumer which field carries the actionable value:
    - REDUCE_RESOURCE -> ``required_reduction`` (subtract this to fit the best node)
    - REDUCE_CONTAINER -> reduce the per-agent container count / cluster size
    - CHANGE_ARCH -> ``available_archs`` (architectures that actually exist)
    - CHANGE_DESIGNATED_AGENT -> ``available_agent_ids`` (designated agents to revise)
    - NONE -> no actionable remediation
    """

    kind: SuggestionKind
    available_archs: list[str] | None = None
    available_agent_ids: list[AgentId] | None = None
    required_reduction: ResourceSlot | None = None
