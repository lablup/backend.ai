from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.bgtask.reporter import ProgressReporter
from ai.backend.common.bgtask.task.base import BaseBackgroundTaskArgs, BaseBackgroundTaskHandler
from ai.backend.common.bgtask.task.registry import BackgroundTaskHandlerRegistry
from ai.backend.common.exception import BgtaskNotRegisteredError
from ai.backend.common.types import DispatchResult

# Mock task names for testing - using actual TaskName values
MOCK_TASK_ONE = "clone_vfolder"  # Matches TaskName.CLONE_VFOLDER
MOCK_TASK_TWO = "push_image"  # Matches TaskName.PUSH_IMAGE


class MockTaskArgs(BaseBackgroundTaskArgs):
    def __init__(self, data: str = "") -> None:
        self.data = data

    def to_metadata_body(self) -> dict[str, Any]:
        return {"data": self.data}

    @classmethod
    def from_metadata_body(cls, body: Mapping[str, Any]) -> MockTaskArgs:
        return cls(data=body.get("data", ""))


class MockTaskOneHandler(BaseBackgroundTaskHandler[MockTaskArgs]):
    async def execute(self, reporter: ProgressReporter, args: MockTaskArgs) -> DispatchResult:
        return DispatchResult(result={"result": f"processed_one: {args.data}"})

    @classmethod
    def name(cls) -> str:  # type: ignore[override]
        return MOCK_TASK_ONE

    @classmethod
    def args_type(cls) -> type[MockTaskArgs]:
        return MockTaskArgs


class MockTaskTwoHandler(BaseBackgroundTaskHandler[MockTaskArgs]):
    async def execute(self, reporter: ProgressReporter, args: MockTaskArgs) -> DispatchResult:
        return DispatchResult(result={"result": f"processed_two: {args.data}"})

    @classmethod
    def name(cls) -> str:  # type: ignore[override]
        return MOCK_TASK_TWO

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
        handler = MockTaskOneHandler()

        registry.register(handler)

        assert MOCK_TASK_ONE in registry._registry
        assert registry._registry[MOCK_TASK_ONE] == handler  # type: ignore[index]

    def test_register_multiple_tasks(self) -> None:
        registry = BackgroundTaskHandlerRegistry()
        handler_one = MockTaskOneHandler()
        handler_two = MockTaskTwoHandler()

        registry.register(handler_one)
        registry.register(handler_two)

        assert len(registry._registry) == 2
        assert registry._registry[MOCK_TASK_ONE] == handler_one  # type: ignore[index]
        assert registry._registry[MOCK_TASK_TWO] == handler_two  # type: ignore[index]

    def test_get_registered_task(self) -> None:
        registry = BackgroundTaskHandlerRegistry()
        handler = MockTaskOneHandler()
        registry.register(handler)

        retrieved_handler = registry.get_task(MOCK_TASK_ONE)  # type: ignore[arg-type]

        assert retrieved_handler == handler
        assert retrieved_handler.name() == MOCK_TASK_ONE

    def test_get_unregistered_task(self) -> None:
        registry = BackgroundTaskHandlerRegistry()

        with pytest.raises(BgtaskNotRegisteredError):
            registry.get_task(MOCK_TASK_ONE)  # type: ignore[arg-type]

    def test_override_registered_task(self) -> None:
        registry = BackgroundTaskHandlerRegistry()

        class CustomTaskOneHandler(BaseBackgroundTaskHandler[MockTaskArgs]):
            async def execute(
                self, reporter: ProgressReporter, args: MockTaskArgs
            ) -> DispatchResult:
                return DispatchResult(result={"result": "custom task one"})

            @classmethod
            def name(cls) -> str:  # type: ignore[override]
                return MOCK_TASK_ONE

            @classmethod
            def args_type(cls) -> type[MockTaskArgs]:
                return MockTaskArgs

        original_handler = MockTaskOneHandler()
        custom_handler = CustomTaskOneHandler()

        registry.register(original_handler)
        assert registry._registry[MOCK_TASK_ONE] == original_handler  # type: ignore[index]

        registry.register(custom_handler)
        assert registry._registry[MOCK_TASK_ONE] == custom_handler  # type: ignore[index]

    def test_get_task_after_override(self) -> None:
        registry = BackgroundTaskHandlerRegistry()

        original_handler = MockTaskOneHandler()
        registry.register(original_handler)

        handler_two = MockTaskTwoHandler()
        registry.register(handler_two)

        retrieved_one = registry.get_task(MOCK_TASK_ONE)  # type: ignore[arg-type]
        retrieved_two = registry.get_task(MOCK_TASK_TWO)  # type: ignore[arg-type]

        assert retrieved_one == original_handler
        assert retrieved_two == handler_two

    def test_registry_isolation(self) -> None:
        registry1 = BackgroundTaskHandlerRegistry()
        registry2 = BackgroundTaskHandlerRegistry()

        handler1 = MockTaskOneHandler()
        handler2 = MockTaskTwoHandler()

        registry1.register(handler1)
        registry2.register(handler2)

        assert MOCK_TASK_ONE in registry1._registry
        assert MOCK_TASK_ONE not in registry2._registry

        assert MOCK_TASK_TWO not in registry1._registry
        assert MOCK_TASK_TWO in registry2._registry

    @pytest.mark.asyncio
    async def test_registered_handler_execution(self) -> None:
        registry = BackgroundTaskHandlerRegistry()
        handler = MockTaskOneHandler()
        registry.register(handler)

        retrieved_handler = registry.get_task(MOCK_TASK_ONE)  # type: ignore[arg-type]
        args = MockTaskArgs(data="test-data")
        reporter = AsyncMock(spec=ProgressReporter)

        result = await retrieved_handler.execute(reporter, args)

        assert result.result is not None
        assert result.result["result"] == "processed_one: test-data"

    def test_get_multiple_unregistered_tasks(self) -> None:
        registry = BackgroundTaskHandlerRegistry()

        with pytest.raises(BgtaskNotRegisteredError):
            registry.get_task(MOCK_TASK_ONE)  # type: ignore[arg-type]

        with pytest.raises(BgtaskNotRegisteredError):
            registry.get_task(MOCK_TASK_TWO)  # type: ignore[arg-type]
