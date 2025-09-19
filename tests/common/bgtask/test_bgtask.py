from __future__ import annotations

import asyncio
import uuid
from collections.abc import Mapping
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from ai.backend.common.bgtask.bgtask import (
    BackgroundTaskManager,
    BackgroundTaskObserver,
    BgTaskInfo,
    NopBackgroundTaskObserver,
)
from ai.backend.common.bgtask.reporter import ProgressReporter
from ai.backend.common.bgtask.task.base import BaseBackgroundTaskArgs, BaseBackgroundTaskHandler
from ai.backend.common.bgtask.task.registry import BackgroundTaskHandlerRegistry
from ai.backend.common.bgtask.types import BackgroundTaskDetailMetadata, BgtaskStatus, TaskID
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.bgtask.broadcast import (
    BgtaskDoneEvent,
    BgtaskFailedEvent,
    BgtaskPartialSuccessEvent,
)
from ai.backend.common.exception import BgtaskFailedError
from ai.backend.common.types import DispatchResult

# Use actual TaskName enum values as string constants to avoid direct enum references
MOCK_TASK = "clone_vfolder"  # Matches TaskName.CLONE_VFOLDER value
MOCK_TASK_ONE = "clone_vfolder"
MOCK_TASK_TWO = "push_image"  # Matches TaskName.PUSH_IMAGE value


class MockBackgroundTaskArgs(BaseBackgroundTaskArgs):
    def __init__(self, test_value: str = "test"):
        self.test_value = test_value

    def to_metadata_body(self) -> dict[str, Any]:
        return {"test_value": self.test_value}

    @classmethod
    def from_metadata_body(cls, body: Mapping[str, Any]) -> MockBackgroundTaskArgs:
        return cls(test_value=body.get("test_value", "test"))


class MockBackgroundTaskHandler(BaseBackgroundTaskHandler[MockBackgroundTaskArgs]):
    async def execute(self, args: MockBackgroundTaskArgs) -> DispatchResult:
        return DispatchResult(result={"result": "success"})

    @classmethod
    def name(cls) -> str:  # type: ignore[override]
        return MOCK_TASK

    @classmethod
    def args_type(cls) -> type[MockBackgroundTaskArgs]:
        return MockBackgroundTaskArgs


@pytest.fixture
def mock_event_producer() -> AsyncMock:
    producer = AsyncMock(spec=EventProducer)
    producer.broadcast_event_with_cache = AsyncMock()
    return producer


@pytest.fixture
def mock_valkey_client() -> AsyncMock:
    client = AsyncMock(spec=ValkeyBgtaskClient)
    client.register_task = AsyncMock()
    client.unregister_task = AsyncMock()
    client.heartbeat = AsyncMock()
    client.list_timeout_tasks_by_server_id = AsyncMock(return_value=[])
    client.list_timeout_tasks_by_tags = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_task_registry() -> BackgroundTaskHandlerRegistry:
    registry = BackgroundTaskHandlerRegistry()
    registry.register(MockBackgroundTaskHandler())
    return registry


@pytest.fixture
def mock_observer() -> Mock:
    observer = Mock(spec=BackgroundTaskObserver)
    observer.observe_bgtask_started = Mock()
    observer.observe_bgtask_done = Mock()
    return observer


@pytest.fixture
async def background_task_manager(
    mock_event_producer: AsyncMock,
    mock_valkey_client: AsyncMock,
    mock_task_registry: BackgroundTaskHandlerRegistry,
    mock_observer: Mock,
):
    manager = BackgroundTaskManager(
        mock_event_producer,
        task_registry=mock_task_registry,
        valkey_client=mock_valkey_client,
        server_id="test-server",
        tags={"test-tag"},
        bgtask_observer=mock_observer,
    )
    yield manager
    await manager.shutdown()


