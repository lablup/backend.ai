from __future__ import annotations

import asyncio
import logging
import time
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import override

from ai.backend.common.cron.base import PeriodicTask
from ai.backend.common.data.entity.storage_backend import StorageBackendID
from ai.backend.common.data.storage.types import (
    StorageStatusFailure,
    StorageStatusResult,
    StorageStatusSuccess,
)
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


class AbstractStorageBackendStatusCheck[TResult](metaclass=ABCMeta):
    """
    The status check of one storage appliance, and nothing else.

    It is not an abstraction of the appliance: it answers only whether the appliance is
    reachable from this service. Everything else about a backend lives elsewhere.
    """

    @property
    @abstractmethod
    def backend_id(self) -> StorageBackendID:
        """The operator-assigned id every service declaring this appliance writes down."""
        raise NotImplementedError

    @abstractmethod
    async def check_status(self) -> TResult:
        """
        Answers whether this appliance is reachable from this service.

        Separate from a volume's check because the two fail independently: an appliance
        can answer its management API while the storage has gone away on one service.
        """
        raise NotImplementedError


@dataclass
class BackendStatusProbeArgs[TResult]:
    check: AbstractStorageBackendStatusCheck[TResult]
    interval: float
    timeout: float
    initial_delay: float


class BackendStatusProbeTask[TResult](PeriodicTask):
    """
    Runs one appliance's status check on a loop of its own and holds the latest result.

    A check that overruns is left to finish rather than cancelled: an appliance without a
    management API is reached through the filesystem or a subprocess, and cancelling
    releases neither.
    """

    _check: AbstractStorageBackendStatusCheck[TResult]
    _interval: float
    _timeout: float
    _initial_delay: float
    _latest: StorageStatusResult | None
    _inflight: asyncio.Task[TResult] | None

    def __init__(self, args: BackendStatusProbeArgs[TResult]) -> None:
        self._check = args.check
        self._interval = args.interval
        self._timeout = args.timeout
        self._initial_delay = args.initial_delay
        self._latest = None
        self._inflight = None

    @property
    def latest(self) -> StorageStatusResult | None:
        """The most recent result, None until the first run finishes."""
        return self._latest

    @property
    @override
    def name(self) -> str:
        return f"backend_status_probe:{self._check.backend_id}"

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

    def _failure(self, detail: str) -> StorageStatusFailure:
        return StorageStatusFailure(checked_at=datetime.now(UTC), detail=detail)

    @override
    async def run(self) -> None:
        if self._inflight is not None and not self._inflight.done():
            self._latest = self._failure("the previous check is still outstanding")
            return
        start_at = time.perf_counter()
        self._inflight = asyncio.create_task(self._check.check_status(), name=self.name)
        try:
            await asyncio.wait_for(asyncio.shield(self._inflight), timeout=self._timeout)
            duration = timedelta(seconds=time.perf_counter() - start_at)
            self._latest = StorageStatusSuccess(checked_at=datetime.now(UTC), duration=duration)
        except TimeoutError:
            self._latest = self._failure(f"the check did not return within {self._timeout}s")
        except Exception as e:
            log.exception("backend status check failed", backend_id=str(self._check.backend_id))
            self._latest = self._failure(str(e))
