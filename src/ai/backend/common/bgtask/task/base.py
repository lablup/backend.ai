from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, Generic, Optional, Self, TypeVar

from ..types import TaskName


class BaseBackgroundTaskArgs(ABC):
    @abstractmethod
    def to_redis_json(self) -> Mapping[str, Any]:
        """
        Convert the instance to a metadata body dictionary.
        This method should be implemented by subclasses to provide
        the specific conversion logic.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    @abstractmethod
    def from_redis_json(cls, body: Mapping[str, Any]) -> Self:
        """
        Create an instance from the given metadata body dictionary.
        This method should be implemented by subclasses to provide
        the specific loading logic.
        """
        raise NotImplementedError("Subclasses must implement this method")


class BaseBackgroundTaskResult(ABC):
    """
    Abstract base class for background task results.
    This represents the result of a background task execution.
    """

    @abstractmethod
    def serialize(self) -> Optional[str]:
        """Serialize the task result to a string."""
        raise NotImplementedError("Subclasses must implement this method")


class EmptyTaskResult(BaseBackgroundTaskResult):
    def serialize(self) -> Optional[str]:
        return None


TFunctionArgs = TypeVar("TFunctionArgs", bound=BaseBackgroundTaskArgs)


class BaseBackgroundTaskHandler(Generic[TFunctionArgs], ABC):
    @classmethod
    @abstractmethod
    def name(cls) -> TaskName:
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
