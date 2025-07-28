from abc import ABC, abstractmethod


class SchedulerValidator(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError("Subclasses must implement the 'name' property.")

    @abstractmethod
    async def validate(self) -> None:
        """
        Validate the scheduler state.
        This method should be implemented by subclasses to define
        how the scheduler state is validated.
        """
        raise NotImplementedError("Subclasses must implement the 'validate' method.")
