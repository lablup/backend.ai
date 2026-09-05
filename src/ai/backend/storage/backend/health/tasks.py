from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

from ai.backend.common.cron.base import PeriodicTask
from ai.backend.common.data.storage.types import VolumeName
from ai.backend.logging import BraceStyleAdapter

from .abc import AbstractBackendProber
from .types import BackendHealthRecord, BackendProbeResult, BackendStatus

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass(frozen=True)
class BackendProbeTaskArgs:
    """What one appliance's probe loop needs to run and where it records."""

    volume_name: VolumeName
    prober: AbstractBackendProber
    record: BackendHealthRecord
    interval: float
    timeout: float


class BackendProbeTask(PeriodicTask):
    """
    Runs one volume's backend prober and records the result.

    Kept on a cadence of its own because an appliance can answer its management API
    while the mount has silently dropped.
    """

    _args: BackendProbeTaskArgs
    _initial_delay: float

    def __init__(self, args: BackendProbeTaskArgs) -> None:
        self._args = args
        self._initial_delay = random.uniform(0.0, args.interval)

    @property
    @override
    def name(self) -> str:
        return "backend_probe"

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
        timeout = self._args.timeout
        try:
            result = await asyncio.wait_for(self._args.prober.probe(), timeout=timeout)
        except TimeoutError:
            log.warning("Backend probe for {} timed out after {}s", self._args.volume_name, timeout)
            result = BackendProbeResult(
                status=BackendStatus.OFFLINE,
                checked_at=datetime.now(UTC),
                status_info=f"the probe timed out after {timeout}s",
            )
        except Exception as e:
            log.exception("Backend probe for {} failed", self._args.volume_name)
            result = BackendProbeResult(
                status=BackendStatus.OFFLINE, checked_at=datetime.now(UTC), status_info=str(e)
            )
        self._args.record.latest = result
