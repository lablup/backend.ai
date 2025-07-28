from abc import ABC, abstractmethod


class SchedulerPolicy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the name of the policy.
        This property should be implemented by subclasses to provide
        a unique identifier for the policy.
        """
        raise NotImplementedError("Subclasses must implement this property.")

    @abstractmethod
    async def apply(self) -> None:
        """
        Apply the scheduling policy.
        This method should be implemented by subclasses to define
        how the policy is applied to the scheduler.
        """
        raise NotImplementedError("Subclasses must implement this method.")
