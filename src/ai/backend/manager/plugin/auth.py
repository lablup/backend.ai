from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Iterator, Mapping
from typing import Any, Final, override

from ai.backend.common.exception import BackendAIError, ConfigurationError
from ai.backend.common.plugin import AbstractPlugin, BasePluginContext
from ai.backend.manager.data.auth.lookup import UserLookupData
from ai.backend.manager.data.auth.request import HTTPRequestData
from ai.backend.manager.data.auth.types import UserData

MIN_LOOKUP_RETRY_COUNT: Final[int] = 0


class AbstractAuthPlugin(AbstractPlugin, metaclass=ABCMeta):
    """The contract an authentication integration implements.

    The plugin names the account a request belongs to; the manager performs the
    lookup, the status checks and everything downstream.
    """

    @classmethod
    @abstractmethod
    def lookup_retry_count(cls) -> int:
        """How many times the manager re-runs the lookup after ``on_user_lookup_error``.

        Zero or less asks for no retry; the manager still performs the lookup once.
        """
        raise NotImplementedError

    @override
    async def init(self, context: Any | None = None) -> None:
        pass

    @override
    async def cleanup(self) -> None:
        pass

    @override
    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        self.plugin_config = plugin_config

    @abstractmethod
    async def generate_lookup_data(self, request: HTTPRequestData) -> UserLookupData | None:
        """Verify the credential the request carries and name the account it belongs to.

        The manager resolves the returned key without verifying the credential itself.
        Return ``None`` when the request carries no credential this plugin handles.
        """
        raise NotImplementedError

    @abstractmethod
    async def on_user_lookup_success(self, user: UserData) -> None:
        """Called once the manager has resolved the account the lookup data named."""
        raise NotImplementedError

    @abstractmethod
    async def on_user_lookup_error(self, error: BackendAIError) -> None:
        """Called for every failed lookup attempt; decides what happens next.

        Returning lets the manager try the lookup again, up to lookup_retry_count.
        Raising aborts the sign-in at once.
        """
        raise NotImplementedError


class AuthPluginContext(BasePluginContext[AbstractAuthPlugin]):
    plugin_group = "backendai_auth_v1"

    @property
    def plugin(self) -> AbstractAuthPlugin | None:
        """The single loaded plugin, or None when no integration is installed."""
        for plugin_instance in self.plugins.values():
            return plugin_instance
        return None

    @override
    @classmethod
    def discover_plugins(
        cls,
        plugin_group: str,
        allowlist: set[str] | None = None,
        blocklist: set[str] | None = None,
    ) -> Iterator[tuple[str, type[AbstractAuthPlugin]]]:
        """Reject a second plugin here, before any of them is instantiated."""
        discovered = list(
            super().discover_plugins(plugin_group, allowlist=allowlist, blocklist=blocklist)
        )
        if len(discovered) > 1:
            names = ", ".join(sorted(name for name, _ in discovered))
            raise ConfigurationError({
                "plugin.AuthPluginContext": (
                    f"Only one authentication plugin may be loaded, but {len(discovered)} were"
                    f" found: {names}. Keep one and list the rest in"
                    " manager.disabled-plugins."
                )
            })
        return iter(discovered)
