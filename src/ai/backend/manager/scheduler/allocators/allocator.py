from abc import ABC, abstractmethod


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
