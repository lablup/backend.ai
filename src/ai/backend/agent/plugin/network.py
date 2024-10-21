from abc import ABCMeta, abstractmethod
from typing import Any, Generic, TypeVar

from ai.backend.agent.kernel import AbstractKernel
from ai.backend.common.plugin import AbstractPlugin, BasePluginContext
from ai.backend.common.types import ClusterInfo, KernelCreationConfig

TKernel = TypeVar("TKernel", bound=AbstractKernel)


class AbstractNetworkAgentPlugin(AbstractPlugin, Generic[TKernel], metaclass=ABCMeta):
    @abstractmethod
    async def join_network(
        self,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
        *,
        network_name: str,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Returns required container config to attach container to network.
        """
        raise NotImplementedError

    @abstractmethod
    async def leave_network(
        self,
        kernel: TKernel,
    ) -> None:
        """
        Performs extra step to make container leave from the network.
        """
        raise NotImplementedError


class NetworkPluginContext(BasePluginContext[AbstractNetworkAgentPlugin]):
    plugin_group = "backendai_network_client_v1"
