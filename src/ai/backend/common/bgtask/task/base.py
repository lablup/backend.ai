from abc import ABC, abstractmethod
from typing import Generic, TypeVar

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


class BaseBackgroundTaskResult(BaseModel):
    """
    Base class for background task results using Pydantic.
    Provides automatic serialization/deserialization via model_dump() and model_validate().
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class EmptyTaskResult(BaseBackgroundTaskResult):
    """Result class for tasks that don't produce meaningful output."""

    pass


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
