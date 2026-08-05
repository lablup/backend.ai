"""Exclusion filter: strict designation limits the pool to the designated agents."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, override

from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.filters.exclusion.filter import (
    AbstractExclusionTrackerFilter,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.tracker import AgentStateTracker
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.types import ResourceRequirements

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
        AgentSelectionCriteria,
    )


class DesignatedStrictTrackerFilter(AbstractExclusionTrackerFilter):
    """Under the STRICT policy only the designated agents may host the
    session; PREFERRED designation is an ordering concern, not a filter."""

    @override
    def name(self) -> str:
        return "designated-strict"

    @override
    def success_message(self) -> str:
        return "Designated agents present (or no strict designation)"

    @override
    def failure_message(
        self,
        criteria: AgentSelectionCriteria,
        resource_req: ResourceRequirements,
    ) -> str:
        designated = ", ".join(str(agent_id) for agent_id in criteria.designated_agent_ids or [])
        return f"none of the strictly designated agents [{designated}] is available"

    @override
    def filter(
        self,
        trackers: Sequence[AgentStateTracker],
        criteria: AgentSelectionCriteria,
        resource_req: ResourceRequirements,
    ) -> Sequence[AgentStateTracker]:
        if (
            not criteria.designated_agent_ids
            or criteria.agent_selection_policy != AgentSelectionPolicy.STRICT
        ):
            return trackers
        return [
            tracker
            for tracker in trackers
            if tracker.original_agent.agent_id in criteria.designated_agent_ids
        ]