class TestBgTaskInfo:
    def test_started(self) -> None:
        info = BgTaskInfo.started("Starting task")
        assert info.status == BgtaskStatus.STARTED
        assert info.msg == "Starting task"
        assert info.current == "0"
        assert info.total == "0"
        assert float(info.started_at) > 0
        assert info.started_at == info.last_update

    def test_finished(self) -> None:
        info = BgTaskInfo.finished(BgtaskStatus.DONE, "Task completed")
        assert info.status == BgtaskStatus.DONE
        assert info.msg == "Task completed"
        assert info.started_at == "0"
        assert float(info.last_update) > 0
        assert info.current == "0"
        assert info.total == "0"

    def test_to_dict(self) -> None:
        info = BgTaskInfo.started("Test")
        data = info.to_dict()
        assert "status" in data
        assert "msg" in data
        assert "started_at" in data
        assert "last_update" in data
        assert "current" in data
        assert "total" in data
        assert data["status"] == str(BgtaskStatus.STARTED)
        assert data["msg"] == "Test"


class TestNopBackgroundTaskObserver:
    def test_nop_observer(self) -> None:
        observer = NopBackgroundTaskObserver()
        observer.observe_bgtask_started(task_name="test")
        observer.observe_bgtask_done(task_name="test", status="done", duration=1.0, error_code=None)


