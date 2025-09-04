"""Leader cron implementation that runs tasks periodically only on the leader."""

from __future__ import annotations

import asyncio
import logging
from typing import Final

from ai.backend.common.leader.base import LeadershipChecker, LeaderTask
from ai.backend.common.leader.tasks.base import PeriodicTask
from ai.backend.common.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class LeaderCron(LeaderTask):
    """
    Leader cron that manages and runs multiple PeriodicTask instances periodically.

    This implements the LeaderTask interface for registration with ValkeyLeaderElection
    and manages the periodic execution of multiple PeriodicTask instances.
    """

    _tasks: Final[list[PeriodicTask]]
    _task_runners: list[asyncio.Task[None]]
    _leadership_checker: LeadershipChecker
    _stopped: bool

    def __init__(
        self,
        tasks: list[PeriodicTask],
    ) -> None:
        """
        Initialize the leader cron with tasks.

        Args:
            tasks: List of periodic tasks to run when leader
        """
        self._tasks = tasks
        self._task_runners = []
        self._stopped = False

        log.info(f"Initialized LeaderCron with {len(tasks)} tasks")

    async def _run_task(self, task: PeriodicTask) -> None:
        """
        Run a single task periodically.

        This task only executes when the instance is the leader.
        """
        try:
            await asyncio.sleep(task.initial_delay)
            while not self._stopped:
                if self._leadership_checker.is_leader:
                    try:
                        await task.run()
                    except Exception:
                        log.exception(f"Error running task {task.name}")
                await asyncio.sleep(task.interval)
        except asyncio.CancelledError:
            log.debug(f"Task {task.name} cancelled")
            raise
        except Exception:
            log.exception(f"Unexpected error in task {task.name}")
            raise

    async def start(self, leadership_checker: LeadershipChecker) -> None:
        """
        Start the leader cron.

        Args:
            leadership_checker: Object that provides leadership status
        """
        log.info("Starting leader cron")

        self._stopped = False
        self._leadership_checker = leadership_checker

        # Start all tasks
        for task in self._tasks:
            runner = asyncio.create_task(self._run_task(task))
            runner.set_name(f"leader-cron-task-{task.name}")
            self._task_runners.append(runner)

        log.info(f"Leader cron started with {len(self._tasks)} tasks")

    async def stop(self) -> None:
        """
        Stop the leader cron.

        This stops all tasks and cleans up resources.
        """
        log.info("Stopping leader cron")
        self._stopped = True
        for runner in self._task_runners:
            if not runner.done():
                runner.cancel()
                try:
                    await runner
                except asyncio.CancelledError:
                    pass
        self._task_runners.clear()
        log.info("Leader cron stopped")
