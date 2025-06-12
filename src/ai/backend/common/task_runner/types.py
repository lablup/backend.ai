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
    timeout: Optional[float] = None

    continue_on_error: bool = False


class TaskRunner:
    """
    TaskRunner is a utility class that runs a task at a specified interval.

    Parameters
    ----------
    task : AbstractTask
        An instance of a class that implements AbstractTask.
    interval : float
        The interval in seconds between task runs.
    grace_period : float
        The initial delay before the first run.
    timeout : float, optional
        timeout for the task execution. task.timeout() will override this value if it is set.
    continue_on_error : bool
        If True, the runner will continue running
        even if the task raises an error except asyncio.CancelledError and asyncio.TimeoutError.

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
    _continue_on_error: bool

    _stopped: bool
    _runner_task: Optional[asyncio.Task]

    def __init__(self, args: TaskRunnerArgs) -> None:
        self._task = args.task
        self._interval = args.interval
        self._grace_period = args.grace_period
        self._timeout = args.task.timeout() if args.task.timeout() is not None else args.timeout
        self._continue_on_error = args.continue_on_error

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
        if self._runner_task.done():
            return
        try:
            await self._runner_task
        except BaseException as e:
            log.debug("Task raises error when stopping: {}", e)
