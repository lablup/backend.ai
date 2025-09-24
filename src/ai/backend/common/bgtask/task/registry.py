from typing import Any, Mapping

from ai.backend.common.exception import (
    BgtaskNotRegisteredError,
)

from ..types import TaskName
from .base import (
    BaseBackgroundTaskArgs,
    BaseBackgroundTaskHandler,
    BaseBackgroundTaskResult,
    TaskExecutor,
)


class BackgroundTaskHandlerRegistry:
    _registry: dict[TaskName, BaseBackgroundTaskHandler]
    _executor_registry: dict[TaskName, TaskExecutor]

    def __init__(self) -> None:
        self._registry = {}
        self._executor_registry = {}

    def register(self, task: BaseBackgroundTaskHandler) -> None:
        self._registry[task.name()] = task

    def get_task(self, name: TaskName) -> BaseBackgroundTaskHandler:
        try:
            return self._registry[name]
        except KeyError:
            raise BgtaskNotRegisteredError

    async def revive_task(
        self, name: TaskName, args: Mapping[str, Any]
    ) -> BaseBackgroundTaskResult:
        try:
            definition = self._executor_registry[name]
        except KeyError:
            raise BgtaskNotRegisteredError(f"Task '{name}' is not registered.")
        return await definition.revive_task(args)

    async def execute_new_task(
        self, name: TaskName, args: BaseBackgroundTaskArgs
    ) -> BaseBackgroundTaskResult:
        try:
            definition = self._executor_registry[name]
        except KeyError:
            raise BgtaskNotRegisteredError(f"Task '{name}' is not registered.")
        return await definition.execute_new_task(args)
