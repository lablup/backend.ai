"""
Dispersed agent selector implementation for sokovan scheduler.

This selector prefers agents with more available resources to spread
workloads across the cluster.
"""

import sys
from collections.abc import Sequence
from decimal import Decimal
from typing import override

from .selector import (
    AbstractAgentSelector,
    AgentStateTracker,
)
from .types import ResourceRequirements
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

    @override
    def name(self) -> str:
        """
        Return the selector name for predicates.
        """
        return "DispersedAgentSelector"

    @override
    def success_message(self) -> str:
        """
        Return a message describing successful agent selection.
        """
        return "Agent selected using dispersed strategy for balanced workload distribution"

    @override
    def select_tracker_by_strategy(
        self,
        trackers: Sequence[AgentStateTracker],
        resource_req: ResourceRequirements,
    ) -> AgentStateTracker:
        """
        Select an agent tracker to disperse workloads.

        Assumes trackers are already filtered for compatibility.
        """
        # Sort requested slots by priority
        resource_priorities = order_slots_by_priority(
            resource_req.requested_slots, self.agent_selection_resource_priority
        )

        # Choose the tracker with maximum remaining resources (to disperse workloads)
        def tracker_sort_key(tracker: AgentStateTracker) -> list[int | Decimal]:
            remaining_slots = tracker.remaining_slots()
            return [
                # First, prefer agents with fewer unutilized capabilities
                -count_unutilized_capabilities(
                    tracker.original_agent, resource_req.requested_slots
                ),
                # Then, prefer agents with more remaining resources (using current state)
                *[remaining_slots.get(key, -sys.maxsize) for key in resource_priorities],
            ]

        return max(trackers, key=tracker_sort_key)
