from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import NewType, Self

from pydantic import BaseModel, ConfigDict

PluginName = NewType("PluginName", str)


class BasePluginConfig(BaseModel):
    """The settings a plugin is created from.

    Extra keys are kept so a plugin can read the settings only it knows about.
    """

    model_config = ConfigDict(frozen=True, extra="allow")


class BasePlugin[TPluginConfig: BasePluginConfig](metaclass=ABCMeta):
    """The contract every plugin implements.

    A plugin is built from its settings and holds no resource, so there is nothing to
    initialize or clean up. Do not implement this class directly: subclass the domain
    base for the kind of plugin it is, such as `AuthPlugin`.
    """

    @classmethod
    @abstractmethod
    def create(cls, config: TPluginConfig) -> Self:
        """Build the plugin from the settings the manager loaded for it."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def name(cls) -> PluginName:
        """The name this plugin is known by."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def description(cls) -> str:
        """What this plugin does, for an operator reading the loaded plugin list."""
        raise NotImplementedError
