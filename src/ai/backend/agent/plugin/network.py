from abc import ABCMeta, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ai.backend.agent.kernel import AbstractKernel
from ai.backend.common.plugin import AbstractPlugin, BasePluginContext
from ai.backend.common.types import ClusterInfo, KernelCreationConfig


class ContainerNetworkCapability(StrEnum):
    GLOBAL = "global"
    """Referred when the network plugin replaces default bridge network and acts as a default route"""


@dataclass
class ContainerNetworkInfo:
    container_host: str
    services: Mapping[str, Mapping[int, int]]  # {service name: {container port: host port}}


class AbstractNetworkAgentPlugin[TKernel: AbstractKernel](AbstractPlugin, metaclass=ABCMeta):
    @abstractmethod
    async def get_capabilities(self) -> set[ContainerNetworkCapability]:
        """
        Returns set of ContainerNetworkCapability enum items. Each enum should represent
        feathre each network plugin is capable of.
        """
        raise NotImplementedError

    @abstractmethod
    async def join_network(
        self,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
        *,
        network_name: str,
        **kwargs: Any,
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

    async def prepare_port_forward(
        self,
        kernel: TKernel,
        bind_host: str,
        ports: Iterable[tuple[int, int]],
        **kwargs: Any,
    ) -> None:
        """
        Prepare underlying network setup before container is actually spawned.
        Only called by agent when `GLOBAL` attribute is advertised by plugin (`get_capabilities()`).
        """
        pass

    async def expose_ports(
        self,
        kernel: TKernel,
        bind_host: str,
        ports: Iterable[tuple[int, int]],
        **kwargs: Any,
    ) -> ContainerNetworkInfo | None:
        """
        Expose given set of ports to the public network after container is started.
        Only called by agent when `GLOBAL` attribute is advertised by plugin (`get_capabilities()`).
        """
        pass


class NetworkPluginContext(BasePluginContext[AbstractNetworkAgentPlugin]):
    plugin_group = "backendai_network_agent_v1"
