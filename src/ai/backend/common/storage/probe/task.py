from __future__ import annotations

import asyncio
from collections.abc import Hashable, Sequence
from dataclasses import dataclass
from functools import partial
from typing import override

from ai.backend.common.cron.base import PeriodicTask
from ai.backend.common.storage.probe.check import AbstractProbeCheck


@dataclass
class ProbeArgs[TID: Hashable]:
    name: str
    checks: Sequence[AbstractProbeCheck[TID]]
    interval: float
    initial_delay: float


class ProbeTask[TID: Hashable](PeriodicTask):
    """
    Runs every status check it is given, each as an asyncio task of its own.

    It keeps no status: a check records what it found and whoever reports it reads that
    off the check. A check still running is not started again.
    """

    _name: str
    _checks: Sequence[AbstractProbeCheck[TID]]
    _interval: float
    _initial_delay: float
    _inflight: dict[TID, asyncio.Task[None]]

    def __init__(self, args: ProbeArgs[TID]) -> None:
        self._name = args.name
        self._checks = args.checks
        self._interval = args.interval
        self._initial_delay = args.initial_delay
        self._inflight = {}

    @property
    @override
    def name(self) -> str:
        return self._name

    @property
    @override
    def interval(self) -> float:
        return self._interval

    @property
    @override
    def initial_delay(self) -> float:
        return self._initial_delay

    @property
    @override
    def run_timeout(self) -> float | None:
        return None

    @override
    async def run(self) -> None:
        for check in self._checks:
            check_id = check.id()
            if check_id in self._inflight:
                continue
            task = asyncio.create_task(check.check_status())
            self._inflight[check_id] = task
            task.add_done_callback(partial(self._forget, check_id))

    def _forget(self, check_id: TID, task: asyncio.Task[None]) -> None:
        self._inflight.pop(check_id, None)
