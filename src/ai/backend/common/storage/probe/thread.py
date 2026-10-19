from __future__ import annotations

from collections.abc import Hashable, Sequence
from concurrent.futures import Executor, Future
from dataclasses import dataclass
from functools import partial
from typing import override

from ai.backend.common.cron.base import PeriodicTask
from ai.backend.common.storage.probe.check import AbstractProbeCheck


@dataclass
class ThreadPoolProbeArgs[TID: Hashable]:
    name: str
    checks: Sequence[AbstractProbeCheck[TID]]
    interval: float
    initial_delay: float
    executor: Executor


class ThreadPoolProbeTask[TID: Hashable](PeriodicTask):
    """
    Runs every status check it is given, each in a thread of its own.

    It keeps no status: a check records what it found and whoever reports it reads that
    off the check. A check still running is not submitted again, because the thread it
    blocks in is not released by anything this task can do. ``_forget`` runs on whichever
    thread finished the check, so it drops the entry only while it is still the one it
    submitted.
    """

    _name: str
    _checks: Sequence[AbstractProbeCheck[TID]]
    _interval: float
    _initial_delay: float
    _executor: Executor
    _inflight: dict[TID, Future[None]]

    def __init__(self, args: ThreadPoolProbeArgs[TID]) -> None:
        self._name = args.name
        self._checks = args.checks
        self._interval = args.interval
        self._initial_delay = args.initial_delay
        self._executor = args.executor
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
            future = self._executor.submit(check.check_status)
            self._inflight[check_id] = future
            future.add_done_callback(partial(self._forget, check_id))

    def _forget(self, check_id: TID, future: Future[None]) -> None:
        self._inflight.pop(check_id, None)
