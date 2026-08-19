"""Order: designated agents come first (the user's explicit choice)."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from ai.backend.manager.sokovan.scheduler.provisioner.selectors.tracker import AgentStateTracker

from .order import AbstractTrackerOrder

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
        AgentSelectionCriteria,
    )


class DesignatedPreferredOrder(AbstractTrackerOrder):
    """Prefers the designated agents when any survive the filters; without a
    designation (or when none survive) every candidate ranks the same."""

    @override
    def name(self) -> str:
        return "designated-preferred"

    @override
    def rank(self, tracker: AgentStateTracker, criteria: AgentSelectionCriteria) -> int:
        if not criteria.designated_agent_ids:
            return 0
        return 0 if tracker.original_agent.agent_id in criteria.designated_agent_ids else 1
