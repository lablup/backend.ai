from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.bgtask.reporter import ProgressReporter
from ai.backend.common.bgtask.task.base import BaseBackgroundTaskArgs, BaseBackgroundTaskHandler
from ai.backend.common.bgtask.task.registry import BackgroundTaskHandlerRegistry
from ai.backend.common.bgtask.types import TaskName
from ai.backend.common.exception import BgtaskNotRegisteredError
from ai.backend.common.types import DispatchResult


class MockTaskArgs(BaseBackgroundTaskArgs):
    def __init__(self, data: str = "") -> None:
        self.data = data

    def to_metadata_body(self) -> dict[str, Any]:
        return {"data": self.data}

    @classmethod
    def from_metadata_body(cls, body: Mapping[str, Any]) -> MockTaskArgs:
        return cls(data=body.get("data", ""))


class CloneVFolderHandler(BaseBackgroundTaskHandler[MockTaskArgs]):
    async def execute(self, reporter: ProgressReporter, args: MockTaskArgs) -> DispatchResult:
        return DispatchResult(result={"result": f"cloned: {args.data}"})

    @classmethod
    def name(cls) -> TaskName:
        return TaskName.CLONE_VFOLDER

    @classmethod
    def args_type(cls) -> type[MockTaskArgs]:
        return MockTaskArgs


class PushImageHandler(BaseBackgroundTaskHandler[MockTaskArgs]):
    async def execute(self, reporter: ProgressReporter, args: MockTaskArgs) -> DispatchResult:
        return DispatchResult(result={"result": f"pushed: {args.data}"})

    @classmethod
    def name(cls) -> TaskName:
        return TaskName.PUSH_IMAGE

    @classmethod
    def args_type(cls) -> type[MockTaskArgs]:
        return MockTaskArgs


class TestBackgroundTaskHandlerRegistry:
    def test_init(self) -> None:
        registry = BackgroundTaskHandlerRegistry()
        assert hasattr(registry, "_registry")
        assert registry._registry == {}

    def test_register_single_task(self) -> None:
        registry = BackgroundTaskHandlerRegistry()
        handler = CloneVFolderHandler()

        registry.register(handler)

        assert TaskName.CLONE_VFOLDER in registry._registry
        assert registry._registry[TaskName.CLONE_VFOLDER] == handler

    def test_register_multiple_tasks(self) -> None:
        registry = BackgroundTaskHandlerRegistry()
        clone_handler = CloneVFolderHandler()
        push_handler = PushImageHandler()

        registry.register(clone_handler)
        registry.register(push_handler)

        assert len(registry._registry) == 2
        assert registry._registry[TaskName.CLONE_VFOLDER] == clone_handler
        assert registry._registry[TaskName.PUSH_IMAGE] == push_handler

    def test_get_registered_task(self) -> None:
        registry = BackgroundTaskHandlerRegistry()
        handler = CloneVFolderHandler()
        registry.register(handler)

        retrieved_handler = registry.get_task(TaskName.CLONE_VFOLDER)

        assert retrieved_handler == handler
        assert retrieved_handler.name() == TaskName.CLONE_VFOLDER

    def test_get_unregistered_task(self) -> None:
        registry = BackgroundTaskHandlerRegistry()

        with pytest.raises(BgtaskNotRegisteredError):
            registry.get_task(TaskName.CLONE_VFOLDER)

    def test_override_registered_task(self) -> None:
        registry = BackgroundTaskHandlerRegistry()

        class CustomCloneHandler(BaseBackgroundTaskHandler[MockTaskArgs]):
            async def execute(
                self, reporter: ProgressReporter, args: MockTaskArgs
            ) -> DispatchResult:
                return DispatchResult(result={"result": "custom clone"})

            @classmethod
            def name(cls) -> TaskName:
                return TaskName.CLONE_VFOLDER

            @classmethod
            def args_type(cls) -> type[MockTaskArgs]:
                return MockTaskArgs

        original_handler = CloneVFolderHandler()
        custom_handler = CustomCloneHandler()

        registry.register(original_handler)
        assert registry._registry[TaskName.CLONE_VFOLDER] == original_handler

        registry.register(custom_handler)
        assert registry._registry[TaskName.CLONE_VFOLDER] == custom_handler

    def test_get_task_after_override(self) -> None:
        registry = BackgroundTaskHandlerRegistry()

        original_handler = CloneVFolderHandler()
        registry.register(original_handler)

        push_handler = PushImageHandler()
        registry.register(push_handler)

        retrieved_clone = registry.get_task(TaskName.CLONE_VFOLDER)
        retrieved_push = registry.get_task(TaskName.PUSH_IMAGE)

        assert retrieved_clone == original_handler
        assert retrieved_push == push_handler

    def test_registry_isolation(self) -> None:
        registry1 = BackgroundTaskHandlerRegistry()
        registry2 = BackgroundTaskHandlerRegistry()

        handler1 = CloneVFolderHandler()
        handler2 = PushImageHandler()

        registry1.register(handler1)
        registry2.register(handler2)

        assert TaskName.CLONE_VFOLDER in registry1._registry
        assert TaskName.CLONE_VFOLDER not in registry2._registry

        assert TaskName.PUSH_IMAGE not in registry1._registry
        assert TaskName.PUSH_IMAGE in registry2._registry

    @pytest.mark.asyncio
    async def test_registered_handler_execution(self) -> None:
        registry = BackgroundTaskHandlerRegistry()
        handler = CloneVFolderHandler()
        registry.register(handler)

        retrieved_handler = registry.get_task(TaskName.CLONE_VFOLDER)
        args = MockTaskArgs(data="test-data")
        reporter = AsyncMock(spec=ProgressReporter)

        result = await retrieved_handler.execute(reporter, args)

        assert result.result is not None
        assert result.result["result"] == "cloned: test-data"

    def test_get_multiple_unregistered_tasks(self) -> None:
        registry = BackgroundTaskHandlerRegistry()

        with pytest.raises(BgtaskNotRegisteredError):
            registry.get_task(TaskName.CLONE_VFOLDER)

        with pytest.raises(BgtaskNotRegisteredError):
            registry.get_task(TaskName.PUSH_IMAGE)
