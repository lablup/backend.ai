from __future__ import annotations

from abc import abstractmethod
from typing import Iterator, Optional

from ai.backend.common.plugin import AbstractPlugin, BasePluginContext
from ai.backend.storage.abc import AbstractVolume


class AbstractStoragePlugin(AbstractPlugin):
    @abstractmethod
    def get_volume_class(
        self,
    ) -> type[AbstractVolume]:
        raise NotImplementedError


class StoragePluginContext(BasePluginContext[AbstractStoragePlugin]):
    plugin_group = "backendai_storage_v10"

    @classmethod
    def discover_plugins(
        cls,
        plugin_group: str,
        allowlist: Optional[set[str]] = None,
        blocklist: Optional[set[str]] = None,
    ) -> Iterator[tuple[str, type[AbstractStoragePlugin]]]:
        scanned_plugins = [*super().discover_plugins(plugin_group, allowlist, blocklist)]
        yield from scanned_plugins
