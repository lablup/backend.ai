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

    It keeps no status: a check records what it found and whoever reports it reads that
    off the check. A loop awaits its check, so a check that has not finished is not
    started again.
    """

    _checks: Sequence[AbstractProbeCheck[TID]]
    _tasks: list[asyncio.Task[None]]

    def __init__(self, args: ProbeCheckRunnerArgs[TID]) -> None:
        self._checks = args.checks
        self._tasks = []

    async def start(self) -> None:
        if self._tasks:
            log.warning("probe check runner already running")
            return
        for check in self._checks:
            task = asyncio.create_task(self._run_check(check))
            task.set_name(f"probe-check-{check.id()}")
            self._tasks.append(task)
        log.debug("probe check runner started", check_count=len(self._tasks))

    async def stop(self) -> None:
        for task in self._tasks:
            await cancel_and_wait(task)
        self._tasks.clear()
        log.debug("probe check runner stopped")

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
