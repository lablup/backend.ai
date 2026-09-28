import asyncio
import logging
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.contexts.request_id import with_request_context
from ai.backend.logging.structured import StructuredLogger, with_log_context
from ai.backend.manager.reporters.base import (
    AbstractReporter,
    FinishedActionMessage,
    StartedActionMessage,
)

log = StructuredLogger(logging.getLogger(__spec__.name))


@dataclass
class ReporterHubArgs:
    reporters: dict[str, list[AbstractReporter]]  # Key: action type, Value: reporter instance


class ReporterHub(AbstractReporter):
    _start_queue: asyncio.Queue[StartedActionMessage]
    _finish_queue: asyncio.Queue[FinishedActionMessage]
    _reporters: dict[str, list[AbstractReporter]]  # Key: action type, Value: reporters list
    _closed: bool
    _start_task: asyncio.Task[Any]
    _finish_task: asyncio.Task[Any]

    def __init__(self, args: ReporterHubArgs) -> None:
        self._start_queue = asyncio.Queue()
        self._finish_queue = asyncio.Queue()
        self._reporters = args.reporters
        self._closed = False
        self._start_task = asyncio.create_task(self._report_started())
        self._finish_task = asyncio.create_task(self._report_finished())

    @override
    async def report_started(self, message: StartedActionMessage) -> None:
        await self._start_queue.put(message)

    @override
    async def report_finished(self, message: FinishedActionMessage) -> None:
        await self._finish_queue.put(message)

    def _target_reporters(self, action_type: str) -> list[AbstractReporter]:
        return self._reporters.get(action_type, [])

    async def _report_started(self) -> None:
        while not self._closed:
            message = await self._start_queue.get()
            target_reporters = self._target_reporters(message.action_type)
            with self._action_scope(message):
                for reporter in target_reporters:
                    try:
                        await reporter.report_started(message)
                    except Exception:
                        log.exception(
                            "reporter report_started failed", reporter_type=type(reporter).__name__
                        )

    async def _report_finished(self) -> None:
        while not self._closed:
            message = await self._finish_queue.get()
            target_reporters = self._target_reporters(message.action_type)
            with self._action_scope(message):
                for reporter in target_reporters:
                    try:
                        await reporter.report_finished(message)
                    except Exception:
                        log.exception(
                            "reporter report_finished failed", reporter_type=type(reporter).__name__
                        )

    @contextmanager
    def _action_scope(
        self, message: StartedActionMessage | FinishedActionMessage
    ) -> Iterator[None]:
        with ExitStack() as stack:
            stack.enter_context(
                with_log_context(action_id=message.action_id, action_name=message.action_type)
            )
            if message.request_id is not None:
                stack.enter_context(with_request_context(message.request_id))
            yield

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._start_task.cancel()
        self._finish_task.cancel()
