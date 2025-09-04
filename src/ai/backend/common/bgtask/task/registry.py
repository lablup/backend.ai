from ai.backend.common.exception import (
    BgtaskNotRegisteredError,
)

from ..types import TaskName
from .base import BaseBackgroundTaskHandler


class BackgroundTaskHandlerRegistry:
    _registry: dict[TaskName, BaseBackgroundTaskHandler]

    def __init__(self) -> None:
        self._registry = {}

    def register(self, task: BaseBackgroundTaskHandler) -> None:
        self._registry[task.name()] = task

    def get_task(self, name: TaskName) -> BaseBackgroundTaskHandler:
        try:
            return self._registry[name]
        except KeyError:
            raise BgtaskNotRegisteredError
