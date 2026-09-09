from __future__ import annotations

import asyncio
import logging
import random
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

from ai.backend.common.cron.base import PeriodicTask
from ai.backend.common.data.storage.types import VolumeName
from ai.backend.logging import BraceStyleAdapter

from .abc import AbstractMountProber
from .types import MountHealthRecord, MountProbeResult, MountStatus

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass(frozen=True)
class MountProbeTaskArgs:
    """What one volume's mount probe loop needs to run and where it records."""

    volume_name: VolumeName
    prober: AbstractMountProber
    record: MountHealthRecord
    interval: float
    timeout: float


class MountProbeTask(PeriodicTask):
    """
    Runs one volume's mount prober in a thread of its own and records the result.

    The pool is isolated per volume so that a probe left blocked in an uninterruptible
    syscall on a dead mount cannot starve the file operations sharing the default one.
    """

    _args: MountProbeTaskArgs
    _initial_delay: float
    _executor: ThreadPoolExecutor
    _inflight: Future[MountProbeResult] | None

    def __init__(self, args: MountProbeTaskArgs) -> None:
        self._args = args
        self._initial_delay = random.uniform(0.0, args.interval)
        self._executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix=f"mount-probe-{args.volume_name}",
        )
        self._inflight = None

    @property
    @override
    def name(self) -> str:
        return "mount_probe"

    @property
    @override
    def interval(self) -> float:
        return self._args.interval

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
        if self._inflight is not None and not self._inflight.done():
            # Resubmitting would only queue behind the thread that is still blocked.
            self._args.record.latest = MountProbeResult(
                status=MountStatus.HUNG,
                checked_at=datetime.now(UTC),
                detail="the previous probe is still outstanding",
            )
            return

        future = self._executor.submit(self._args.prober.probe)
        self._inflight = future
        timeout = self._args.timeout
        try:
            result = await asyncio.wait_for(asyncio.wrap_future(future), timeout=timeout)
        except TimeoutError:
            log.warning("Mount probe for {} timed out after {}s", self._args.volume_name, timeout)
            result = MountProbeResult(
                status=MountStatus.HUNG,
                checked_at=datetime.now(UTC),
                detail=f"the probe timed out after {timeout}s",
            )
        except Exception as e:
            log.exception("Mount probe for {} failed", self._args.volume_name)
            result = MountProbeResult(
                status=MountStatus.ERROR, checked_at=datetime.now(UTC), detail=str(e)
            )
        self._args.record.latest = result

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
