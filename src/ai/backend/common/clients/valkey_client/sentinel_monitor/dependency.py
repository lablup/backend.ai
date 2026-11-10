from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import override

from ai.backend.common.clients.valkey_client.sentinel_monitor.monitor_set import (
    SentinelMonitorSet,
)
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.types import ValkeyTarget


class SentinelMonitorDependency(
    NonMonitorableDependencyProvider[Sequence[ValkeyTarget], SentinelMonitorSet]
):
    """Sentinel monitors for the Sentinel targets, entered before the Valkey clients that use them."""

    @property
    @override
    def stage_name(self) -> str:
        return "sentinel-monitor"

    @asynccontextmanager
    @override
    async def provide(
        self, setup_input: Sequence[ValkeyTarget]
    ) -> AsyncIterator[SentinelMonitorSet]:
        monitors = SentinelMonitorSet(setup_input)
        await monitors.start()
        try:
            yield monitors
        finally:
            await monitors.close()
