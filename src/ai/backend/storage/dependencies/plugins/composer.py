from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.storage.plugin import StoragePluginContext
from ai.backend.storage.volumes.abc import AbstractVolume
from ai.backend.storage.volumes.backends import DEFAULT_BACKENDS

from .base import PluginsInput
from .storage_backend import StorageBackendPluginDependency


@dataclass
class PluginsResources:
    """Container for all plugin context resources."""

    storage_backend_plugin_ctx: StoragePluginContext
    backends: Mapping[str, type[AbstractVolume]]


class PluginsComposer(DependencyComposer[PluginsInput, PluginsResources]):
    """Composes plugin context dependencies and the volume backend registry."""

    @property
    @override
    def stage_name(self) -> str:
        return "plugins"

    @asynccontextmanager
    @override
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: PluginsInput,
    ) -> AsyncIterator[PluginsResources]:
        storage_backend_plugin_ctx = await stack.enter_dependency(
            StorageBackendPluginDependency(),
            setup_input,
        )

        yield PluginsResources(
            storage_backend_plugin_ctx=storage_backend_plugin_ctx,
            backends=self._build_backends(storage_backend_plugin_ctx),
        )

    def _build_backends(
        self,
        plugin_ctx: StoragePluginContext,
    ) -> Mapping[str, type[AbstractVolume]]:
        backends: dict[str, type[AbstractVolume]] = {**DEFAULT_BACKENDS}
        for plugin_name, plugin_instance in plugin_ctx.plugins.items():
            backends[plugin_name] = plugin_instance.get_volume_class()
        return backends
