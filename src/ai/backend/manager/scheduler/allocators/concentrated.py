import sys
from typing import Optional, Sequence

from ai.backend.common.types import AgentId, ResourceSlot
from ai.backend.manager.models import AgentRow
from ai.backend.manager.scheduler.allocators.base import BaseAllocator
from ai.backend.manager.scheduler.utils import (
    get_num_extras,
    sort_requested_slots_by_priority,
)


class ConcentratedAllocator(BaseAllocator):
    """
    Concentrated agent allocator.

    This allocator prefers agents that already have running kernels,
    minimizing the number of agents used. This is useful for maximizing
    resource utilization on fewer agents.
    """

    def __init__(self, agent_selection_resource_priority: list[str] | None = None):
        super().__init__()
        self.agent_selection_resource_priority = agent_selection_resource_priority or []

    @property
    def name(self) -> str:
        return "concentrated"

    async def allocate(self) -> None:
        """No preprocessing needed for concentrated allocation."""
        pass

    async def select_agent(
        self,
        agents: Sequence[AgentRow],
        requested_slots: ResourceSlot,
        requested_architecture: Optional[str] = None,
        **kwargs,
    ) -> Optional[AgentId]:
        """
        Select an agent using concentrated strategy.

        Prefers agents with:
        1. More existing kernels (higher utilization)
        2. Fewer unused resource types
        3. Less available resources (filling up agents)

        Args:
            agents: List of available agents
            requested_slots: Resources requested
            requested_architecture: Required architecture
            **kwargs: Additional keyword arguments (e.g., kernel_counts)

        Returns:
            Selected agent ID or None if no suitable agent found
        """
        kernel_counts = kwargs.get("kernel_counts", None)
        # Filter by architecture if specified
        if requested_architecture:
            agents = self.filter_agents_by_architecture(agents, requested_architecture)

        # Filter by available resources
        agents = self.filter_agents_by_resources(agents, requested_slots)

        if not agents:
            return None

        # Get resource priorities for sorting
        resource_priorities = sort_requested_slots_by_priority(
            requested_slots, self.agent_selection_resource_priority
        )

        # Default kernel counts to 0 if not provided
        if kernel_counts is None:
            kernel_counts = {}

        # Select agent with:
        # 1. Most kernels already running (concentrate load)
        # 2. Fewest unused resource types
        # 3. Least available resources for requested types
        chosen_agent = min(
            agents,
            key=lambda agent: (
                -kernel_counts.get(agent.id, 0),  # Negative to prefer higher counts
                get_num_extras(agent, requested_slots),  # Fewer extras is better
                *[
                    (agent.available_slots - agent.occupied_slots).get(key, sys.maxsize)
                    for key in resource_priorities
                ],
            ),
        )

        return chosen_agent.id
