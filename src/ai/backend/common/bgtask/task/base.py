from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, Generic, Self, TypeVar

from ai.backend.common.types import DispatchResult

from ..reporter import ProgressReporter
from ..types import TaskName


class BaseBackgroundTaskArgs(ABC):
    @abstractmethod
    def to_metadata_body(self) -> dict[str, Any]:
        """
        Convert the arguments to a metadata body dictionary.
        This method should be implemented by subclasses to provide
        the specific conversion logic.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    @abstractmethod
    def from_metadata_body(cls, body: Mapping[str, Any]) -> Self:
        """
        Create an instance from a metadata body dictionary.
        This method should be implemented by subclasses to provide
        the specific conversion logic.
        """
        raise NotImplementedError("Subclasses must implement this method")


TFunctionArgs = TypeVar("TFunctionArgs", bound=BaseBackgroundTaskArgs)


class BaseBackgroundTaskHandler(Generic[TFunctionArgs], ABC):
    @abstractmethod
    async def execute(self, reporter: ProgressReporter, args: TFunctionArgs) -> DispatchResult:
        """
        Execute the background task with the provided reporter and arguments.
        This method should be implemented by subclasses to provide
        the specific execution logic.
        """
        raise NotImplementedError("Subclasses must implement this method")

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
