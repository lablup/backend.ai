"""
Round-robin agent selector implementation for sokovan scheduler.

This selector distributes workloads evenly across agents using
a simple round-robin index.
"""

from typing import Sequence

from .selector import (
    AbstractAgentSelector,
    AgentSelectionConfig,
    AgentSelectionCriteria,
    AgentStateTracker,
    ResourceRequirements,
)


class RoundRobinAgentSelector(AbstractAgentSelector):
    """
    Round-robin agent selector that distributes workloads evenly.

    This selector uses a simple index-based approach for round-robin
    selection. Some variance is acceptable.
    """

    def __init__(self, next_index: int = 0) -> None:
        """
        Initialize with the next index to use.

        Args:
            next_index: The index for the next selection
        """
        self.next_index = next_index

    def name(self) -> str:
        """
        Return the selector name for predicates.
        """
        return "RoundRobinAgentSelector"

    def success_message(self) -> str:
        """
        Return a message describing successful agent selection.
        """
        return "Agent selected using round-robin strategy for even workload distribution"

    def select_tracker_by_strategy(
        self,
        trackers: Sequence[AgentStateTracker],
        resource_req: ResourceRequirements,
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
    ) -> AgentStateTracker:
        """
        Select an agent tracker using round-robin.

        Assumes trackers are already filtered for compatibility.
        The caller should track and update the index after successful allocation.
        """
        # Sort trackers by agent ID for consistent ordering
        sorted_trackers = sorted(trackers, key=lambda tracker: tracker.original_agent.agent_id)

        # Use modulo to wrap around
        selected_index = self.next_index % len(sorted_trackers)

        return sorted_trackers[selected_index]
