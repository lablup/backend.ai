"""Generic, entity-agnostic lifecycle coordinator."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from contextlib import AsyncExitStack

from ai.backend.common.leader.tasks import EventTaskSpec
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.sokovan.lifecycle.base import (
    LifecycleNeededFlags,
    LifecycleStageRunner,
    LifecycleTaskSpec,
)
from ai.backend.manager.types import DistributedLockFactory

log = BraceStyleAdapter(logging.getLogger(__name__))


class LifecycleCoordinator:
    """Dispatches lifecycle stages: acquire lock, run the stage, on needed-flag or tick."""

    _stages: Mapping[str, LifecycleStageRunner]
    _flags: LifecycleNeededFlags
    _lock_factory: DistributedLockFactory
    _config_provider: ManagerConfigProvider
    _task_specs: list[LifecycleTaskSpec]

    def __init__(
        self,
        stages: Mapping[str, LifecycleStageRunner],
        flags: LifecycleNeededFlags,
        lock_factory: DistributedLockFactory,
        config_provider: ManagerConfigProvider,
        task_specs: Sequence[LifecycleTaskSpec],
    ) -> None:
        self._stages = stages
        self._flags = flags
        self._lock_factory = lock_factory
        self._config_provider = config_provider
        self._task_specs = list(task_specs)

    async def process(self, lifecycle_type: str) -> None:
        stage = self._stages.get(lifecycle_type)
        if stage is None:
            log.warning("No stage for lifecycle type: {}", lifecycle_type)
            return

        async with AsyncExitStack() as stack:
            if stage.lock_id is not None:
                lock_lifetime = self._config_provider.config.manager.session_schedule_lock_lifetime
                await stack.enter_async_context(self._lock_factory(stage.lock_id, lock_lifetime))
            try:
                await stage.run()
            except Exception as e:
                log.error("Error while processing lifecycle {}: {}", lifecycle_type, e)

    async def process_if_needed(self, lifecycle_type: str) -> None:
        if not await self._flags.load_and_delete(lifecycle_type):
            return
        await self.process(lifecycle_type)

    def create_task_specs(self) -> list[EventTaskSpec]:
        specs: list[EventTaskSpec] = []
        for spec in self._task_specs:
            if spec.short_interval is not None:
                specs.append(
                    EventTaskSpec(
                        name=spec.short_task_name,
                        event_factory=spec.create_if_needed_event,
                        interval=spec.short_interval,
                        initial_delay=0.0,
                    )
                )
            specs.append(
                EventTaskSpec(
                    name=spec.long_task_name,
                    event_factory=spec.create_process_event,
                    interval=spec.long_interval,
                    initial_delay=spec.initial_delay,
                )
            )
        return specs
