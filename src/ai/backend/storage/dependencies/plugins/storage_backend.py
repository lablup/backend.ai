from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.logging.structured import StructuredLogger
from ai.backend.storage.plugin import StoragePluginContext

from .base import PluginDependency, PluginsInput

log = StructuredLogger(logging.getLogger(__spec__.name))


class StorageBackendPluginDependency(PluginDependency[StoragePluginContext]):
    """Provides the storage backend plugin context lifecycle."""

    @property
    @override
    def stage_name(self) -> str:
        return "storage-backend-plugin"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: PluginsInput) -> AsyncIterator[StoragePluginContext]:
        ctx = StoragePluginContext(setup_input.etcd, setup_input.local_config)
        await ctx.init()
        log.info("storage plugins loaded", plugin_names=", ".join(ctx.plugins.keys()))
        try:
            yield ctx
        finally:
            await ctx.cleanup()
