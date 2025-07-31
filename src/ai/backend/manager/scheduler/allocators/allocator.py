from abc import ABC, abstractmethod
from typing import Optional, Sequence

from ai.backend.common.types import AgentId, ResourceSlot
from ai.backend.manager.models import AgentRow


class SchedulerAllocator(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the name of the allocator.
        This property should be implemented by subclasses to provide
        a unique identifier for the allocator.
        """
        raise NotImplementedError("Subclasses must implement this property.")

    @abstractmethod
    async def allocate(self) -> None:
        """
        Allocate resources for the scheduler.
        This method should be implemented by subclasses to define
        how resources are allocated.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    async def select_agent(
        self,
        agents: Sequence[AgentRow],
        requested_slots: ResourceSlot,
        requested_architecture: Optional[str] = None,
        **kwargs,
    ) -> Optional[AgentId]:
        """
        Select an agent from the available agents.

        Args:
            agents: List of available agents
            requested_slots: Resources requested
            requested_architecture: Required architecture (if any)
            **kwargs: Additional parameters specific to each allocator

        Returns:
            Selected agent ID or None if no suitable agent found
        """
        raise NotImplementedError("Subclasses must implement this method.")
