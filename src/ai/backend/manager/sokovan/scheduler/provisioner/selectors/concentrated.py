"""
Concentrated agent selector implementation for sokovan scheduler.

This selector prefers agents with fewer available resources to maximize
resource utilization by concentrating workloads.
"""

from __future__ import annotations

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


class ConcentratedAgentSelector(AbstractAgentSelector):
    """
    Concentrated agent selector that maximizes resource utilization.

    This selector prefers agents with:
    1. Fewer unutilized capabilities
    2. Less remaining resources (to concentrate workloads)
    """

    def __init__(self, agent_selection_resource_priority: list[str]) -> None:
        """
        Initialize the concentrated selector.

        Args:
            agent_selection_resource_priority: Resource types in priority order
        """
        self.agent_selection_resource_priority = agent_selection_resource_priority

    @override
    def name(self) -> str:
        """
        Return the selector name for predicates.
        """
        return "ConcentratedAgentSelector"

    @override
    def success_message(self) -> str:
        """
        Return a message describing successful agent selection.
        """
        return "Agent selected using concentrated strategy for maximum resource utilization"

    @override
    def select_tracker_by_strategy(
        self,
        trackers: Sequence[AgentStateTracker],
        resource_req: ResourceRequirements,
    ) -> AgentStateTracker:
        """
        Select an agent tracker to concentrate workloads.

        Assumes trackers are already filtered for compatibility.
        """
        # Sort requested slots by priority
        resource_priorities = order_slots_by_priority(
            resource_req.requested_slots, self.agent_selection_resource_priority
        )

        # Choose the tracker with minimum resources (to concentrate workloads)
        def tracker_sort_key(tracker: AgentStateTracker) -> tuple[int | Decimal, ...]:
            agent = tracker.original_agent
            remaining_slots = tracker.remaining_slots()
            sort_key: list[int | Decimal] = []

            # First, prefer agents with fewer unutilized capabilities
            sort_key.append(count_unutilized_capabilities(agent, resource_req.requested_slots))

            # Then, prefer agents with less remaining resources (using current state)
            for key in resource_priorities:
                sort_key.append(remaining_slots.get(key, sys.maxsize))

            return tuple(sort_key)

        return min(trackers, key=tracker_sort_key)
