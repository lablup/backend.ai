"""Local cron implementation that runs tasks periodically on every node."""

from __future__ import annotations

import asyncio
import logging
from typing import Final

from ai.backend.common.cron.base import Cron, PeriodicTask
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class LocalCron(Cron):
    """
    Local cron that runs its tasks unconditionally on the current node.

    Each task runs in its own loop with per-iteration exception isolation: an exception
    (or a per-run timeout) is logged via the structured logger and the loop continues at
    the next interval, so a transient failure (e.g. a Redis outage) neither terminates the
    task nor leaks a raw traceback.
    """

    _tasks: Final[list[PeriodicTask]]
    _task_runners: list[asyncio.Task[None]]
    _stopped: bool

    def __init__(
        self,
        tasks: list[PeriodicTask],
    ) -> None:
        self._tasks = tasks
        self._task_runners = []
        self._stopped = False

    async def _run_task(self, task: PeriodicTask) -> None:
        """Run a single task periodically until the cron is stopped or cancelled."""
        try:
            await asyncio.sleep(task.initial_delay)
            while not self._stopped:
                try:
                    run_timeout = task.run_timeout
                    if run_timeout is not None:
                        await asyncio.wait_for(task.run(), timeout=run_timeout)
                    else:
                        await task.run()
                except TimeoutError:
                    log.warning("Task {} timed out after {}s", task.name, task.run_timeout)
                except Exception:
                    log.exception("Error running task {}", task.name)
                await asyncio.sleep(task.interval)
        except asyncio.CancelledError:
            log.debug("Task {} cancelled", task.name)
            raise

    async def start(self) -> None:
        """Start the local cron."""
        self._stopped = False
        for task in self._tasks:
            runner = asyncio.create_task(self._run_task(task))
            runner.set_name(f"local-cron-task-{task.name}")
            self._task_runners.append(runner)

    async def stop(self) -> None:
        """Stop the local cron and cancel all of its task runners."""
        self._stopped = True
        for runner in self._task_runners:
            if not runner.done():
                runner.cancel()
                try:
                    await runner
                except asyncio.CancelledError:
                    pass
        self._task_runners.clear()
