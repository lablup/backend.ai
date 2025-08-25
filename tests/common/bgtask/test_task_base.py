from __future__ import annotations

from typing import Any, Mapping

import pytest

from ai.backend.common.bgtask.reporter import ProgressReporter
from ai.backend.common.bgtask.task.base import BaseBackgroundTaskArgs, BaseBackgroundTaskHandler
from ai.backend.common.bgtask.types import TaskName
from ai.backend.common.types import DispatchResult


class ConcreteTaskArgs(BaseBackgroundTaskArgs):
    def __init__(self, value: str, count: int = 0):
        self.value = value
        self.count = count

    def to_metadata_body(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "count": self.count,
        }

    @classmethod
    def from_metadata_body(cls, body: Mapping[str, Any]) -> ConcreteTaskArgs:
        return cls(
            value=body.get("value", ""),
            count=body.get("count", 0),
        )


class ConcreteTaskHandler(BaseBackgroundTaskHandler[ConcreteTaskArgs]):
    async def execute(self, reporter: ProgressReporter, args: ConcreteTaskArgs) -> DispatchResult:
        await reporter.update(1, f"Processing {args.value}")
        result = {"processed": args.value, "count": args.count}
        return DispatchResult(result=result)

    @classmethod
    def name(cls) -> TaskName:
        return TaskName.CLONE_VFOLDER

    @classmethod
    def args_type(cls) -> type[ConcreteTaskArgs]:
        return ConcreteTaskArgs


class TestBaseBackgroundTaskArgs:
    def test_abstract_methods_not_implemented(self):
        with pytest.raises(TypeError):
            BaseBackgroundTaskArgs()

    def test_concrete_implementation(self):
        args = ConcreteTaskArgs(value="test", count=5)
        assert args.value == "test"
        assert args.count == 5

    def test_to_metadata_body(self):
        args = ConcreteTaskArgs(value="hello", count=10)
        body = args.to_metadata_body()

        assert isinstance(body, dict)
        assert body["value"] == "hello"
        assert body["count"] == 10

    def test_from_metadata_body(self):
        body = {"value": "world", "count": 20}
        args = ConcreteTaskArgs.from_metadata_body(body)

        assert isinstance(args, ConcreteTaskArgs)
        assert args.value == "world"
        assert args.count == 20

    def test_from_metadata_body_with_missing_fields(self):
        body = {"value": "partial"}
        args = ConcreteTaskArgs.from_metadata_body(body)

        assert args.value == "partial"
        assert args.count == 0

    def test_from_metadata_body_empty(self):
        body = {}
        args = ConcreteTaskArgs.from_metadata_body(body)

        assert args.value == ""
        assert args.count == 0

    def test_round_trip_serialization(self):
        original = ConcreteTaskArgs(value="round-trip", count=42)
        body = original.to_metadata_body()
        restored = ConcreteTaskArgs.from_metadata_body(body)

        assert restored.value == original.value
        assert restored.count == original.count


class TestBaseBackgroundTaskHandler:
    def test_abstract_methods_not_implemented(self):
        with pytest.raises(TypeError):
            BaseBackgroundTaskHandler()

    @pytest.mark.asyncio
    async def test_concrete_handler_execute(self):
        from unittest.mock import AsyncMock

        handler = ConcreteTaskHandler()
        args = ConcreteTaskArgs(value="test-value", count=3)

        reporter = AsyncMock(spec=ProgressReporter)
        reporter.update = AsyncMock()

        result = await handler.execute(reporter, args)

        assert isinstance(result, DispatchResult)
        assert result.result["processed"] == "test-value"
        assert result.result["count"] == 3

        reporter.update.assert_called_once_with(1, "Processing test-value")

    def test_handler_name(self):
        assert ConcreteTaskHandler.name() == TaskName.CLONE_VFOLDER

    def test_handler_args_type(self):
        assert ConcreteTaskHandler.args_type() == ConcreteTaskArgs

    def test_handler_generic_typing(self):
        handler = ConcreteTaskHandler()
        assert isinstance(handler, BaseBackgroundTaskHandler)

    @pytest.mark.asyncio
    async def test_handler_with_empty_args(self):
        from unittest.mock import AsyncMock

        handler = ConcreteTaskHandler()
        args = ConcreteTaskArgs(value="", count=0)

        reporter = AsyncMock(spec=ProgressReporter)
        reporter.update = AsyncMock()

        result = await handler.execute(reporter, args)

        assert result.result["processed"] == ""
        assert result.result["count"] == 0

    @pytest.mark.asyncio
    async def test_handler_with_error_result(self):
        from unittest.mock import AsyncMock

        class ErrorTaskHandler(BaseBackgroundTaskHandler[ConcreteTaskArgs]):
            async def execute(
                self, reporter: ProgressReporter, args: ConcreteTaskArgs
            ) -> DispatchResult:
                return DispatchResult(
                    result={"status": "partial"},
                    errors=["Something went wrong"],
                )

            @classmethod
            def name(cls) -> TaskName:
                return TaskName.PUSH_IMAGE

            @classmethod
            def args_type(cls) -> type[ConcreteTaskArgs]:
                return ConcreteTaskArgs

        handler = ErrorTaskHandler()
        args = ConcreteTaskArgs(value="error-test", count=1)

        reporter = AsyncMock(spec=ProgressReporter)
        result = await handler.execute(reporter, args)

        assert result.has_error()
        assert len(result.errors) == 1
        assert result.errors[0] == "Something went wrong"
