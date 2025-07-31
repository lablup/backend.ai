import sys
from typing import Optional, Sequence

from ai.backend.common.types import AgentId, ResourceSlot
from ai.backend.manager.models import AgentRow
from ai.backend.manager.scheduler.allocators.base import BaseAllocator
from ai.backend.manager.scheduler.utils import (
    get_num_extras,
    sort_requested_slots_by_priority,
)


class LegacyAllocator(BaseAllocator):
    """
    Legacy agent allocator.

    This allocator uses the original agent selection strategy,
    preferring agents with:
    1. Fewer unused resource types
    2. More available resources for the requested types
    """

    def __init__(self, agent_selection_resource_priority: list[str] | None = None):
        super().__init__()
        self.agent_selection_resource_priority = agent_selection_resource_priority or []

    @property
    def name(self) -> str:
        return "legacy"

    async def allocate(self) -> None:
        """No preprocessing needed for legacy allocation."""
        pass

    async def select_agent(
        self,
        agents: Sequence[AgentRow],
        requested_slots: ResourceSlot,
        requested_architecture: Optional[str] = None,
        **kwargs,
    ) -> Optional[AgentId]:
        """
        Select an agent using legacy strategy.

        Args:
            agents: List of available agents
            requested_slots: Resources requested
            requested_architecture: Required architecture

        Returns:
            Selected agent ID or None if no suitable agent found
        """
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

        # Select agent with:
        # 1. Fewest unused resource types (negative to minimize)
        # 2. Most available resources for requested types
        chosen_agent = max(
            agents,
            key=lambda agent: [
                -get_num_extras(agent, requested_slots),
                *[agent.available_slots.get(key, -sys.maxsize) for key in resource_priorities],
            ],
        )

        return chosen_agent.id
