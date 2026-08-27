from __future__ import annotations

import logging

from ai.backend.common.exception import ConfigurationError
from ai.backend.common.plugins.discovery import scan_plugin_entrypoints
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.unified import PluginsConfig
from ai.backend.manager.plugins.auth import AUTH_PLUGIN_GROUP, AuthPlugin, AuthPluginConfig
from ai.backend.manager.plugins.plugins import ManagerPlugins

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ManagerPluginLoader:
    """Discovers the manager's plugins and builds each one from the settings its name keys."""

    _plugins_config: PluginsConfig
    _allowlist: set[str] | None
    _blocklist: set[str] | None

    def __init__(
        self,
        plugins_config: PluginsConfig,
        allowlist: set[str] | None = None,
        blocklist: set[str] | None = None,
    ) -> None:
        self._plugins_config = plugins_config
        self._allowlist = allowlist
        self._blocklist = blocklist

    def load(self) -> ManagerPlugins:
        return ManagerPlugins(auth_plugin=self._load_auth_plugin())

    def _load_auth_plugin(self) -> AuthPlugin | None:
        plugin_cls = self._discover_auth_plugin()
        if plugin_cls is None:
            return None
        config = self._plugins_config.auth.get(plugin_cls.name(), AuthPluginConfig())
        log.info("loaded auth plugin: {} ({})", plugin_cls.name(), plugin_cls.description())
        return plugin_cls.create(config)

    def _discover_auth_plugin(self) -> type[AuthPlugin] | None:
        """Reject a second plugin here, before any of them is built."""
        discovered: list[type[AuthPlugin]] = []
        for name, loaded in scan_plugin_entrypoints(
            AUTH_PLUGIN_GROUP,
            allowlist=self._allowlist,
            blocklist=self._blocklist,
        ):
            if not (isinstance(loaded, type) and issubclass(loaded, AuthPlugin)):
                log.warning(
                    "skipping plugin (group:{}): {} (not an AuthPlugin subclass, got {})",
                    AUTH_PLUGIN_GROUP,
                    name,
                    type(loaded),
                )
                continue
            discovered.append(loaded)
        if len(discovered) > 1:
            names = ", ".join(sorted(str(plugin_cls.name()) for plugin_cls in discovered))
            raise ConfigurationError({
                "plugins.ManagerPluginLoader": (
                    f"Only one authentication plugin may be loaded, but {len(discovered)} were"
                    f" found: {names}. Keep one and list the rest in manager.disabled-plugins."
                )
            })
        return discovered[0] if discovered else None
