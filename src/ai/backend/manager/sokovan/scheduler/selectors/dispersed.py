"""
Dispersed agent selector implementation for sokovan scheduler.

This selector prefers agents with more available resources to spread
workloads across the cluster.
"""

import sys
from typing import Optional, Sequence

from ai.backend.common.types import AgentId

from .selector import AbstractAgentSelector, AgentInfo, AgentSelectionCriteria
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

    async def select_agent_by_strategy(
        self,
        agents: Sequence[AgentInfo],
        criteria: AgentSelectionCriteria,
    ) -> Optional[AgentId]:
        """
        Select an agent to disperse workloads.

        Assumes agents are already filtered for compatibility.
        """
        if not agents:
            return None

        # Sort requested slots by priority
        resource_priorities = order_slots_by_priority(
            criteria.requested_slots, self.agent_selection_resource_priority
        )

        # Choose the agent with maximum available resources (to disperse workloads)
        chosen_agent = max(
            agents,
            key=lambda agent: [
                # First, prefer agents with fewer unutilized capabilities
                -count_unutilized_capabilities(agent, criteria.requested_slots),
                # Then, prefer agents with more available resources
                *[
                    (agent.available_slots - agent.occupied_slots).get(key, -sys.maxsize)
                    for key in resource_priorities
                ],
            ],
        )

        return chosen_agent.agent_id
