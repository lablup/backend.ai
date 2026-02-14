from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.plugin.network import NetworkPluginContext

from .base import PluginDependency, PluginsInput

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class NetworkPluginDependency(PluginDependency[NetworkPluginContext]):
    """Provides NetworkPluginContext lifecycle management."""

    @property
    def stage_name(self) -> str:
        return "network-plugin"

    @asynccontextmanager
    async def provide(self, setup_input: PluginsInput) -> AsyncIterator[NetworkPluginContext]:
        """Initialize and provide a NetworkPluginContext.

        Args:
            setup_input: Plugins input containing etcd and config

        Yields:
            Initialized NetworkPluginContext
        """
        ctx = NetworkPluginContext(setup_input.etcd, setup_input.local_config)
        await ctx.init(
            context=setup_input.init_context,
            allowlist=setup_input.allowed_plugins,
            blocklist=setup_input.disabled_plugins,
        )
        log.info("NetworkPluginContext initialized with plugins: {}", list(ctx.plugins.keys()))
        try:
            yield ctx
        finally:
            await ctx.cleanup()
