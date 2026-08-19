"""Leader-cron periodic task that sweeps expired DB records (BEP-1063).

Registered as a single :class:`PeriodicTask` on the manager's ``LeaderCron`` so
it runs only on the leader (leader election guarantees a single executor — no
``GlobalTimer`` or distributed lock). Each tick delegates the whole policy-driven
sweep to :meth:`RetentionRepository.sweep`; this task only owns the cadence.
"""

from __future__ import annotations

import logging
from typing import Final, override

from ai.backend.common.cron.base import PeriodicTask
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.repositories.retention.repository import RetentionRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RetentionSweepTask(PeriodicTask):
    """Periodically purges DB records past each enabled policy's age boundary."""

    _repository: Final[RetentionRepository]
    _interval: Final[float]
    _initial_delay: Final[float]

    def __init__(
        self,
        repository: RetentionRepository,
        interval: float,
        initial_delay: float = 0.0,
    ) -> None:
        self._repository = repository
        self._interval = interval
        self._initial_delay = initial_delay

    @override
    async def run(self) -> None:
        """Run one sweep. All orchestration lives in the repository."""
        await self._repository.sweep()

    @property
    @override
    def name(self) -> str:
        return "retention_sweep"

    @property
    @override
    def interval(self) -> float:
        return self._interval

    @property
    @override
    def initial_delay(self) -> float:
        return self._initial_delay
