from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.common.plugin.hook import ALL_COMPLETED, PASSED, HookPluginContext
from ai.backend.logging import BraceStyleAdapter

from .base import PluginDependency, PluginsInput

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class HookPluginDependency(PluginDependency[HookPluginContext]):
    """Provides HookPluginContext lifecycle management.

    After initialization, dispatches ACTIVATE_MANAGER and raises
    RuntimeError if the hook result is not PASSED.
    """

    @property
    def stage_name(self) -> str:
        return "hook-plugin"

    @asynccontextmanager
    async def provide(self, setup_input: PluginsInput) -> AsyncIterator[HookPluginContext]:
        """Initialize and provide a HookPluginContext.

        Args:
            setup_input: Plugins input containing etcd and config

        Yields:
            Initialized HookPluginContext

        Raises:
            RuntimeError: If ACTIVATE_MANAGER hook dispatch does not pass
        """
        ctx = HookPluginContext(setup_input.etcd, setup_input.local_config)
        await ctx.init(
            context=setup_input.init_context,
            allowlist=setup_input.allowed_plugins,
            blocklist=setup_input.disabled_plugins,
        )
        hook_result = await ctx.dispatch(
            "ACTIVATE_MANAGER",
            (),
            return_when=ALL_COMPLETED,
        )
        if hook_result.status != PASSED:
            raise RuntimeError("Could not activate the manager instance.")
        log.info("HookPluginContext initialized with plugins: {}", list(ctx.plugins.keys()))
        try:
            yield ctx
        finally:
            await ctx.cleanup()
