from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping

from ai.backend.common.plugin import AbstractPlugin, BasePluginContext


@dataclass
class NetworkInfo:
    network_id: str
    options: Mapping[str, Any]


class AbstractNetworkManagerPlugin(AbstractPlugin, metaclass=ABCMeta):
    @abstractmethod
    async def create_network(
        self,
        *,
        identifier: str | None = None,
        options: dict[str, Any] = {},
    ) -> NetworkInfo:
        """
        Creates a cross-container network and returns network config which later will be passed to agent.
        :param identifier: Optional network identifier. If not provided, a random identifier will be generated.
        :param options: Network options.
        :return: NetworkInfo object which contains network_id and options.
        """
        raise NotImplementedError

    @abstractmethod
    async def destroy_network(
        self,
        network_id: str,
    ) -> None:
        """
        Destroys network which were used to bind containers.
        """
        raise NotImplementedError


class NetworkPluginContext(BasePluginContext[AbstractNetworkManagerPlugin]):
    plugin_group = "backendai_network_manager_v1"
