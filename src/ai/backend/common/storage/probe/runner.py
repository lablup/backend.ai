from __future__ import annotations

import asyncio
import logging
from collections.abc import Hashable, Sequence
from dataclasses import dataclass

from aiotools import cancel_and_wait

from ai.backend.common.storage.probe.check import AbstractProbeCheck
from ai.backend.logging.structured import StructuredLogger, with_log_context

log = StructuredLogger(logging.getLogger(__spec__.name))


@dataclass
class ProbeCheckRunnerArgs[TID: Hashable]:
    checks: Sequence[AbstractProbeCheck[TID]]


class ProbeCheckRunner[TID: Hashable]:
    """
    Runs every check it is given on the check's own interval, each in a loop of its own.

    An update stops and closes the checks no longer given and starts the ones given anew.
    A loop awaits its check, so a check that has not finished is not started again.
    """

    _checks: dict[TID, AbstractProbeCheck[TID]]
    _tasks: dict[TID, asyncio.Task[None]]
    _running: bool

    def __init__(self, args: ProbeCheckRunnerArgs[TID]) -> None:
        self._checks = {check.id(): check for check in args.checks}
        self._tasks = {}
        self._running = False

    async def start(self) -> None:
        if self._running:
            log.warning("probe check runner already running")
            return
        self._running = True
        for check in self._checks.values():
            self._start_check(check)
        log.debug("probe check runner started", check_count=len(self._tasks))

    async def stop(self) -> None:
        """Stops every loop and closes every check."""
        self._running = False
        for task in self._tasks.values():
            await cancel_and_wait(task)
        self._tasks.clear()
        for check in self._checks.values():
            check.close()
        log.debug("probe check runner stopped")

    def update(self, checks: Sequence[AbstractProbeCheck[TID]]) -> None:
        """Replaces the checks: a check no longer given is stopped and closed, and a given
        check without a loop is started."""
        updated_checks = {check.id(): check for check in checks}
        for check_id, check in self._checks.items():
            if updated_checks.get(check_id) is not check:
                task = self._tasks.pop(check_id, None)
                if task is not None:
                    task.cancel()
                check.close()
        self._checks = updated_checks
        if not self._running:
            return
        for check in updated_checks.values():
            if check.id() not in self._tasks:
                self._start_check(check)

    def _start_check(self, check: AbstractProbeCheck[TID]) -> None:
        task = asyncio.create_task(self._run_check(check))
        task.set_name(f"probe-check-{check.id()}")
        self._tasks[check.id()] = task

    async def _run_check(self, check: AbstractProbeCheck[TID]) -> None:
        with with_log_context(check_id=str(check.id())):
            try:
                await asyncio.sleep(check.initial_delay())
                while True:
                    try:
                        await check.check_status()
                    except Exception:
                        log.exception("probe check raised")
                    await asyncio.sleep(check.interval())
            except asyncio.CancelledError:
                log.debug("probe check loop cancelled")
                raise
