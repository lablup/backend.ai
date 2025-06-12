import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AbstractTask(ABC):
    @classmethod
    @abstractmethod
    def name(cls) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def timeout(cls) -> Optional[float]:
        """
        Returns the timeout for the task
        """
        raise NotImplementedError

    @abstractmethod
    async def run(self) -> None:
        raise NotImplementedError


@dataclass
class TaskRunnerArgs:
    task: AbstractTask
    interval: float
    grace_period: float = 0


class TaskRunner:
    _task: AbstractTask
    _grace_period: float
    _interval: float

    def __init__(self, args: TaskRunnerArgs) -> None:
        self._task = args.task
        self._interval = args.interval
        self._grace_period = args.grace_period

        self._stopped = False
        self._runner_task: Optional[asyncio.Task] = None

    async def _spawned(self) -> None:
        await asyncio.sleep(self._grace_period)
        while not self._stopped:
            try:
                async with asyncio.timeout(self._task.timeout()):
                    await self._task.run()
            except asyncio.TimeoutError:
                log.warning(
                    "Task {} timed out after {} seconds",
                    self._task.name(),
                    self._task.timeout(),
                )
            except asyncio.CancelledError:
                log.debug("Task {} was cancelled", self._task.name())
                break
            finally:
                await asyncio.sleep(0)
            if self._stopped:
                break
            await asyncio.sleep(self._interval)

    async def run(self) -> None:
        self._runner_task = asyncio.create_task(self._spawned())
        await asyncio.sleep(0)

    async def stop(self) -> None:
        self._stopped = True
        if self._runner_task is not None:
            self._runner_task.cancel()
            await asyncio.sleep(0)
            if not self._runner_task.done():
                await self._runner_task
