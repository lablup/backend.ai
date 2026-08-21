"""enroot agent backend (BEP-1062, rootless).

Selectable via ``agent.backend = "enroot"``. Runs the same Linux session containers as the
containerd backend, but launches them through the **enroot** CLI (squashfs image + userns)
instead of a containerd daemon — a rootless/daemonless runtime aimed at HPC-style GPU nodes.

Design: this backend reuses the *entire* containerd agent (``ContainerdAgent`` — the OCI-spec
build, BEP-1062 session networking, scratch/ssh/recovery) and swaps only the ``OciRuntime``
implementation for :class:`~ai.backend.agent.enroot.runtime.EnrootRuntime`. The single seam is
``ContainerdAgent._create_runtime()``. Resource detection and krunner provisioning are identical
to containerd (same cgroup-based compute plugins, same extract-to-host krunner), so those are
reused verbatim.
"""

from collections.abc import Mapping
from decimal import Decimal
from typing import Any, override

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.containerd.krunner import prepare_krunner_env
from ai.backend.agent.containerd.runtime.interface import OciRuntime
from ai.backend.agent.resources import (
    AbstractComputePlugin,
    load_resources,
    scan_available_resources,
)
from ai.backend.agent.types import AbstractAgentDiscovery
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.types import DeviceName, SlotName

from .agent import EnrootAgent, create_runtime


class EnrootAgentDiscovery(AbstractAgentDiscovery):
    @override
    def get_agent_cls(self) -> type[AbstractAgent[Any, Any]]:
        return EnrootAgent

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

    @override
    def create_oci_runtime(self, local_config: AgentUnifiedConfig) -> OciRuntime:
        return create_runtime(local_config)


def get_agent_discovery() -> AbstractAgentDiscovery:
    return EnrootAgentDiscovery()
