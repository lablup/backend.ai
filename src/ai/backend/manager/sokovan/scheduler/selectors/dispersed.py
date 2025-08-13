"""
Dispersed agent selector implementation for sokovan scheduler.

This selector prefers agents with more available resources to spread
workloads across the cluster.
"""

import sys
from decimal import Decimal
from typing import Sequence, Union

from .selector import (
    AbstractAgentSelector,
    AgentSelectionConfig,
    AgentSelectionCriteria,
    AgentStateTracker,
    ResourceRequirements,
)
from .utils import count_unutilized_capabilities, order_slots_by_priority


class DispersedAgentSelector(AbstractAgentSelector):
    """
    Dispersed agent selector that spreads workloads across agents.

    This selector prefers agents with:
    1. Fewer unutilized capabilities
    2. More available resources (to spread workloads)
    """

    def __init__(self, agent_selection_resource_priority: list[str]) -> None:
        """
        Initialize the dispersed selector.

        Args:
            agent_selection_resource_priority: Resource types in priority order
        """
        self.agent_selection_resource_priority = agent_selection_resource_priority

    def name(self) -> str:
        """
        Return the selector name for predicates.
        """
        return "DispersedAgentSelector"

    def success_message(self) -> str:
        """
        Return a message describing successful agent selection.
        """
        return "Agent selected using dispersed strategy for balanced workload distribution"

    def select_tracker_by_strategy(
        self,
        trackers: Sequence[AgentStateTracker],
        resource_req: ResourceRequirements,
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
    ) -> AgentStateTracker:
        """
        Select an agent tracker to disperse workloads.

        Assumes trackers are already filtered for compatibility.
        """
        # Sort requested slots by priority
        resource_priorities = order_slots_by_priority(
            resource_req.requested_slots, self.agent_selection_resource_priority
        )

        # Choose the tracker with maximum available resources (to disperse workloads)
        def tracker_sort_key(tracker: AgentStateTracker) -> list[Union[int, Decimal]]:
            occupied_slots = tracker.get_current_occupied_slots()
            return [
                # First, prefer agents with fewer unutilized capabilities
                -count_unutilized_capabilities(
                    tracker.original_agent, resource_req.requested_slots
                ),
                # Then, prefer agents with more available resources (using current state)
                *[
                    (tracker.original_agent.available_slots - occupied_slots).get(key, -sys.maxsize)
                    for key in resource_priorities
                ],
            ]

        chosen_tracker = max(trackers, key=tracker_sort_key)

        return chosen_tracker
