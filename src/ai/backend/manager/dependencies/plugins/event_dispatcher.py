from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.common.plugin.event import EventDispatcherPluginContext
from ai.backend.logging import BraceStyleAdapter

from .base import PluginDependency, PluginsInput

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class EventDispatcherPluginDependency(PluginDependency[EventDispatcherPluginContext]):
    """Provides EventDispatcherPluginContext lifecycle management."""

    @property
    def stage_name(self) -> str:
        return "event-dispatcher-plugin"

    @asynccontextmanager
    async def provide(
        self, setup_input: PluginsInput
    ) -> AsyncIterator[EventDispatcherPluginContext]:
        """Initialize and provide an EventDispatcherPluginContext.

        Args:
            setup_input: Plugins input containing etcd and config

        Yields:
            Initialized EventDispatcherPluginContext
        """
        ctx = EventDispatcherPluginContext(setup_input.etcd, setup_input.local_config)
        await ctx.init(
            context=setup_input.init_context,
            allowlist=setup_input.allowed_plugins,
            blocklist=setup_input.disabled_plugins,
        )
        log.info(
            "EventDispatcherPluginContext initialized with plugins: {}",
            list(ctx.plugins.keys()),
        )
        try:
            yield ctx
        finally:
            await ctx.cleanup()
