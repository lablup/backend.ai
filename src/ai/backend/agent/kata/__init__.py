"""
KataAgent backend package.

Selected via ``[agent] backend = "kata"`` in the agent config. The discovery
object reuses the Docker backend's resource detection and krunner-volume
preparation verbatim — only the agent class (and thus the kernel create/start
path) differs.
"""

from collections.abc import Mapping
from decimal import Decimal
from typing import Any, override

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.docker.kernel import prepare_krunner_env
from ai.backend.agent.docker.resources import load_resources, scan_available_resources
from ai.backend.agent.resources import AbstractComputePlugin
from ai.backend.agent.types import AbstractAgentDiscovery
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.types import DeviceName, SlotName

from .agent import KataAgent


class KataAgentDiscovery(AbstractAgentDiscovery):
    @override
    def get_agent_cls(self) -> type[AbstractAgent[Any, Any]]:
        return KataAgent

    @override
    async def load_resources(
        self,
        etcd: AbstractKVStore,
        local_config: Mapping[str, Any],
    ) -> Mapping[DeviceName, AbstractComputePlugin]:
        # Resource detection is host-level and backend-agnostic; reuse Docker's.
        return await load_resources(etcd, local_config)

    @override
    async def scan_available_resources(
        self, compute_device_types: Mapping[DeviceName, AbstractComputePlugin]
    ) -> Mapping[SlotName, Decimal]:
        return await scan_available_resources(compute_device_types)

    @override
    async def prepare_krunner_env(self, local_config: Mapping[str, Any]) -> Mapping[str, str]:
        # krunner volumes are still created via dockerd; the KataAgent resolves
        # the named volume to its host path and bind-mounts it into the guest.
        return await prepare_krunner_env(local_config)


def get_agent_discovery() -> AbstractAgentDiscovery:
    return KataAgentDiscovery()
