from decimal import Decimal
from typing import Any, Mapping, Type, override

from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.types import DeviceName, SlotName

from ..agent import AbstractAgent
from ..resources import AbstractComputePlugin
from ..types import AbstractAgentDiscovery
from .agent import DockerAgent
from .kernel import prepare_krunner_env
from .resources import load_resources, scan_available_resources


class DockerAgentDiscovery(AbstractAgentDiscovery):
    @override
    def get_agent_cls(self) -> Type[AbstractAgent]:
        return DockerAgent

    @override
    async def load_resources(
        self,
        etcd: AbstractKVStore,
        local_config: Mapping[str, Any],
    ) -> Mapping[DeviceName, AbstractComputePlugin]:
        return await load_resources(etcd, local_config)

    @override
    async def scan_available_resources(
        self, compute_device_types: Mapping[DeviceName, AbstractComputePlugin]
    ) -> Mapping[SlotName, Decimal]:
        return await scan_available_resources(compute_device_types)

    @override
    async def prepare_krunner_env(self, local_config: Mapping[str, Any]) -> Mapping[str, str]:
        return await prepare_krunner_env(local_config)


def get_agent_discovery() -> AbstractAgentDiscovery:
    return DockerAgentDiscovery()
