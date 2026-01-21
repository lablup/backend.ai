from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock

import pytest

from ai.backend.common.bgtask.reporter import ProgressReporter
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.bgtask.broadcast import BgtaskUpdatedEvent
from ai.backend.common.events.types import EventCacheDomain


@pytest.fixture
def mock_event_producer() -> AsyncMock:
    producer = AsyncMock(spec=EventProducer)
    producer.broadcast_event_with_cache = AsyncMock()
    return producer


@pytest.fixture
def task_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def progress_reporter(mock_event_producer: AsyncMock, task_id: uuid.UUID) -> ProgressReporter:
    return ProgressReporter(
        event_producer=mock_event_producer,
        task_id=task_id,
        current_progress=0,
        total_progress=100,
    )


class TestProgressReporter:
    def test_init(self, mock_event_producer: AsyncMock, task_id: uuid.UUID) -> None:
        reporter = ProgressReporter(mock_event_producer, task_id)
        assert reporter._event_producer == mock_event_producer
        assert reporter._task_id == task_id
        assert reporter.current_progress == 0
        assert reporter.total_progress == 0

    def test_init_with_progress(self, mock_event_producer: AsyncMock, task_id: uuid.UUID) -> None:
        reporter = ProgressReporter(
            mock_event_producer,
            task_id,
            current_progress=10,
            total_progress=100,
        )
        assert reporter.current_progress == 10
        assert reporter.total_progress == 100

    @pytest.mark.asyncio
    async def test_update_without_message(
        self,
        progress_reporter: ProgressReporter,
        mock_event_producer: AsyncMock,
        task_id: uuid.UUID,
    ) -> None:
        await progress_reporter.update(increment=10)

        assert progress_reporter.current_progress == 10
        mock_event_producer.broadcast_event_with_cache.assert_called_once()

        call_args = mock_event_producer.broadcast_event_with_cache.call_args
        assert call_args[0][0] == EventCacheDomain.BGTASK.cache_id(str(task_id))

        event = call_args[0][1]
        assert isinstance(event, BgtaskUpdatedEvent)
        assert event.task_id == task_id
        assert event.message is None
        assert event.current_progress == 10
        assert event.total_progress == 100

    @pytest.mark.asyncio
    async def test_update_with_message(
        self,
        progress_reporter: ProgressReporter,
        mock_event_producer: AsyncMock,
        task_id: uuid.UUID,
    ) -> None:
        await progress_reporter.update(increment=25, message="Processing batch 1")

        assert progress_reporter.current_progress == 25
        mock_event_producer.broadcast_event_with_cache.assert_called_once()

        call_args = mock_event_producer.broadcast_event_with_cache.call_args
        event = call_args[0][1]
        assert isinstance(event, BgtaskUpdatedEvent)
        assert event.message == "Processing batch 1"
        assert event.current_progress == 25
        assert event.total_progress == 100

    @pytest.mark.asyncio
    async def test_multiple_updates(
        self, progress_reporter: ProgressReporter, mock_event_producer: AsyncMock
    ) -> None:
        await progress_reporter.update(increment=10, message="Step 1")
        await progress_reporter.update(increment=20, message="Step 2")
        await progress_reporter.update(increment=30, message="Step 3")

        assert progress_reporter.current_progress == 60
        assert mock_event_producer.broadcast_event_with_cache.call_count == 3

        last_call = mock_event_producer.broadcast_event_with_cache.call_args_list[-1]
        event = last_call[0][1]
        assert event.current_progress == 60
        assert event.message == "Step 3"

    @pytest.mark.asyncio
    async def test_update_with_float_increment(
        self, progress_reporter: ProgressReporter, mock_event_producer: AsyncMock
    ) -> None:
        await progress_reporter.update(increment=10.5)
        assert progress_reporter.current_progress == 10.5

        await progress_reporter.update(increment=20.3)
        assert progress_reporter.current_progress == 30.8

    @pytest.mark.asyncio
    async def test_update_with_zero_increment(
        self, progress_reporter: ProgressReporter, mock_event_producer: AsyncMock
    ) -> None:
        await progress_reporter.update(increment=0, message="Status update")

        assert progress_reporter.current_progress == 0
        mock_event_producer.broadcast_event_with_cache.assert_called_once()

        call_args = mock_event_producer.broadcast_event_with_cache.call_args
        event = call_args[0][1]
        assert event.current_progress == 0
        assert event.message == "Status update"

    @pytest.mark.asyncio
    async def test_update_with_negative_increment(
        self, progress_reporter: ProgressReporter
    ) -> None:
        progress_reporter.current_progress = 50
        await progress_reporter.update(increment=-10)

        assert progress_reporter.current_progress == 40

    @pytest.mark.asyncio
    async def test_concurrent_updates(self, progress_reporter: ProgressReporter) -> None:
        async def update_task(increment: int, message: str):
            await progress_reporter.update(increment=increment, message=message)

        tasks = [
            update_task(10, "Task 1"),
            update_task(20, "Task 2"),
            update_task(30, "Task 3"),
        ]

        await asyncio.gather(*tasks)
        assert progress_reporter.current_progress == 60

    def test_progress_state_persistence(self, progress_reporter: ProgressReporter) -> None:
        progress_reporter.current_progress = 50
        progress_reporter.total_progress = 200

        assert progress_reporter.current_progress == 50
        assert progress_reporter.total_progress == 200

    @pytest.mark.asyncio
    async def test_cache_id_usage(self, mock_event_producer: AsyncMock, task_id: uuid.UUID) -> None:
        reporter = ProgressReporter(mock_event_producer, task_id)
        await reporter.update(increment=1)

        expected_cache_id = EventCacheDomain.BGTASK.cache_id(str(task_id))
        call_args = mock_event_producer.broadcast_event_with_cache.call_args
        assert call_args[0][0] == expected_cache_id
