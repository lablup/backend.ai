"""
Legacy agent selector implementation for sokovan scheduler.

This selector chooses agents based on resource priorities, preferring agents
with fewer unutilized capabilities.
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


class LegacyAgentSelector(AbstractAgentSelector):
    """
    Legacy agent selector that chooses agents based on resource priorities.

    This selector prefers agents with:
    1. Fewer unutilized capabilities (resource types)
    2. More available resources in priority order
    """

    def __init__(self, agent_selection_resource_priority: list[str]) -> None:
        self.agent_selection_resource_priority = agent_selection_resource_priority

    def name(self) -> str:
        """
        Return the selector name for predicates.
        """
        return "LegacyAgentSelector"

    def success_message(self) -> str:
        """
        Return a message describing successful agent selection.
        """
        return "Agent selected using legacy priority-based strategy"

    def select_tracker_by_strategy(
        self,
        trackers: Sequence[AgentStateTracker],
        resource_req: ResourceRequirements,
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
    ) -> AgentStateTracker:
        """
        Select an agent tracker based on resource priorities.

        Assumes trackers are already filtered for compatibility.
        """
        # Sort requested slots by priority
        resource_priorities = order_slots_by_priority(
            resource_req.requested_slots, self.agent_selection_resource_priority
        )

        # Choose the best tracker
        def tracker_sort_key(tracker: AgentStateTracker) -> list[Union[int, Decimal]]:
            occupied_slots = tracker.get_current_occupied_slots()
            return [
                -count_unutilized_capabilities(
                    tracker.original_agent, resource_req.requested_slots
                ),
                *[
                    (tracker.original_agent.available_slots - occupied_slots).get(key, -sys.maxsize)
                    for key in resource_priorities
                ],
            ]

        chosen_tracker = max(trackers, key=tracker_sort_key)

        return chosen_tracker
