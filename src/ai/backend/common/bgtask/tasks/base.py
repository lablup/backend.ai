from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar


class BaseBackgroundTaskFunctionArgs(ABC):
    @abstractmethod
    def to_metadata_body(self) -> dict[str, Any]:
        """
        Convert the arguments to a metadata body dictionary.
        This method should be implemented by subclasses to provide
        the specific conversion logic.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    @classmethod
    def from_metadata_body(cls, body: dict[str, Any]) -> "BaseBackgroundTaskFunctionArgs":
        """
        Create an instance from a metadata body dictionary.
        This method should be implemented by subclasses to provide
        the specific conversion logic.
        """
        raise NotImplementedError("Subclasses must implement this method")


TArgs = TypeVar("TArgs", bound=BaseBackgroundTaskFunctionArgs)


class BaseBackgroundTaskFunction(ABC, Generic[TArgs]):
    """
    Base class for background task functions.
    All background task functions should inherit from this class.
    """

    @abstractmethod
    def execute(self, args: TArgs):
        """
        Execute the background task with the provided arguments.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    @classmethod
    def get_name(cls) -> str:
        """
        Return the name of the background task.
        """
        raise NotImplementedError("Subclasses must implement this method")
