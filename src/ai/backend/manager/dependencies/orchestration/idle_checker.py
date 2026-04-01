from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.idle import IdleCheckerHost, init_idle_checkers
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.types import DistributedLockFactory


@dataclass
class IdleCheckerInput:
    """Input required for idle checker host setup."""

    db: ExtendedAsyncSAEngine
    config_provider: ManagerConfigProvider
    event_producer: EventProducer
    lock_factory: DistributedLockFactory


class IdleCheckerHostDependency(
    NonMonitorableDependencyProvider[IdleCheckerInput, IdleCheckerHost]
):
    """Provides IdleCheckerHost lifecycle management.

    Wraps the idle checker initialization, startup, and shutdown
    sequence from the original ``idle_checker_ctx`` in server.py.
    """

    @property
    def stage_name(self) -> str:
        return "idle-checker-host"

    @asynccontextmanager
    async def provide(self, setup_input: IdleCheckerInput) -> AsyncIterator[IdleCheckerHost]:
        """Initialize and provide idle checker host.

        Args:
            setup_input: Input containing database, config, event producer, and lock factory

        Yields:
            Initialized and started IdleCheckerHost
        """
        checker_host = await init_idle_checkers(
            setup_input.db,
            setup_input.config_provider,
            setup_input.event_producer,
            setup_input.lock_factory,
        )
        await checker_host.start()
        try:
            yield checker_host
        finally:
            await checker_host.shutdown()
