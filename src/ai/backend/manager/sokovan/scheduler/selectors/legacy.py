"""
Legacy agent selector implementation for sokovan scheduler.

This selector chooses agents based on resource priorities, preferring agents
with fewer unutilized capabilities.
"""

import sys
from typing import Optional, Sequence

from ai.backend.common.types import AgentId

from .selector import (
    AbstractAgentSelector,
    AgentInfo,
    AgentSelectionConfig,
    AgentSelectionCriteria,
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

    def select_agent_by_strategy(
        self,
        agents: Sequence[AgentInfo],
        resource_req: ResourceRequirements,
        criteria: AgentSelectionCriteria,
        config: AgentSelectionConfig,
    ) -> Optional[AgentId]:
        """
        Select an agent based on resource priorities.

        Assumes agents are already filtered for compatibility.
        """
        # Sort requested slots by priority
        resource_priorities = order_slots_by_priority(
            resource_req.requested_slots, self.agent_selection_resource_priority
        )

        # Choose the best agent
        chosen_agent = max(
            agents,
            key=lambda agent: [
                -count_unutilized_capabilities(agent, resource_req.requested_slots),
                *[
                    (agent.available_slots - agent.occupied_slots).get(key, -sys.maxsize)
                    for key in resource_priorities
                ],
            ],
        )

        return chosen_agent.agent_id