class TestBackgroundTaskManager:
    @pytest.mark.asyncio
    async def test_init(
        self, mock_event_producer: AsyncMock, mock_valkey_client: AsyncMock
    ) -> None:
        manager = BackgroundTaskManager(
            mock_event_producer,
            valkey_client=mock_valkey_client,
            server_id="test-server",
        )
        assert manager._server_id == "test-server"
        assert manager._tags == set()
        assert manager._ongoing_tasks == {}
        await manager.shutdown()

    @pytest.mark.asyncio
    async def test_init_with_tags(
        self, mock_event_producer: AsyncMock, mock_valkey_client: AsyncMock
    ) -> None:
        manager = BackgroundTaskManager(
            mock_event_producer,
            valkey_client=mock_valkey_client,
            server_id="test-server",
            tags=["tag1", "tag2"],
        )
        assert manager._tags == {"tag1", "tag2"}
        await manager.shutdown()

    @pytest.mark.asyncio
    async def test_start_simple_task(self, background_task_manager: BackgroundTaskManager) -> None:
        async def simple_task(reporter: ProgressReporter, value: str) -> str:
            await reporter.update(1, "Processing")
            return f"Result: {value}"

        task_id = await background_task_manager.start(simple_task, name="simple", value="test")
        assert isinstance(task_id, uuid.UUID)
        assert TaskID(task_id) in background_task_manager._ongoing_tasks

        await asyncio.sleep(0.1)
        assert TaskID(task_id) not in background_task_manager._ongoing_tasks

    @pytest.mark.asyncio
    async def test_start_task_with_exception(
        self, background_task_manager: BackgroundTaskManager, mock_observer: Mock
    ) -> None:
        async def failing_task(reporter: ProgressReporter) -> None:
            raise ValueError("Test error")

        await background_task_manager.start(failing_task, name="failing")
        await asyncio.sleep(0.1)

        mock_observer.observe_bgtask_started.assert_called_with(task_name="failing")
        mock_observer.observe_bgtask_done.assert_called()
        call_args = mock_observer.observe_bgtask_done.call_args
        assert call_args.kwargs["status"] == BgtaskStatus.FAILED
        assert call_args.kwargs["task_name"] == "failing"

    @pytest.mark.asyncio
    async def test_start_task_with_backend_error(
        self, background_task_manager: BackgroundTaskManager, mock_observer: Mock
    ) -> None:
        async def backend_error_task(reporter: ProgressReporter) -> None:
            raise BgtaskFailedError("Backend error")

        await background_task_manager.start(backend_error_task, name="backend_error")
        await asyncio.sleep(0.1)

        mock_observer.observe_bgtask_done.assert_called()
        call_args = mock_observer.observe_bgtask_done.call_args
        assert call_args.kwargs["status"] == BgtaskStatus.FAILED

    @pytest.mark.asyncio
    async def test_start_task_cancelled(
        self, background_task_manager: BackgroundTaskManager, mock_observer: Mock
    ) -> None:
        cancel_event = asyncio.Event()

        async def long_task(reporter: ProgressReporter) -> None:
            cancel_event.set()  # Signal that we're ready to be cancelled
            await asyncio.sleep(10)

        task_id = await background_task_manager.start(long_task, name="long")

        # Wait for the task to be ready
        await cancel_event.wait()

        task = background_task_manager._ongoing_tasks[TaskID(task_id)]
        task.cancel()

        # Wait for the cancellation to propagate
        await asyncio.sleep(0.1)

        mock_observer.observe_bgtask_done.assert_called()
        call_args = mock_observer.observe_bgtask_done.call_args
        assert call_args.kwargs["status"] == BgtaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_start_retriable(self, background_task_manager: BackgroundTaskManager) -> None:
        args = MockBackgroundTaskArgs("test_value")
        task_id = await background_task_manager.start_retriable(
            "mock_task_name",
            MOCK_TASK,  # type: ignore[arg-type]
            args,
            tags=["test-tag"],
        )

        assert isinstance(task_id, uuid.UUID)
        assert task_id in background_task_manager._ongoing_tasks

        await asyncio.sleep(0.1)
        assert task_id not in background_task_manager._ongoing_tasks

    @pytest.mark.asyncio
    async def test_convert_bgtask_to_event(
        self, background_task_manager: BackgroundTaskManager
    ) -> None:
        task_id = uuid.uuid4()

        event = background_task_manager._convert_bgtask_to_event(task_id, None)
        assert isinstance(event, BgtaskDoneEvent)
        assert event.task_id == task_id
        assert event.message is None

        event = background_task_manager._convert_bgtask_to_event(task_id, "Success")
        assert isinstance(event, BgtaskDoneEvent)
        assert event.message == "Success"

        result = DispatchResult(result={"test": "data"})
        event = background_task_manager._convert_bgtask_to_event(task_id, result)
        assert isinstance(event, BgtaskDoneEvent)

        result_with_error = DispatchResult(result={"test": "data"}, errors=["test error"])
        event = background_task_manager._convert_bgtask_to_event(task_id, result_with_error)
        assert isinstance(event, BgtaskPartialSuccessEvent)
        assert event.errors == ["test error"]

    @pytest.mark.asyncio
    async def test_heartbeat_loop(
        self, background_task_manager: BackgroundTaskManager, mock_valkey_client: AsyncMock
    ) -> None:
        # The heartbeat loop runs periodically - we'll just check that the task starts
        async def long_task(reporter: ProgressReporter) -> None:
            await asyncio.sleep(0.01)

        task_id = await background_task_manager.start(long_task)

        # Task should be in ongoing_tasks initially
        assert TaskID(task_id) in background_task_manager._ongoing_tasks

        # Wait for task to complete
        await asyncio.sleep(0.1)

        # Task should be removed after completion
        assert TaskID(task_id) not in background_task_manager._ongoing_tasks

    @pytest.mark.asyncio
    async def test_retry_loop_server_tasks(
        self,
        background_task_manager: BackgroundTaskManager,
        mock_valkey_client: AsyncMock,
        mock_task_registry: BackgroundTaskHandlerRegistry,
    ) -> None:
        metadata = BackgroundTaskDetailMetadata.create(
            task_key="mock_task_key",
            task_id=TaskID(uuid.uuid4()),
            task_name=MOCK_TASK,  # type: ignore[arg-type]
            body={"test_value": "retry"},
            server_id="old-server",
        )
        mock_valkey_client.list_timeout_tasks_by_server_id.return_value = [metadata]

        await background_task_manager._check_server_tasks()

        assert metadata.task_id in background_task_manager._ongoing_tasks
        assert metadata.server_id == "test-server"

    @pytest.mark.asyncio
    async def test_retry_loop_tagged_tasks(
        self, background_task_manager: BackgroundTaskManager, mock_valkey_client: AsyncMock
    ) -> None:
        metadata = BackgroundTaskDetailMetadata.create(
            task_key="mock_task_key",
            task_id=TaskID(uuid.uuid4()),
            task_name=MOCK_TASK,  # type: ignore[arg-type]
            body={"test_value": "retry"},
            server_id="old-server",
            tags=["test-tag"],
        )
        mock_valkey_client.list_timeout_tasks_by_tags.return_value = [metadata]

        await background_task_manager._check_tagged_tasks()

        assert metadata.task_id in background_task_manager._ongoing_tasks

    @pytest.mark.asyncio
    async def test_retry_task_not_registered(
        self, background_task_manager: BackgroundTaskManager, mock_valkey_client: AsyncMock
    ) -> None:
        metadata = BackgroundTaskDetailMetadata.create(
            task_key="mock_task_key",
            task_id=TaskID(uuid.uuid4()),
            task_name=MOCK_TASK_TWO,  # type: ignore[arg-type]
            body={"test": "data"},
            server_id="old-server",
        )

        await background_task_manager._retry_bgtask(metadata)
        assert metadata.task_id not in background_task_manager._ongoing_tasks

    @pytest.mark.asyncio
    async def test_shutdown(
        self, mock_event_producer: AsyncMock, mock_valkey_client: AsyncMock
    ) -> None:
        manager = BackgroundTaskManager(
            mock_event_producer,
            valkey_client=mock_valkey_client,
            server_id="test-server",
        )

        async def long_task(reporter: ProgressReporter) -> None:
            await asyncio.sleep(10)

        task_id = await manager.start(long_task)
        assert TaskID(task_id) in manager._ongoing_tasks

        await manager.shutdown()

        # All tasks should be cancelled or done
        for task in manager._ongoing_tasks.values():
            assert task.done() or task.cancelled()

    @pytest.mark.asyncio
    async def test_task_with_dispatch_result(
        self, background_task_manager: BackgroundTaskManager
    ) -> None:
        async def task_with_result(reporter: ProgressReporter) -> DispatchResult:
            await reporter.update(1, "Processing")
            return DispatchResult(result={"result": "success"})

        task_id = await background_task_manager.start(task_with_result, name="result_task")
        await asyncio.sleep(0.1)

        assert TaskID(task_id) not in background_task_manager._ongoing_tasks

    @pytest.mark.asyncio
    async def test_observe_retriable_bgtask_with_exception(
        self, background_task_manager: BackgroundTaskManager, mock_observer: Mock
    ) -> None:
        class FailingHandler(BaseBackgroundTaskHandler[MockBackgroundTaskArgs]):
            async def execute(self, args: MockBackgroundTaskArgs) -> DispatchResult:
                raise ValueError("Test error")

            @classmethod
            def name(cls) -> str:  # type: ignore[override]
                return MOCK_TASK

            @classmethod
            def args_type(cls) -> type[MockBackgroundTaskArgs]:
                return MockBackgroundTaskArgs

        handler = FailingHandler()
        args = MockBackgroundTaskArgs()
        metadata = BackgroundTaskDetailMetadata.create(
            task_key="mock_task_key",
            task_id=TaskID(uuid.uuid4()),
            task_name=MOCK_TASK,  # type: ignore[arg-type]
            body=args.to_metadata_body(),
            server_id="test-server",
        )

        event = await background_task_manager._observe_retriable_bgtask(handler, args, metadata)

        assert isinstance(event, BgtaskFailedEvent)
        assert event.message is not None
        assert "ValueError" in event.message
