from abc import ABC, abstractmethod
from typing import Any, Generic, Mapping, override

from ai.backend.common.exception import (
    BgtaskNotRegisteredError,
)

from ..types import TaskName
from .base import (
    BaseBackgroundTaskArgs,
    BaseBackgroundTaskHandler,
    BaseBackgroundTaskResult,
    TFunctionArgs,
)


class _TaskExecutor(ABC):
    @abstractmethod
    async def revive_task(self, args: Mapping[str, Any]) -> BaseBackgroundTaskResult:
        """
        Revive the background task with the provided arguments.
        This method should be implemented by subclasses to provide
        the specific revival logic.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    async def execute_new_task(self, args: BaseBackgroundTaskArgs) -> BaseBackgroundTaskResult:
        """
        Execute the background task with the provided reporter and arguments.
        This method should be implemented by subclasses to provide
        the specific execution logic.
        """
        raise NotImplementedError("Subclasses must implement this method")


class _TaskDefinition(_TaskExecutor, Generic[TFunctionArgs]):
    _handler: BaseBackgroundTaskHandler[TFunctionArgs]
    _task_name: TaskName

    def __init__(self, handler: BaseBackgroundTaskHandler[TFunctionArgs]) -> None:
        self._handler = handler
        self._task_name = handler.name()

    def task_name(self) -> TaskName:
        return self._task_name

    @override
    async def revive_task(self, args: Mapping[str, Any]) -> BaseBackgroundTaskResult:
        args_instance = self._handler.args_type().model_validate(args)
        return await self._handler.execute(args_instance)

    @override
    async def execute_new_task(self, args: BaseBackgroundTaskArgs) -> BaseBackgroundTaskResult:
        if not isinstance(args, self._handler.args_type()):
            raise TypeError(f"Expected args of type {self._handler.args_type()}, got {type(args)}")
        return await self._handler.execute(args)


class BackgroundTaskHandlerRegistry:
    _executor_registry: dict[str, _TaskDefinition]

    def __init__(self) -> None:
        self._executor_registry = {}

    def register(self, handler: BaseBackgroundTaskHandler) -> None:
        self._executor_registry[handler.name().value] = _TaskDefinition(
            handler=handler,
        )

    def get_task_name(self, name: str) -> TaskName:
        """Get TaskName instance from string name."""
        try:
            definition = self._executor_registry[name]
        except KeyError:
            raise BgtaskNotRegisteredError(f"Task '{name}' is not registered.")
        return definition.task_name()

    async def revive_task(self, name: str, args: Mapping[str, Any]) -> BaseBackgroundTaskResult:
        try:
            definition = self._executor_registry[name]
        except KeyError:
            raise BgtaskNotRegisteredError(f"Task '{name}' is not registered.")
        return await definition.revive_task(args)

    async def execute_new_task(
        self, name: TaskName, args: BaseBackgroundTaskArgs
    ) -> BaseBackgroundTaskResult:
        try:
            definition = self._executor_registry[name.value]
        except KeyError:
            raise BgtaskNotRegisteredError(f"Task '{name}' is not registered.")
        return await definition.execute_new_task(args)
