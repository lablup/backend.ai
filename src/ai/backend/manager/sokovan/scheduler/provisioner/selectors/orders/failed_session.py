"""Order: agents where this session already failed come last."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from ai.backend.manager.sokovan.scheduler.provisioner.selectors.tracker import AgentStateTracker

from .order import AbstractTrackerOrder

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
        AgentSelectionCriteria,
    )


class FailedSessionOrder(AbstractTrackerOrder):
    """Deprioritizes agents that previously failed to start this session;
    when every candidate has failed, all of them stay (retry must not block)."""

    @override
    def name(self) -> str:
        return "failed-session"

    @override
    def rank(self, tracker: AgentStateTracker, criteria: AgentSelectionCriteria) -> int:
        return 1 if criteria.session_id in tracker.failed_session_ids else 0
