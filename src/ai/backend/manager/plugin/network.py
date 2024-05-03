from abc import ABCMeta, abstractmethod
from typing import Any

from ai.backend.common.plugin import AbstractPlugin, BasePluginContext


class AbstractNetworkManagerPlugin(AbstractPlugin, metaclass=ABCMeta):
    @abstractmethod
    async def create_network(
        self,
        *,
        identifier: str | None = None,
        options: dict[str, Any] = {},
    ) -> dict[str, Any]:
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
        network_name: str,
        session: SessionRow,
    ) -> None:
        """
        Destroys network which were used to bind containers.
        """
        raise NotImplementedError


class NetworkPluginContext(BasePluginContext[AbstractNetworkManagerPlugin]):
    plugin_group = "backendai_network_manager_v1"
