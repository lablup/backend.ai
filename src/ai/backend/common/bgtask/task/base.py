from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, Generic, Optional, Self, TypeVar

from ..types import BgtaskNameBase


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
