"""
Round-robin agent selector implementation for sokovan scheduler.

This selector distributes workloads evenly across agents using
a simple round-robin index.
"""

from typing import Optional, Sequence

from ai.backend.common.types import AgentId

from .selector import (
    AbstractAgentSelector,
    AgentInfo,
    AgentSelectionConfig,
    AgentSelectionCriteria2,
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

    def select_agent_by_strategy(
        self,
        agents: Sequence[AgentInfo],
        resource_req: ResourceRequirements,
        criteria: AgentSelectionCriteria2,
        config: AgentSelectionConfig,
    ) -> Optional[AgentId]:
        """
        Select an agent using round-robin.

        The caller should track and update the index after successful allocation.
        """
        # Sort agents by ID for consistent ordering
        sorted_agents = sorted(agents, key=lambda agent: agent.agent_id)

        # Use modulo to wrap around
        selected_index = self.next_index % len(sorted_agents)

        return sorted_agents[selected_index].agent_id
