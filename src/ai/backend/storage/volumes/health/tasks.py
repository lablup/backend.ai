from __future__ import annotations

import asyncio
import logging
import random
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, datetime
from typing import override

from ai.backend.common.cron.base import PeriodicTask
from ai.backend.common.data.storage.types import VolumeName
from ai.backend.logging import BraceStyleAdapter

from .abc import AbstractBackendProber, AbstractMountProber
from .types import (
    BackendProbeResult,
    BackendStatus,
    MountProbeResult,
    MountStatus,
    VolumeHealthRecord,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class MountProbeTask(PeriodicTask):
    """
    Runs one volume's mount prober in a thread of its own and records the result.

    A probe that timed out is never resubmitted while its thread is still blocked in the
    system call, because cancelling the await does not release that thread.
    """

    _volume_name: VolumeName
    _prober: AbstractMountProber
    _record: VolumeHealthRecord
    _interval: float
    _initial_delay: float
    _timeout: float
    _executor: ThreadPoolExecutor
    _inflight: Future[MountProbeResult] | None

    def __init__(
        self,
        volume_name: VolumeName,
        prober: AbstractMountProber,
        record: VolumeHealthRecord,
        interval: float,
        timeout: float,
    ) -> None:
        self._volume_name = volume_name
        self._prober = prober
        self._record = record
        self._interval = interval
        # Spreads the volumes over the interval so that they do not all probe at once.
        self._initial_delay = random.uniform(0.0, interval)
        self._timeout = timeout
        # One worker per volume: a thread stuck in a dead mount can then starve nothing else.
        self._executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix=f"mount-probe-{volume_name}",
        )
        self._inflight = None

    @property
    @override
    def name(self) -> str:
        return "mount_probe"

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
        # Bounded below instead; cutting the await here would leave the executor thread
        # untracked and let repeated attempts pile threads up.
        return None

    @override
    async def run(self) -> None:
        if self._inflight is not None and not self._inflight.done():
            self._record.mount = MountProbeResult(
                status=MountStatus.HUNG,
                checked_at=datetime.now(UTC),
                detail="the previous probe is still outstanding",
            )
            return

        future = self._executor.submit(self._prober.probe)
        self._inflight = future
        try:
            result = await asyncio.wait_for(asyncio.wrap_future(future), timeout=self._timeout)
        except TimeoutError:
            log.warning("Mount probe for {} timed out after {}s", self._volume_name, self._timeout)
            result = MountProbeResult(
                status=MountStatus.HUNG,
                checked_at=datetime.now(UTC),
                detail=f"the probe timed out after {self._timeout}s",
            )
        except Exception as e:
            log.exception("Mount probe for {} failed", self._volume_name)
            result = MountProbeResult(
                status=MountStatus.ERROR, checked_at=datetime.now(UTC), detail=str(e)
            )
        self._record.mount = result

    def shutdown(self) -> None:
        # Never waits: a thread blocked in a dead mount's system call would never return.
        self._executor.shutdown(wait=False, cancel_futures=True)


class BackendProbeTask(PeriodicTask):
    """
    Runs one volume's backend prober and records the result.

    Kept on a cadence of its own because an appliance can answer its management API
    while the mount has silently dropped.
    """

    _volume_name: VolumeName
    _prober: AbstractBackendProber
    _record: VolumeHealthRecord
    _interval: float
    _initial_delay: float
    _timeout: float

    def __init__(
        self,
        volume_name: VolumeName,
        prober: AbstractBackendProber,
        record: VolumeHealthRecord,
        interval: float,
        timeout: float,
    ) -> None:
        self._volume_name = volume_name
        self._prober = prober
        self._record = record
        self._interval = interval
        self._initial_delay = random.uniform(0.0, interval)
        self._timeout = timeout

    @property
    @override
    def name(self) -> str:
        return "backend_probe"

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
        # Handled inside run(), so that a timeout is recorded as an offline appliance
        # instead of only being logged by the cron.
        return None

    @override
    async def run(self) -> None:
        try:
            result = await asyncio.wait_for(self._prober.probe(), timeout=self._timeout)
        except TimeoutError:
            log.warning(
                "Backend probe for {} timed out after {}s", self._volume_name, self._timeout
            )
            result = BackendProbeResult(
                status=BackendStatus.OFFLINE,
                checked_at=datetime.now(UTC),
                status_info=f"the probe timed out after {self._timeout}s",
            )
        except Exception as e:
            log.exception("Backend probe for {} failed", self._volume_name)
            result = BackendProbeResult(
                status=BackendStatus.OFFLINE, checked_at=datetime.now(UTC), status_info=str(e)
            )
        self._record.backend = result
