"""
Concentrated agent selector implementation for sokovan scheduler.

This selector prefers agents with fewer available resources to maximize
resource utilization by concentrating workloads.
"""

import sys
from decimal import Decimal
from typing import Sequence, Union

from ai.backend.common.types import SessionTypes

from .selector import (
    AbstractAgentSelector,
    AgentSelectionConfig,
    AgentSelectionCriteria,
    AgentStateTracker,
    ResourceRequirements,
)
from .utils import count_unutilized_capabilities, order_slots_by_priority


class ConcentratedAgentSelector(AbstractAgentSelector):
    """
    Concentrated agent selector that maximizes resource utilization.

    This selector prefers agents with:
    1. Fewer kernels at the same endpoint (for endpoint replica spreading)
    2. Fewer unutilized capabilities
    3. Less available resources (to concentrate workloads)
    """

    def __init__(self, agent_selection_resource_priority: list[str]) -> None:
        """
        Initialize the concentrated selector.

        Args:
            agent_selection_resource_priority: Resource types in priority order
        """
        self.agent_selection_resource_priority = agent_selection_resource_priority

    def name(self) -> str:
        """
        Return the selector name for predicates.
        """
        return "ConcentratedAgentSelector"

    def success_message(self) -> str:
        """
        Return a message describing successful agent selection.
        """
        return "Agent selected using concentrated strategy for maximum resource utilization"

    def select_tracker_by_strategy(
        self,
        trackers: Sequence[AgentStateTracker],
        resource_req: ResourceRequirements,
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
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
        def tracker_sort_key(tracker: AgentStateTracker) -> tuple[Union[int, Decimal], ...]:
            agent = tracker.original_agent
            occupied_slots = tracker.get_current_occupied_slots()
            sort_key = []

            # First, consider kernel counts at endpoint for replica spreading
            if (
                config.enforce_spreading_endpoint_replica
                and criteria.kernel_counts_at_endpoint
                and criteria.session_metadata.session_type == SessionTypes.INFERENCE
            ):
                kernel_count = criteria.kernel_counts_at_endpoint.get(agent.agent_id, 0)
                sort_key.append(kernel_count)

            # Then, prefer agents with fewer unutilized capabilities
            sort_key.append(count_unutilized_capabilities(agent, resource_req.requested_slots))

            # Finally, prefer agents with less available resources (using current state)
            for key in resource_priorities:
                sort_key.append((agent.available_slots - occupied_slots).get(key, sys.maxsize))

            return tuple(sort_key)

        chosen_tracker = min(trackers, key=tracker_sort_key)

        return chosen_tracker
