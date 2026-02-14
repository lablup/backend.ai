from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.plugin.monitor import ManagerErrorPluginContext, ManagerStatsPluginContext

from .base import PluginDependency, PluginsInput

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ErrorMonitorDependency(PluginDependency[ManagerErrorPluginContext | None]):
    """Provides ManagerErrorPluginContext lifecycle management.

    Tolerates initialization failures — yields None if init fails.
    Passes ``{"_root.context": init_context}`` as the context parameter,
    matching the current server.py behavior.
    """

    @property
    def stage_name(self) -> str:
        return "error-monitor-plugin"

    @asynccontextmanager
    async def provide(
        self, setup_input: PluginsInput
    ) -> AsyncIterator[ManagerErrorPluginContext | None]:
        """Initialize and provide a ManagerErrorPluginContext.

        Args:
            setup_input: Plugins input containing etcd and config

        Yields:
            Initialized ManagerErrorPluginContext, or None if init fails
        """
        ctx = ManagerErrorPluginContext(setup_input.etcd, setup_input.local_config)
        try:
            await ctx.init(
                context={"_root.context": setup_input.init_context},
                allowlist=setup_input.allowed_plugins,
            )
        except Exception:
            log.error("Failed to initialize error monitor plugin")
            yield None
            return
        log.info(
            "ManagerErrorPluginContext initialized with plugins: {}",
            list(ctx.plugins.keys()),
        )
        try:
            yield ctx
        finally:
            await ctx.cleanup()


class StatsMonitorDependency(PluginDependency[ManagerStatsPluginContext | None]):
    """Provides ManagerStatsPluginContext lifecycle management.

    Tolerates initialization failures — yields None if init fails.
    Does not pass any context to init, matching current server.py behavior.
    """

    @property
    def stage_name(self) -> str:
        return "stats-monitor-plugin"

    @asynccontextmanager
    async def provide(
        self, setup_input: PluginsInput
    ) -> AsyncIterator[ManagerStatsPluginContext | None]:
        """Initialize and provide a ManagerStatsPluginContext.

        Args:
            setup_input: Plugins input containing etcd and config

        Yields:
            Initialized ManagerStatsPluginContext, or None if init fails
        """
        ctx = ManagerStatsPluginContext(setup_input.etcd, setup_input.local_config)
        try:
            await ctx.init(
                allowlist=setup_input.allowed_plugins,
            )
        except Exception:
            log.error("Failed to initialize stats monitor plugin")
            yield None
            return
        log.info(
            "ManagerStatsPluginContext initialized with plugins: {}",
            list(ctx.plugins.keys()),
        )
        try:
            yield ctx
        finally:
            await ctx.cleanup()
