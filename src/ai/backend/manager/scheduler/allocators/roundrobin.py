from typing import Optional, Sequence

from ai.backend.common.types import AgentId, ArchName, ResourceSlot
from ai.backend.manager.models import AgentRow
from ai.backend.manager.scheduler.allocators.base import BaseAllocator


class RoundRobinAllocator(BaseAllocator):
    """
    Round-robin agent allocator.

    This allocator cycles through available agents in order,
    distributing sessions evenly across all agents.
    """

    def __init__(self):
        super().__init__()
        # Track next index per architecture and scaling group
        self._next_indices: dict[tuple[str, ArchName], int] = {}

    @property
    def name(self) -> str:
        return "roundrobin"

    async def allocate(self) -> None:
        """No preprocessing needed for round-robin allocation."""
        pass

    async def select_agent(
        self,
        agents: Sequence[AgentRow],
        requested_slots: ResourceSlot,
        requested_architecture: Optional[str] = None,
        **kwargs,
    ) -> Optional[AgentId]:
        """
        Select an agent using round-robin strategy.

        Args:
            agents: List of available agents
            requested_slots: Resources requested
            requested_architecture: Required architecture
            **kwargs: Additional keyword arguments (e.g., scaling_group)

        Returns:
            Selected agent ID or None if no suitable agent found
        """
        scaling_group = kwargs.get("scaling_group", None)
        # Filter by architecture if specified
        if requested_architecture:
            agents = self.filter_agents_by_architecture(agents, requested_architecture)

        # Filter by available resources
        agents = self.filter_agents_by_resources(agents, requested_slots)

        if not agents:
            return None

        # Sort agents by ID for consistent ordering
        agents = sorted(agents, key=lambda agent: agent.id)

        # Get the next index for this architecture/scaling group combination
        key = (scaling_group or "default", ArchName(requested_architecture or "default"))
        start_idx = self._next_indices.get(key, 0)

        # Ensure index is within bounds
        start_idx = start_idx % len(agents)

        # Find the next available agent starting from start_idx
        for i in range(len(agents)):
            idx = (start_idx + i) % len(agents)
            agent = agents[idx]

            # Double-check the agent has enough resources
            if agent.available_slots - agent.occupied_slots >= requested_slots:
                # Update next index for this key
                self._next_indices[key] = (idx + 1) % len(agents)
                return agent.id

        return None
