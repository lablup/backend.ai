from collections.abc import Mapping
from decimal import Decimal
from typing import Any, override

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.resources import AbstractComputePlugin
from ai.backend.agent.types import AbstractAgentDiscovery
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.types import DeviceName, SlotName

__all__ = ("CocoAgentDiscovery", "get_agent_discovery")


class CocoAgentDiscovery(AbstractAgentDiscovery):
    @override
    def get_agent_cls(self) -> type[AbstractAgent[Any, Any]]:
        from .agent import CocoAgent

        return CocoAgent

    @override
    async def load_resources(
        self, etcd: AbstractKVStore, local_config: Mapping[str, Any]
    ) -> Mapping[DeviceName, AbstractComputePlugin]:
        from .resources import load_resources

        return await load_resources(etcd, local_config)

    @override
    async def scan_available_resources(
        self, compute_device_types: Mapping[DeviceName, AbstractComputePlugin]
    ) -> Mapping[SlotName, Decimal]:
        from .resources import scan_available_resources

        return await scan_available_resources(compute_device_types)

    @override
    async def prepare_krunner_env(self, local_config: Mapping[str, Any]) -> Mapping[str, str]:
        return {}


def get_agent_discovery() -> AbstractAgentDiscovery:
    return CocoAgentDiscovery()
