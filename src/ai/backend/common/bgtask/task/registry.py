from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, cast, override

from ai.backend.common.bgtask.types import BgtaskNameBase
from ai.backend.common.exception import (
    BgtaskNotRegisteredError,
)

from .base import (
    BaseBackgroundTaskHandler,
    BaseBackgroundTaskManifest,
    BaseBackgroundTaskResult,
)


class _TaskExecutor(ABC):
    @abstractmethod
    async def revive_task(
        self, manifest_dict: Mapping[str, Any]
    ) -> BaseBackgroundTaskResult | None:
        """
        Revive the background task with the provided manifest dictionary.
        This method should be implemented by subclasses to provide
        the specific revival logic.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    async def execute_new_task(
        self, manifest: BaseBackgroundTaskManifest
    ) -> BaseBackgroundTaskResult | None:
        """
        Execute the background task with the provided manifest.
        This method should be implemented by subclasses to provide
        the specific execution logic.
        """
        raise NotImplementedError("Subclasses must implement this method")


class _TaskDefinition[
    TManifest: BaseBackgroundTaskManifest,
    TResult: BaseBackgroundTaskResult | None,
](_TaskExecutor):
    _handler: BaseBackgroundTaskHandler[TManifest, TResult]
    _task_name: BgtaskNameBase

    def __init__(self, handler: BaseBackgroundTaskHandler[TManifest, TResult]) -> None:
        self._handler = handler
        self._task_name = handler.name()

    def task_name(self) -> BgtaskNameBase:
        return self._task_name

    @override
    async def revive_task(self, manifest_dict: Mapping[str, Any]) -> TResult:
        manifest_instance = self._handler.manifest_type().model_validate(manifest_dict)
        return await self._handler.execute(manifest_instance)

    @override
    async def execute_new_task(self, manifest: BaseBackgroundTaskManifest) -> TResult:
        if not isinstance(manifest, self._handler.manifest_type()):
            raise TypeError(
                f"Expected manifest of type {self._handler.manifest_type()}, got {type(manifest)}"
            )
        return await self._handler.execute(manifest)


class BackgroundTaskHandlerRegistry:
    _executor_registry: dict[str, _TaskDefinition]  # type: ignore[type-arg]

    def __init__(self) -> None:
        self._executor_registry = {}

    def register(self, handler: BaseBackgroundTaskHandler) -> None:  # type: ignore[type-arg]
        self._executor_registry[handler.name().value] = _TaskDefinition(
            handler=handler,
        )

    def get_task_name(self, name: str) -> BgtaskNameBase:
        """Get BgtaskNameBase instance from string name."""
        try:
            definition = self._executor_registry[name]
        except KeyError as e:
            raise BgtaskNotRegisteredError(f"Task '{name}' is not registered.") from e
        return definition.task_name()

    async def revive_task(
        self, name: str, manifest_dict: Mapping[str, Any]
    ) -> BaseBackgroundTaskResult | None:
        try:
            definition = self._executor_registry[name]
        except KeyError as e:
            raise BgtaskNotRegisteredError(f"Task '{name}' is not registered.") from e
        return cast(BaseBackgroundTaskResult | None, await definition.revive_task(manifest_dict))

    async def execute_new_task(
        self, name: BgtaskNameBase, manifest: BaseBackgroundTaskManifest
    ) -> BaseBackgroundTaskResult | None:
        try:
            definition = self._executor_registry[name.value]
        except KeyError as e:
            raise BgtaskNotRegisteredError(f"Task '{name}' is not registered.") from e
        return cast(BaseBackgroundTaskResult | None, await definition.execute_new_task(manifest))
