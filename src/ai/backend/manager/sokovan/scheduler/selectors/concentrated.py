"""
Concentrated agent selector implementation for sokovan scheduler.

This selector prefers agents with fewer available resources to maximize
resource utilization by concentrating workloads.
"""

import sys
from typing import Optional, Sequence

from ai.backend.common.types import AgentId

from .selector import AbstractAgentSelector, AgentInfo, AgentSelectionCriteria
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

    def select_agent_by_strategy(
        self,
        agents: Sequence[AgentInfo],
        criteria: AgentSelectionCriteria,
    ) -> Optional[AgentId]:
        """
        Select an agent to concentrate workloads.

        Assumes agents are already filtered for compatibility.
        """
        if not agents:
            return None

        # Sort requested slots by priority
        resource_priorities = order_slots_by_priority(
            criteria.requested_slots, self.agent_selection_resource_priority
        )

        # Choose the agent with minimum resources (to concentrate workloads)
        chosen_agent = min(
            agents,
            key=lambda agent: (
                # First, consider kernel counts at endpoint for replica spreading
                agent.kernel_count_at_endpoint,
                # Then, prefer agents with fewer unutilized capabilities
                count_unutilized_capabilities(agent, criteria.requested_slots),
                # Finally, prefer agents with less available resources
                *[
                    (agent.available_slots - agent.occupied_slots).get(key, sys.maxsize)
                    for key in resource_priorities
                ],
            ),
        )

        return chosen_agent.agent_id
