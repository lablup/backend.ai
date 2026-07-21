"""
Round-robin agent selector implementation for sokovan scheduler.

This selector distributes workloads evenly across agents by rotating an
in-process index over the ID-ordered compatible candidates.

The rotation is a best-effort approximation, not a strict turn order:
the index resets on process restart / leader failover, and the candidate
set varies per selection with compatibility filtering. That is
sufficient for the goal of evening out placements.
"""

from collections.abc import Sequence
from typing import override

from .selector import (
    AbstractAgentSelector,
    AgentSelectionConfig,
    AgentSelectionCriteria,
    AgentStateTracker,
)
from .types import ResourceRequirements


class RoundRobinAgentSelector(AbstractAgentSelector):
    """
    Round-robin agent selector that distributes workloads evenly.
    """

    _next_index: int

    def __init__(self) -> None:
        self._next_index = 0

    @override
    def name(self) -> str:
        """
        Return the selector name for predicates.
        """
        return "RoundRobinAgentSelector"

    @override
    def success_message(self) -> str:
        """
        Return a message describing successful agent selection.
        """
        return "Agent selected using round-robin strategy for even workload distribution"

    @override
    def select_tracker_by_strategy(
        self,
        trackers: Sequence[AgentStateTracker],
        _resource_req: ResourceRequirements,
        _criteria: AgentSelectionCriteria,
        _config: AgentSelectionConfig,
    ) -> AgentStateTracker:
        """
        Select an agent tracker using round-robin.

        Assumes trackers are already filtered for compatibility.
        """
        # Sort trackers by agent ID for consistent ordering
        sorted_trackers = sorted(trackers, key=lambda tracker: tracker.original_agent.agent_id)

        selected = sorted_trackers[self._next_index % len(sorted_trackers)]
        self._next_index += 1
        return selected
