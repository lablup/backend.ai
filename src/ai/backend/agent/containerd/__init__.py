"""Containerd agent backend (BEP-1058).

Selectable via ``agent.backend = "containerd"``. Reuses the Docker backend's resource and
compute-plugin logic (containerd runs the same Linux containers with the same cgroup-based
compute plugins), but provisions krunner natively (extract-to-host-dir, no Docker/nerdctl).
"""

from collections.abc import Mapping
from decimal import Decimal
from typing import Any, override

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.containerd.krunner import prepare_krunner_env
from ai.backend.agent.resources import (
    AbstractComputePlugin,
    load_resources,
    scan_available_resources,
)
from ai.backend.agent.types import AbstractAgentDiscovery
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.types import DeviceName, SlotName

from .agent import ContainerdAgent


class ContainerdAgentDiscovery(AbstractAgentDiscovery):
    @override
    def get_agent_cls(self) -> type[AbstractAgent[Any, Any]]:
        return ContainerdAgent

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
    return ContainerdAgentDiscovery()
