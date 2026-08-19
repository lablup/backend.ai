"""Periodic task that pings the coordinator to keep the worker registered."""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Final, override

from tenacity import AsyncRetrying, TryAgain, retry_if_exception_type, wait_exponential

from ai.backend.appproxy.common.errors import CoordinatorConnectionError
from ai.backend.appproxy.worker.coordinator_client import ping_worker
from ai.backend.common.cron import PeriodicTask
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.appproxy.worker.types import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class WorkerHeartbeatTask(PeriodicTask):
    """Periodically ping the coordinator to keep this worker registered."""

    _root_ctx: Final[RootContext]

    def __init__(self, root_ctx: RootContext) -> None:
        self._root_ctx = root_ctx

    @property
    @override
    def name(self) -> str:
        return "worker_heartbeat"

    @property
    @override
    def interval(self) -> float:
        return self._root_ctx.local_config.proxy_worker.heartbeat_period

    @property
    @override
    def initial_delay(self) -> float:
        return 0.0

    @override
    async def run(self) -> None:
        try:
            async for attempt in AsyncRetrying(
                wait=wait_exponential(multiplier=1, min=4, max=10),
                retry=retry_if_exception_type(TryAgain),
            ):
                with attempt:
                    try:
                        await ping_worker(self._root_ctx, str(uuid.uuid4()))
                    except CoordinatorConnectionError:
                        log.warning(
                            "Failed to ping coordinator {}, retrying...",
                            self._root_ctx.local_config.proxy_worker.coordinator_endpoint,
                        )
        except Exception as e:
            log.warning("Failed to ping coordinator: {}", str(e))
