from decimal import Decimal
from typing import Any, Mapping, override

from ai.backend.agent.agent import ComputerContext
from ai.backend.agent.backends.backend import AbstractBackend
from ai.backend.agent.backends.type import BackendArgs
from ai.backend.agent.kubernetes.resources import load_resources, scan_available_resources
from ai.backend.agent.resources import AbstractComputePlugin
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.types import DeviceName, SlotName


class KubernetesBackend(AbstractBackend):
    _etcd: AsyncEtcd
    _local_config: Mapping[str, Any]

    def __init__(self, args: BackendArgs) -> None:
        """
        Initialize the Kubernetes backend with the provided arguments.
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
        """
        Create a local bridge network for a single-node multicontainer session, where containers in the
        same agent can connect to each other using cluster hostnames without explicit port mapping.

        This is called by the manager before kernel creation.
        It may raise :exc:`NotImplementedError` and then the manager
        will cancel creation of the session.
        """
        raise NotImplementedError

    @override
    async def destroy_local_network(self, network_name: str) -> None:
        """
        Destroy a local bridge network used for a single-node multi-container session.

        This is called by the manager after kernel destruction.
        """
        raise NotImplementedError
