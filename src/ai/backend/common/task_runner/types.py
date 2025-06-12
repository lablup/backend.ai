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

    continue_on_error: bool = False


class TaskRunner:
    _task: AbstractTask
    _interval: float
    _grace_period: float
    _continue_on_error: bool

    _stopped: bool
    _runner_task: Optional[asyncio.Task]

    def __init__(self, args: TaskRunnerArgs) -> None:
        self._task = args.task
        self._interval = args.interval
        self._grace_period = args.grace_period
        self._continue_on_error = args.continue_on_error

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
            except Exception as e:
                log.error(
                    "Task {} raised an exception: {}",
                    self._task.name(),
                    e,
                )
                if not self._continue_on_error:
                    raise
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
        if self._runner_task is None:
            return
        is_canceled = self._runner_task.cancel()
        if not is_canceled:
            # Task has already finished
            return
        await asyncio.sleep(0)
        try:
            await self._runner_task
        except BaseException as e:
            log.debug("Task raises error when stopping: {}", e)
