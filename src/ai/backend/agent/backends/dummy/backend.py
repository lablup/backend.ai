import asyncio
from decimal import Decimal
from typing import Any, Mapping, override

from ai.backend.agent.agent import ComputerContext
from ai.backend.agent.backends.type import BackendArgs
from ai.backend.agent.dummy.config import DEFAULT_CONFIG_PATH, dummy_local_config
from ai.backend.agent.dummy.resources import load_resources, scan_available_resources
from ai.backend.common.config import read_from_file
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.types import DeviceName, SlotName

from ...resources import AbstractComputePlugin
from ..backend import AbstractBackend


class DummyBackend(AbstractBackend):
    _etcd: AsyncEtcd
    _local_config: Mapping[str, Any]
    _dummy_config: Mapping[str, Any]
    _dummy_agent_cfg: Mapping[str, Any]

    def __init__(self, args: BackendArgs) -> None:
        self._etcd = args.etcd
        self._local_config = args.local_config
        # Load the dummy local config
        raw_config, _ = read_from_file(DEFAULT_CONFIG_PATH, "dummy")
        self._dummy_config = dummy_local_config.check(raw_config)
        self._dummy_agent_cfg = self._dummy_config["agent"]

    @override
    async def load_resources(
        self,
    ) -> Mapping[DeviceName, AbstractComputePlugin]:
        return await load_resources(self._etcd, self._local_config, self._dummy_config)

    @override
    async def scan_available_resources(
        self, computers: Mapping[DeviceName, ComputerContext]
    ) -> Mapping[SlotName, Decimal]:
        return await scan_available_resources(
            self._local_config, {name: cctx.instance for name, cctx in computers.items()}
        )

    @override
    async def create_local_network(self, network_name: str) -> None:
        delay = self._dummy_agent_cfg["delay"]["create-network"]
        await asyncio.sleep(delay)

    @override
    async def destroy_local_network(self, network_name: str) -> None:
        delay = self._dummy_agent_cfg["delay"]["destroy-network"]
        await asyncio.sleep(delay)
