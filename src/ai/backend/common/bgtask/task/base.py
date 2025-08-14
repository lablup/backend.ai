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

    @abstractmethod
    @classmethod
    def from_metadata_body(cls, body: Mapping[str, Any]) -> Self:
        """
        Create an instance from a metadata body dictionary.
        This method should be implemented by subclasses to provide
        the specific conversion logic.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        """
        Convert the arguments to a dictionary representation.
        This method should be implemented by subclasses to provide
        the specific conversion logic.
        """
        raise NotImplementedError("Subclasses must implement this method")


TFunctionArgs = TypeVar("TFunctionArgs", bound=BaseBackgroundTaskArgs)
TFunctionContext = TypeVar("TFunctionContext")


class BaseBackgroundTask(Generic[TFunctionArgs, TFunctionContext], ABC):
    def __init__(self, context: TFunctionContext) -> None:
        self._context = context

    @abstractmethod
    @staticmethod
    async def execute(
        reporter: ProgressReporter, args: TFunctionArgs
    ) -> DispatchResult | str | None:
        """
        Execute the background task with the provided reporter and arguments.
        This method should be implemented by subclasses to provide
        the specific execution logic.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    @classmethod
    def name(cls) -> TaskName:
        """
        Return the name of the background task.
        This method should be implemented by subclasses to provide
        the specific task name.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    @classmethod
    def get_args_from_metadata(cls, body: Mapping[str, Any]) -> TFunctionArgs:
        """
        Return the type of arguments that this task accepts.
        This method should be implemented by subclasses to provide
        the specific argument type.
        """
        raise NotImplementedError("Subclasses must implement this method")
