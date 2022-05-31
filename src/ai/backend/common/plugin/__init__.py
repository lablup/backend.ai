from __future__ import annotations

from abc import ABCMeta, abstractmethod
import asyncio
import logging
import pkg_resources
import re
from typing import (
    Any,
    ClassVar,
    Container,
    Dict,
    Generic,
    Iterator,
    Mapping,
    Tuple,
    Type,
    TypeVar,
)
from weakref import WeakSet

from ai.backend.common.asyncio import cancel_tasks

from ..etcd import AsyncEtcd
from ..logging_utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__name__))

__all__ = (
    'AbstractPlugin',
    'BasePluginContext',
)


class AbstractPlugin(metaclass=ABCMeta):
    """
    The minimum generic plugin interface.
    """

    plugin_config: Mapping[str, Any]
    """
    ``plugin_config`` contains the plugin-specific configuration read from the etcd.
    """

    local_config: Mapping[str, Any]
    """
    ``local_config`` contains the configuration read from the disk TOML file of the current daemon.
    This configuration is only updated when restarting the daemon and thus plugins should assume
    that it's read-only and immutable during its lifetime.
    e.g., If the plugin is running with the manager, it's the validated content of manager.toml file.
    """

    config_watch_enabled: ClassVar[bool] = True
    """
    If set True (default), the hosting plugin context will watch and automatically update
    the etcd's plugin configuration changes via the ``update_plugin_config()`` method.
    """

    def __init__(self, plugin_config: Mapping[str, Any], local_config: Mapping[str, Any]) -> None:
        """
        Instantiate the plugin with the given initial configuration.
        """
        self.plugin_config = plugin_config
        self.local_config = local_config

    @abstractmethod
    async def init(self, context: Any = None) -> None:
        """
        Initialize any resource used by the plugin.
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """
        Clean up any resource used by the plugin upon server cleanup.
        """
        pass

    @abstractmethod
    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        """
        Handle runtime configuration updates.
        The config parameter contains both the updated parts
        and unchanged parts of the configuration.

        The default implementation is just to replace the config property,
        but actual plugins may trigger other operations to reflect config changes
        and/or inspect the differences of configs before replacing the current config.
        """
        self.plugin_config = plugin_config


P = TypeVar('P', bound=AbstractPlugin)


class BasePluginContext(Generic[P]):
    """
    A minimal plugin manager which controls the lifecycles of the given plugins
    and watches & applies the configuration changes in etcd.

    The subclasses must redefine ``plugin_group``.
    """

    etcd: AsyncEtcd
    local_config: Mapping[str, Any]
    plugins: Dict[str, P]
    plugin_group: ClassVar[str] = 'backendai_XXX_v10'

    _config_watchers: WeakSet[asyncio.Task]

    def __init__(self, etcd: AsyncEtcd, local_config: Mapping[str, Any]) -> None:
        self.etcd = etcd
        self.local_config = local_config
        self.plugins = {}
        self._config_watchers = WeakSet()
        if m := re.search(r'^backendai_(\w+)_v(\d+)$', self.plugin_group):
            self._group_key = m.group(1)
        else:
            raise TypeError(
                f"{type(self).__name__} has invalid plugin_group class attribute",
                self.plugin_group,
            )

    @classmethod
    def discover_plugins(
        cls,
        plugin_group: str,
        blocklist: Container[str] = None,
    ) -> Iterator[Tuple[str, Type[P]]]:
        if blocklist is None:
            blocklist = set()
        for entrypoint in pkg_resources.iter_entry_points(plugin_group):
            if entrypoint.name in blocklist:
                continue
            log.info('loading plugin (group:{}): {}', plugin_group, entrypoint.name)
            yield entrypoint.name, entrypoint.load()

    async def init(self, context: Any = None) -> None:
        scanned_plugins = self.discover_plugins(self.plugin_group)
        for plugin_name, plugin_entry in scanned_plugins:
            plugin_config = await self.etcd.get_prefix(
                f"config/plugins/{self._group_key}/{plugin_name}/",
            )
            try:
                plugin_instance = plugin_entry(plugin_config, self.local_config)
                await plugin_instance.init(context=context)
            except Exception:
                log.exception('error during initialization of plugin: {}', plugin_name)
                continue
            else:
                self.plugins[plugin_name] = plugin_instance
            if plugin_instance.config_watch_enabled:
                await self.watch_config_changes(plugin_name)
        await asyncio.sleep(0)

    async def cleanup(self) -> None:
        await cancel_tasks(self._config_watchers)
        await asyncio.sleep(0)
        for plugin_instance in self.plugins.values():
            await plugin_instance.cleanup()

    async def _watcher(self, plugin_name: str) -> None:
        # As wait_timeout applies to the waiting for an internal async queue,
        # so short timeouts for polling the changes does not incur gRPC/network overheads.
        async for _ in self.etcd.watch_prefix(
            f"config/plugins/{self._group_key}/{plugin_name}",
            wait_timeout=0.2,
        ):
            new_config = await self.etcd.get_prefix(
                f"config/plugins/{self._group_key}/{plugin_name}/",
            )
            await self.plugins[plugin_name].update_plugin_config(new_config)

    async def watch_config_changes(self, plugin_name: str) -> None:
        wtask = asyncio.create_task(self._watcher(plugin_name))
        self._config_watchers.add(wtask)
