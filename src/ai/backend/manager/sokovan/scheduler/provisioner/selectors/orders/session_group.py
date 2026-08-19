"""Order: the session group's placement direction narrows the tier."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from ai.backend.manager.data.session_group.types import SessionGroupPlacementDirection
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.tracker import AgentStateTracker

from .order import AbstractTrackerOrder

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
        AgentSelectionCriteria,
    )


class SessionGroupOrder(AbstractTrackerOrder):
    """Narrows to the tier the group's direction prefers, leaving the final
    pick to the resource group's strategy.

    Both directions rank by the member count, in opposite signs: ``spread``
    keeps the emptiest agents, ``pack`` the fullest ones (the pipeline takes
    the minimum rank across every candidate, so a negated count selects the
    maximum). Under STRICT the filter has already restricted the candidates,
    so this is a no-op there — the same way the designated-agent order defers
    to its strict filter.
    """

    @override
    def name(self) -> str:
        return "session-group"

    @override
    def rank(self, tracker: AgentStateTracker, criteria: AgentSelectionCriteria) -> int:
        policy = criteria.session_group
        if policy is None:
            return 0
        match policy.direction:
            case SessionGroupPlacementDirection.SPREAD:
                return tracker.current_group_member_count(policy.group_id)
            case SessionGroupPlacementDirection.PACK:
                return -tracker.current_group_member_count(policy.group_id)
            case SessionGroupPlacementDirection.NONE:
                return 0
