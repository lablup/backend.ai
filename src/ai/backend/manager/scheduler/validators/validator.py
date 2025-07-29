from abc import ABC, abstractmethod

from ai.backend.manager.scheduler.validators.types import ValidatorContext


class SchedulerValidator(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError("Subclasses must implement the 'name' property.")

    @abstractmethod
    async def validate(self, context: ValidatorContext) -> None:
        """
        Validate the scheduler state.
        This method should be implemented by subclasses to define
        how the scheduler state is validated.

        Raises:
            SchedulerValidationError: If validation fails
        """
        raise NotImplementedError("Subclasses must implement the 'validate' method.")
