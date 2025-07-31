from abc import ABCMeta
from typing import Optional, Sequence

from ai.backend.common.types import AgentId, ResourceSlot
from ai.backend.manager.models import AgentRow
from ai.backend.manager.scheduler.allocators.allocator import SchedulerAllocator


class BaseAllocator(SchedulerAllocator, metaclass=ABCMeta):
    """Base allocator with common agent filtering functionality."""

    def filter_agents_by_resources(
        self,
        agents: Sequence[AgentRow],
        requested_slots: ResourceSlot,
    ) -> Sequence[AgentRow]:
        """
        Filter agents that have enough available resources.

        Args:
            agents: List of available agents
            requested_slots: Resources requested by the session/kernel

        Returns:
            List of agents that can accommodate the requested resources
        """
        return [
            agent
            for agent in agents
            if (agent.available_slots - agent.occupied_slots >= requested_slots)
        ]

    def filter_agents_by_architecture(
        self,
        agents: Sequence[AgentRow],
        requested_architecture: str,
    ) -> Sequence[AgentRow]:
        """
        Filter agents by architecture compatibility.

        Args:
            agents: List of available agents
            requested_architecture: Required architecture

        Returns:
            List of agents with compatible architecture
        """
        return [agent for agent in agents if agent.architecture == requested_architecture]

    async def select_agent(
        self,
        agents: Sequence[AgentRow],
        requested_slots: ResourceSlot,
        requested_architecture: Optional[str] = None,
        **kwargs,
    ) -> Optional[AgentId]:
        """
        Select an agent from the available agents.

        This method should be overridden by subclasses to implement
        specific selection strategies.

        Args:
            agents: List of available agents
            requested_slots: Resources requested
            requested_architecture: Required architecture (if any)

        Returns:
            Selected agent ID or None if no suitable agent found
        """
        raise NotImplementedError("Subclasses must implement select_agent method")
