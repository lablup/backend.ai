from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Final

from ai.backend.common.exception import BackendAIError
from ai.backend.common.plugins.base import BasePlugin, BasePluginConfig
from ai.backend.manager.data.auth.types import UserData
from ai.backend.manager.dto.auth.lookup import UserLookupData
from ai.backend.manager.dto.auth.request import HTTPRequestData

MIN_LOOKUP_RETRY_COUNT: Final[int] = 0

AUTH_PLUGIN_GROUP: Final[str] = "backendai_auth_v1"


class AuthPluginConfig(BasePluginConfig):
    """The `plugin-config.auth.<name>` section an authentication plugin is created from."""


class AuthPlugin(BasePlugin[AuthPluginConfig], metaclass=ABCMeta):
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
