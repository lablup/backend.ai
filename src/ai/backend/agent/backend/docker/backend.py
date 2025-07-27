import asyncio
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import AsyncIterator, Optional, override

from aiodocker.docker import Docker, DockerError

from ai.backend.agent.affinity_map import AffinityMap
from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.data.cgroup import CGroupInfo
from ai.backend.agent.data.kernel.creator import KernelCreationInfo
from ai.backend.agent.docker.utils import PersistentServiceContainer
from ai.backend.agent.plugin.network import NetworkPluginContext
from ai.backend.agent.resources import ComputerContext
from ai.backend.agent.types import (
    Container,
)
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.docker import (
    ImageRef,
)
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import (
    AgentId,
    ContainerId,
    ContainerStatus,
    DeviceName,
    ImageRegistry,
    KernelId,
    Sentinel,
)

from ..abc import AbstractBackend
from ..defs import ACTIVE_STATUS_SET
from .kernel_lifecycle.stage import (
    KernelCreationProvisioner,
    KernelCreationSpec,
    KernelCreationSpecGenerator,
    KernelCreationStage,
)


class DockerBackend(AbstractBackend):
    def __init__(
        self,
        config: AgentUnifiedConfig,
        computers: Mapping[DeviceName, ComputerContext],
        affinity_map: AffinityMap,
        resource_lock: asyncio.Lock,
        network_plugin_ctx: NetworkPluginContext,
        gwbridge_subnet: Optional[str],
        agent_sockpath: Path,
        *,
        event_producer: EventProducer,
        valkey_stat_client: ValkeyStatClient,
    ) -> None:
        self._config = config
        self._computers = computers
        self._affinity_map = affinity_map
        self._resource_lock = resource_lock
        self._network_plugin_ctx = network_plugin_ctx
        self._gwbridge_subnet = gwbridge_subnet
        self._agent_sockpath = agent_sockpath

        self._event_producer = event_producer
        self._valkey_stat_client = valkey_stat_client

    @override
    async def create_kernel(
        self,
        info: KernelCreationInfo,
        *,
        throttle_sema: Optional[asyncio.Semaphore] = None,
    ) -> None:
        spec = KernelCreationSpec.from_creation_info(info)
        stage = KernelCreationStage(
            KernelCreationProvisioner(
                self._config,
                self._computers,
                self._affinity_map,
                self._resource_lock,
                self._network_plugin_ctx,
                self._gwbridge_subnet,
                self._agent_sockpath,
                event_producer=self._event_producer,
                valkey_stat_client=self._valkey_stat_client,
            )
        )
        await stage.setup(KernelCreationSpecGenerator(spec))
        _ = await stage.wait_for_resource()

    @override
    async def create_local_network(self, network_name: str) -> None:
        """
        Create a local bridge network for a single-node multicontainer session, where containers in the
        same agent can connect to each other using cluster hostnames without explicit port mapping.

        This is called by the manager before kernel creation.
        It may raise :exc:`NotImplementedError` and then the manager
        will cancel creation of the session.
        """
        raise NotImplementedError

    @override
    async def destroy_kernel(self, kernel_id: KernelId) -> None:
        raise NotImplementedError

    @override
    async def destroy_local_network(self, network_name: str) -> None:
        """
        Destroy a local bridge network used for a single-node multi-container session.

        This is called by the manager after kernel destruction.
        """
        raise NotImplementedError

    @override
    async def clean_kernel(self, kernel_id: KernelId) -> None:
        raise NotImplementedError

    @override
    async def restart_kernel(self, kernel_id: KernelId) -> None:
        # TODO: Implement kernel restart logic
        raise NotImplementedError

    @override
    async def yield_temp_container(self, image: ImageRef) -> AsyncIterator[Container]:
        """
        Yield a temporary container from given image.
        This is used to run backend-specific tasks that require a container.
        The container should be cleaned up after use.
        """
        raise NotImplementedError

    @override
    async def get_container_logs(self, container_id: ContainerId) -> list[str]:
        """
        Get the logs of the container.
        This method should return a list of log lines as strings.
        """
        raise NotImplementedError

    @override
    async def get_managed_images(self) -> tuple[ImageRef]:
        raise NotImplementedError

    @override
    async def get_managed_containers(
        self,
        agent_id: Optional[AgentId] = None,
        status_filter: frozenset[ContainerStatus] = ACTIVE_STATUS_SET,
    ) -> tuple[Container]:
        """
        Get all containers managed by this backend.
        This method should return a tuple of Container objects.
        """
        raise NotImplementedError

    @override
    def get_cgroup_info(self, container_id: ContainerId, controller: str) -> CGroupInfo:
        """
        Get the cgroup path for the given controller and container ID, and the cgroup version.
        This is used to read/write cgroup files for resource management.
        """
        raise NotImplementedError

    @override
    async def push_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout: float | None | Sentinel = Sentinel.TOKEN,
    ) -> None:
        """
        Push the image.
        This method should be implemented by the backend to handle image pushing.
        """
        raise NotImplementedError

    @override
    async def pull_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout: float | None | Sentinel = Sentinel.TOKEN,
    ) -> None:
        """
        Pull the image.
        This method should be implemented by the backend to handle image pulling.
        """
        raise NotImplementedError


async def make_docker_backend(
    config: AgentUnifiedConfig,
    local_instance_id: str,
    computers: Mapping[DeviceName, ComputerContext],
    affinity_map: AffinityMap,
    resource_lock: asyncio.Lock,
    network_plugin_ctx: NetworkPluginContext,
    *,
    event_producer: EventProducer,
    valkey_stat_client: ValkeyStatClient,
) -> DockerBackend:
    gwbridge_subnet: Optional[str] = None
    try:
        async with Docker() as docker:
            gwbridge = await docker.networks.get("docker_gwbridge")
            gwbridge_info = await gwbridge.show()
            gwbridge_subnet = gwbridge_info["IPAM"]["Config"][0]["Subnet"]
    except (DockerError, KeyError, IndexError):
        pass

    ipc_base_path = config.agent.ipc_base_path
    agent_sockpath = ipc_base_path / "container" / f"agent.{local_instance_id}.sock"
    if sys.platform != "darwin":
        socket_relay_name = f"backendai-socket-relay.{local_instance_id}"
        socket_relay_container = PersistentServiceContainer(
            "backendai-socket-relay:latest",
            {
                "Cmd": [
                    f"UNIX-LISTEN:/ipc/{agent_sockpath.name},unlink-early,fork,mode=777",
                    f"TCP-CONNECT:127.0.0.1:{config.agent.agent_sock_port}",
                ],
                "HostConfig": {
                    "Mounts": [
                        {
                            "Type": "bind",
                            "Source": str(ipc_base_path / "container"),
                            "Target": "/ipc",
                        },
                    ],
                    "NetworkMode": "host",
                },
            },
            name=socket_relay_name,
        )
        await socket_relay_container.ensure_running_latest()
    return DockerBackend(
        config,
        computers,
        affinity_map,
        resource_lock,
        network_plugin_ctx,
        gwbridge_subnet,
        agent_sockpath,
        event_producer=event_producer,
        valkey_stat_client=valkey_stat_client,
    )
