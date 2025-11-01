from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

from ..types import BgtaskNameBase


class BaseBackgroundTaskArgs(BaseModel):
    """
    Base class for background task arguments using Pydantic.
    Provides automatic serialization/deserialization via model_dump() and model_validate().
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class BaseBackgroundTaskResult(ABC):
    """
    Abstract base class for background task results.
    This represents the result of a background task execution.
    Similar to BaseActionResult, each result should provide entity identification
    and serialization capabilities.
    """

    @abstractmethod
    def entity_id(self) -> Optional[str]:
        """
        Return the ID of the entity this task result relates to.
        Returns None if the task doesn't operate on a specific entity.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def serialize(self) -> Optional[str]:
        """
        Serialize the task result to a string for storage.
        Returns None if there's no data to serialize.
        """
        raise NotImplementedError("Subclasses must implement this method")


class EmptyTaskResult(BaseBackgroundTaskResult):
    """Result class for tasks that don't produce meaningful output."""

    def entity_id(self) -> Optional[str]:
        return None

    def serialize(self) -> Optional[str]:
        return None


TFunctionArgs = TypeVar("TFunctionArgs", bound=BaseBackgroundTaskArgs)


class BaseBackgroundTaskHandler(Generic[TFunctionArgs], ABC):
    @classmethod
    @abstractmethod
    def name(cls) -> BgtaskNameBase:
        """
        Return the name of the background task.
        This method should be implemented by subclasses to provide
        the specific task name.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    @abstractmethod
    def args_type(cls) -> type[TFunctionArgs]:
        """
        Return the type of arguments that this task expects.
        This method should be implemented by subclasses to provide
        the specific argument type.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    async def execute(self, args: TFunctionArgs) -> BaseBackgroundTaskResult:
        """
        Execute the background task with the provided reporter and arguments.
        This method should be implemented by subclasses to provide
        the specific execution logic.
        """
        raise NotImplementedError("Subclasses must implement this method")
