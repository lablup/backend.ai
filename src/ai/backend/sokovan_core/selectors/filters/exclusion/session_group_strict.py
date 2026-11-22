"""Exclusion filter: a strict session-group direction removes non-conforming agents."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, override

from ai.backend.sokovan_core.selectors.filters.exclusion.filter import (
    AbstractExclusionTrackerFilter,
)
from ai.backend.sokovan_core.selectors.tracker import AgentStateTracker
from ai.backend.sokovan_core.selectors.types import ResourceRequirements
from ai.backend.sokovan_core.types.policy import (
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)

if TYPE_CHECKING:
    from ai.backend.sokovan_core.selectors.selector import (
        AgentSelectionCriteria,
    )


class SessionGroupStrictTrackerFilter(AbstractExclusionTrackerFilter):
    """Under STRICT enforcement the group's direction is a hard condition;
    PREFERRED enforcement is an ordering concern, not a filter.

    An emptied pool is an absolute failure by design: every agent already
    holds a member of this group, and freeing resources on one of them does
    not remove that member, so no state change (preemption included) can
    make the placement conform.
    """

    @override
    def name(self) -> str:
        return "session-group-strict"

    @override
    def success_message(self) -> str:
        return "Agents conforming to the session group's placement direction found"

    @override
    def failure_message(
        self,
        criteria: AgentSelectionCriteria,
        resource_req: ResourceRequirements,
    ) -> str:
        policy = criteria.session_group
        if policy is None:
            return "no agent conforms to the session group's placement direction"
        return (
            f"session group {policy.group_id} enforces strict "
            f"'{policy.direction}' placement and no agent satisfies it"
        )

    @override
    def filter(
        self,
        trackers: Sequence[AgentStateTracker],
        criteria: AgentSelectionCriteria,
        resource_req: ResourceRequirements,
    ) -> Sequence[AgentStateTracker]:
        policy = criteria.session_group
        if policy is None or policy.enforcement is not SessionGroupPlacementEnforcement.STRICT:
            return trackers
        match policy.direction:
            case SessionGroupPlacementDirection.SPREAD:
                return [
                    tracker
                    for tracker in trackers
                    if tracker.current_group_member_count(policy.group_id) == 0
                ]
            case SessionGroupPlacementDirection.PACK:
                holders = [
                    tracker
                    for tracker in trackers
                    if tracker.current_group_member_count(policy.group_id) > 0
                ]
                # Anchor rule: with no member placed yet there is nothing to
                # pack onto, so the first member is unconstrained.
                return holders or trackers
            case SessionGroupPlacementDirection.NONE:
                return trackers
