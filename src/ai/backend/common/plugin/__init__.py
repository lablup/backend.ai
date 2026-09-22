from __future__ import annotations

import asyncio
import logging
import re
from abc import ABCMeta, abstractmethod
from collections.abc import Iterator, Mapping
from typing import Any, ClassVar, TypeVar, cast
from weakref import WeakSet

from ai.backend.common.asyncio import cancel_tasks
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.exception import ConfigurationError
from ai.backend.logging import BraceStyleAdapter
from ai.backend.plugin.entrypoint import scan_entrypoints

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = (
    "AbstractPlugin",
    "BasePluginContext",
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

    require_explicit_allow: ClassVar[bool] = False
    """
    If set True, this plugin will only be loaded when explicitly listed in the
    ``allowed_plugins`` configuration. When the allowlist is None (load all discovered
    plugins), plugins with this flag set will be skipped.
    """

    def __init__(self, plugin_config: Mapping[str, Any], local_config: Mapping[str, Any]) -> None:
        """
        Instantiate the plugin with the given initial configuration.
        """
        self.plugin_config = plugin_config
        self.local_config = local_config

    @abstractmethod
    async def init(self, context: Any | None = None) -> None:
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


P = TypeVar("P", bound=AbstractPlugin)


class BasePluginContext[P: AbstractPlugin]:
    """
    A minimal plugin manager which controls the lifecycles of the given plugins
    and watches & applies the configuration changes in etcd.

    The subclasses must redefine ``plugin_group``.
    """

    etcd: AbstractKVStore
    local_config: Mapping[str, Any]
    plugins: dict[str, P]
    plugin_group: ClassVar[str] = "backendai_XXX_v10"
    allowlist: ClassVar[set[str] | None] = None
    blocklist: ClassVar[set[str] | None] = None

    _config_watchers: WeakSet[asyncio.Task[Any]]

    def __init__(self, etcd: AbstractKVStore, local_config: Mapping[str, Any]) -> None:
        self.etcd = etcd
        self.local_config = local_config
        self.plugins = {}
        self._config_watchers = WeakSet()
        if m := re.search(r"^backendai_(\w+)_v(\d+)$", self.plugin_group):
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
        allowlist: set[str] | None = None,
        blocklist: set[str] | None = None,
    ) -> Iterator[tuple[str, type[P]]]:
        cls_allowlist = set() if cls.allowlist is None else cls.allowlist
        arg_allowlist = set() if allowlist is None else allowlist
        allowlist_enabled = allowlist is not None or cls.allowlist is not None
        cls_blocklist = set() if cls.blocklist is None else cls.blocklist
        arg_blocklist = set() if blocklist is None else blocklist
        for entrypoint in scan_entrypoints(
            plugin_group,
            allowlist=cls_allowlist | arg_allowlist if allowlist_enabled else None,
            blocklist=cls_blocklist | arg_blocklist,
        ):
            plugin_cls = entrypoint.load()
            if not (isinstance(plugin_cls, type) and issubclass(plugin_cls, AbstractPlugin)):
                log.warning(
                    "skipping plugin (group:{}): {} (not a valid AbstractPlugin subclass, got {})",
                    plugin_group,
                    entrypoint.name,
                    type(plugin_cls),
                )
                continue
            if not allowlist_enabled and plugin_cls.require_explicit_allow:
                log.info(
                    "skipping plugin (group:{}): {} (requires explicit allow)",
                    plugin_group,
                    entrypoint.name,
                )
                continue
            log.info("loading plugin (group:{}): {}", plugin_group, entrypoint.name)
            yield entrypoint.name, cast(type[P], plugin_cls)

    async def init(
        self,
        context: Any | None = None,
        allowlist: set[str] | None = None,
        blocklist: set[str] | None = None,
    ) -> None:
        if allowlist is not None and blocklist is not None:
            if union := allowlist & blocklist:
                raise ConfigurationError({
                    "plugin.BasePluginContext": f"allowlist and blocklist has union value '{union}'"
                })
        scanned_plugins = self.discover_plugins(
            self.plugin_group,
            allowlist=allowlist,
            blocklist=blocklist,
        )
        for plugin_name, plugin_entry in scanned_plugins:
            plugin_config = await self.etcd.get_prefix(
                f"config/plugins/{self._group_key}/{plugin_name}/",
            )
            try:
                plugin_instance = plugin_entry(plugin_config, self.local_config)
                await plugin_instance.init(context=context)
            except Exception:
                log.exception("error during initialization of plugin: {}", plugin_name)
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

    #: How long to wait before fetching again a configuration that could not be READ, doubling
    #: to the ceiling. Unbounded in count, because the alternative is losing the change.
    _CONFIG_RETRY_BACKOFF_SEC = 0.5
    _CONFIG_RETRY_CEILING_SEC = 30.0
    #: Where the doubling stops. Past this the delay is the ceiling anyway, and the shift is only
    #: a way to overflow.
    _CONFIG_RETRY_MAX_SHIFT = 8

    async def _watcher(self, plugin_name: str) -> None:
        # As wait_timeout applies to the waiting for an internal async queue,
        # so short timeouts for polling the changes does not incur gRPC/network overheads.
        async for _ in self.etcd.watch_prefix(
            f"config/plugins/{self._group_key}/{plugin_name}",
            wait_timeout=0.2,
        ):
            # Retried, not merely survived. The watch event that carried this change is consumed
            # either way, so a failure that is only logged leaves the change unapplied until some
            # LATER edit happens to arrive -- which, for a configuration an operator has finished
            # editing, is never.
            attempt = 0
            while not await self._apply_config(plugin_name):
                # Until it is read, not a fixed number of tries. The watch event that carried this
                # change is consumed either way, so giving up leaves the change unapplied until
                # some LATER edit arrives -- and for a configuration an operator has finished
                # editing, that is never. An etcd outage longer than a handful of seconds is
                # ordinary; the backoff is capped and this is cancelled with the task.
                await asyncio.sleep(
                    min(
                        self._CONFIG_RETRY_BACKOFF_SEC * (2**attempt),
                        self._CONFIG_RETRY_CEILING_SEC,
                    )
                )
                # Stops climbing once the ceiling is reached. Left to grow, `2**attempt` overflows
                # a float somewhere past a thousand tries -- about eight hours of retrying -- and
                # the watcher this loop exists to keep alive dies of the arithmetic.
                attempt = min(attempt + 1, self._CONFIG_RETRY_MAX_SHIFT)

    async def _apply_config(self, plugin_name: str) -> bool:
        """Read the plugin's configuration and hand it over. False if that could not be done.

        :return: ``True`` when the plugin holds a configuration it accepted -- which includes it
            REFUSING the new one, because a refusal is an answer and retrying will get the same.
        """
        try:
            new_config = await self.etcd.get_prefix(
                f"config/plugins/{self._group_key}/{plugin_name}/",
            )
        except Exception:
            # A momentary etcd failure. The value is still there to be read, so this is worth
            # coming back for.
            log.exception("could not read plugin {}'s configuration; retrying", plugin_name)
            return False
        try:
            await self.plugins[plugin_name].update_plugin_config(new_config)
        except Exception:
            # The plugin looked at it and said no. Retrying hands it the same value, so this is
            # reported and left: the operator's next edit is what changes the answer. What must
            # not happen either way is the watcher ending -- it used to, on the first of either
            # failure, and every later change including the correction went undelivered.
            log.exception(
                "plugin {} refused a configuration update; keeping the one it has and continuing"
                " to watch",
                plugin_name,
            )
        return True

    async def watch_config_changes(self, plugin_name: str) -> None:
        wtask = asyncio.create_task(self._watcher(plugin_name))
        self._config_watchers.add(wtask)
