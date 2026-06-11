"""Generic, entity-agnostic lifecycle coordinator."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Mapping
from contextlib import AsyncExitStack

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.sokovan.reconciler.base import ReconcilerStageRunner
from ai.backend.manager.types import DistributedLockFactory

log = BraceStyleAdapter(logging.getLogger(__name__))


class ReconcilerFlag(ABC):
    """Marker for lifecycle-needed flags that drive scheduling decisions."""

    @abstractmethod
    async def check_mark_needed(self, reconcile_type: str) -> bool:
        """Check if the lifecycle type needs to be processed, and mark it as needed if so."""
        raise NotImplementedError


class ReconcilerCoordinator:
    """Coordinates lifecycle stages for scheduling decisions."""

    _stages: Mapping[str, ReconcilerStageRunner]
    _lock_factory: DistributedLockFactory
    _config_provider: ManagerConfigProvider
    _flags: ReconcilerFlag

    def __init__(
        self,
        stages: Mapping[str, ReconcilerStageRunner],
        lock_factory: DistributedLockFactory,
        config_provider: ManagerConfigProvider,
        flags: ReconcilerFlag,
    ) -> None:
        self._stages = stages
        self._flags = flags
        self._lock_factory = lock_factory
        self._config_provider = config_provider

    async def process(self, reconcile_type: str) -> None:
        stage = self._stages.get(reconcile_type)
        if stage is None:
            log.warning("No stage for lifecycle type: {}", reconcile_type)
            return

        async with AsyncExitStack() as stack:
            if stage.lock_id is not None:
                lock_lifetime = self._config_provider.config.manager.session_schedule_lock_lifetime
                await stack.enter_async_context(self._lock_factory(stage.lock_id, lock_lifetime))
            try:
                await stage.run()
            except Exception as e:
                log.error("Error while processing lifecycle {}: {}", reconcile_type, e)

    async def process_if_needed(self, reconcile_type: str) -> None:
        if not await self._flags.check_mark_needed(reconcile_type):
            log.debug("Lifecycle {} not needed, skipping", reconcile_type)
            return
        await self.process(reconcile_type)
