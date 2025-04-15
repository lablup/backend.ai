import asyncio
import logging
from dataclasses import dataclass
from typing import override

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.reporters.base import (
    AbstractReporter,
    FinishedActionMessage,
    StartedActionMessage,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class ReporterHubArgs:
    reporters: dict[str, list[AbstractReporter]]  # Key: action type, Value: reporter instance


class ReporterHub(AbstractReporter):
    _start_queue: asyncio.Queue[StartedActionMessage]
    _finish_queue: asyncio.Queue[FinishedActionMessage]
    _reporters: dict[str, list[AbstractReporter]]  # Key: action type, Value: reporters list
    _closed: bool
    _start_task: asyncio.Task
    _finish_task: asyncio.Task

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
            for reporter in target_reporters:
                try:
                    await reporter.report_started(message)
                except Exception as e:
                    log.error(f"reporter.report_started failed: {e}")

    async def _report_finished(self) -> None:
        while not self._closed:
            message = await self._finish_queue.get()
            target_reporters = self._target_reporters(message.action_type)
            for reporter in target_reporters:
                try:
                    await reporter.report_finished(message)
                except Exception as e:
                    log.error(f"reporter.report_finished failed: {e}")

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._start_task.cancel()
        self._finish_task.cancel()
