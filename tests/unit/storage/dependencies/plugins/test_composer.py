from __future__ import annotations

from typing import override
from unittest.mock import MagicMock

from ai.backend.common.dependencies import (
    DependencyComposer,
    DependencyProvider,
    DependencyStack,
    ResourcesT,
    ResourceT,
    SetupInputT,
)
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.storage.dependencies.plugins.base import PluginsInput
from ai.backend.storage.dependencies.plugins.composer import PluginsComposer
from ai.backend.storage.plugin import AbstractStoragePlugin, StoragePluginContext
from ai.backend.storage.volumes.backends import DEFAULT_BACKENDS
from ai.backend.storage.volumes.vfs import BaseVolume


class StubStack(DependencyStack):
    """A stack that hands back a prepared resource instead of running the provider."""

    def __init__(self, resource: object) -> None:
        self._resource = resource

    @override
    async def enter_dependency(
        self,
        provider: DependencyProvider[SetupInputT, ResourceT],
        setup_input: SetupInputT,
    ) -> ResourceT:
        return self._resource  # type: ignore[return-value]

    @override
    async def enter_composer(
        self,
        composer: DependencyComposer[SetupInputT, ResourcesT],
        setup_input: SetupInputT,
    ) -> ResourcesT:
        raise NotImplementedError


def plugin_ctx(plugins: dict[str, AbstractStoragePlugin]) -> StoragePluginContext:
    ctx = MagicMock(spec=StoragePluginContext)
    ctx.plugins = plugins
    return ctx


def plugins_input() -> PluginsInput:
    return PluginsInput(etcd=MagicMock(spec=AsyncEtcd), local_config={})


class TestPluginsComposer:
    """Test the volume backend registry composed from the storage plugin context."""

    async def test_defaults_without_plugins(self) -> None:
        ctx = plugin_ctx({})

        async with PluginsComposer().compose(StubStack(ctx), plugins_input()) as resources:
            assert resources.storage_backend_plugin_ctx is ctx
            assert resources.backends == DEFAULT_BACKENDS

    async def test_plugin_volume_class_is_registered(self) -> None:
        class CustomVolume(BaseVolume):
            name = "custom"

        plugin = MagicMock(spec=AbstractStoragePlugin)
        plugin.get_volume_class.return_value = CustomVolume
        ctx = plugin_ctx({"custom": plugin})

        async with PluginsComposer().compose(StubStack(ctx), plugins_input()) as resources:
            assert resources.backends["custom"] is CustomVolume
            assert all(resources.backends[name] is cls for name, cls in DEFAULT_BACKENDS.items())

    async def test_plugin_overrides_default_backend(self) -> None:
        class OverridingVolume(BaseVolume):
            name = "vfs"

        plugin = MagicMock(spec=AbstractStoragePlugin)
        plugin.get_volume_class.return_value = OverridingVolume
        ctx = plugin_ctx({"vfs": plugin})

        async with PluginsComposer().compose(StubStack(ctx), plugins_input()) as resources:
            assert resources.backends["vfs"] is OverridingVolume
