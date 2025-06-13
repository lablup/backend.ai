import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Final, Optional

from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


DEFAULT_INTERVAL: Final[float] = 10.0
DEFAULT_GRACE_PERIOD: Final[float] = 0.0


class AbstractTask(ABC):
    @classmethod
    @abstractmethod
    def name(cls) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def timeout(cls) -> Optional[float]:
        """
        Returns the timeout for the task in seconds.
        """
        raise NotImplementedError

    @abstractmethod
    async def run(self) -> None:
        raise NotImplementedError


@dataclass
class TaskRunnerArgs:
    task: AbstractTask
    interval: float = DEFAULT_INTERVAL
    grace_period: float = DEFAULT_GRACE_PERIOD


class TaskRunner:
    """
    TaskRunner is a utility class that runs a task at a specified interval.

    Parameters
    ----------
    task : AbstractTask
        An instance of a class that implements AbstractTask.
    interval : float, default=10.0
        The interval in seconds between task runs.
    grace_period : float, default=0.0
        The initial delay before the first run.

    Examples
    --------
    task = MyTask()  # An instance of a class that implements AbstractTask
    runner_args = TaskRunnerArgs(task=task, interval=5.0, grace_period=2.0, timeout=10.0)
    task_runner = TaskRunner(runner_args)
    await task_runner.run()

    # To stop the runner
    await task_runner.stop()
    """

    _task: AbstractTask
    _interval: float
    _grace_period: float
    _timeout: Optional[float]

    _stopped: bool
    _runner_task: Optional[asyncio.Task]

    def __init__(self, args: TaskRunnerArgs) -> None:
        self._task = args.task
        self._interval = args.interval
        self._grace_period = args.grace_period
        self._timeout = args.task.timeout()

        self._stopped = False
        self._runner_task: Optional[asyncio.Task] = None

    async def _spawned(self) -> None:
        await asyncio.sleep(self._grace_period)
        while not self._stopped:
            try:
                async with asyncio.timeout(self._timeout):
                    await self._task.run()
            except asyncio.TimeoutError:
                log.warning(
                    "Task {} timed out after {} seconds",
                    self._task.name(),
                    self._timeout,
                )
            except asyncio.CancelledError:
                log.debug("Task {} was canceled", self._task.name())
                break
            except Exception as e:
                log.error(
                    "Task {} raised an exception: {}",
                    self._task.name(),
                    e,
                )
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
        if self._runner_task.done():
            return
        try:
            await self._runner_task
        except BaseException as e:
            log.debug("Task raises error when stopping: {}", e)
