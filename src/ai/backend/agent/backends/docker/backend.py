import logging
from decimal import Decimal
from typing import Any, Mapping, override

from aiodocker import Docker
from aiotools import closing_async

from ai.backend.agent.agent import ComputerContext
from ai.backend.agent.backends.backend import AbstractBackend
from ai.backend.agent.backends.type import BackendArgs
from ai.backend.agent.docker.resources import load_resources, scan_available_resources
from ai.backend.agent.resources import AbstractComputePlugin
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.types import DeviceName, SlotName
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DockerBackend(AbstractBackend):
    _etcd: AsyncEtcd
    _local_config: Mapping[str, Any]

    def __init__(self, args: BackendArgs) -> None:
        """
        Initialize the Docker backend with the provided arguments.
        """
        self._etcd = args.etcd
        self._local_config = args.local_config

    @override
    async def load_resources(
        self,
    ) -> Mapping[DeviceName, AbstractComputePlugin]:
        """
        Detect available resources attached on the system and load corresponding device plugin.
        """
        return await load_resources(self._etcd, self._local_config)

    @override
    async def scan_available_resources(
        self, computers: Mapping[DeviceName, ComputerContext]
    ) -> Mapping[SlotName, Decimal]:
        """
        Scan and define the amount of available resource slots in this node.
        """
        return await scan_available_resources(
            self._local_config, {name: cctx.instance for name, cctx in computers.items()}
        )

    @override
    async def create_local_network(self, network_name: str) -> None:
        async with closing_async(Docker()) as docker:
            await docker.networks.create({
                "Name": network_name,
                "Driver": "bridge",
                "Labels": {
                    "ai.backend.cluster-network": "1",
                },
            })

    @override
    async def destroy_local_network(self, network_name: str) -> None:
        async with closing_async(Docker()) as docker:
            network = await docker.networks.get(network_name)
            await network.delete()
