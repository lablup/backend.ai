"""Runtime-neutral cluster-network manager plugin (CNI/etcd control plane).

Replaces the Swarm-based `OverlayNetworkPlugin` for containerd and other host-native
runtimes. This plugin owns the *control plane*: it allocates a per-session subnet
(and a VNI for the vxlan backend), selects the data-plane backend from agent
capabilities, and writes the session network descriptor to etcd. The data plane
itself is realized by the agent-side v2 plugins (see BEP-1055/agent-plugin-v2.md).

NOTE: This is a P1 skeleton. Allocation and etcd writes are implemented in P2.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ai.backend.common.network.types import NetworkBackendKind
from ai.backend.manager.network.ipam import SubnetAllocator, VNIAllocator
from ai.backend.manager.plugin.network import AbstractNetworkManagerPlugin, NetworkInfo


class CNINetworkPlugin(AbstractNetworkManagerPlugin):
    """Control-plane plugin for the runtime-neutral cluster network (BEP-1055)."""

    _subnet_allocator: SubnetAllocator
    _vni_allocator: VNIAllocator
    _forced_backend: NetworkBackendKind | None

    def __init__(self, plugin_config: Mapping[str, Any], local_config: Mapping[str, Any]) -> None:
        super().__init__(plugin_config, local_config)
        self._forced_backend = None

    async def init(self, context: Any = None) -> None:
        # P2: obtain AsyncEtcd from context, construct allocators, load config
        # (network/config/*, InterContainerNetworkConfig.forced_backend).
        raise NotImplementedError("BEP-1055 P2")

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        return await super().update_plugin_config(plugin_config)

    async def create_network(
        self, *, identifier: str | None = None, options: dict[str, Any] | None = None
    ) -> NetworkInfo:
        # P2: options["member_agents"] -> select backend from caps -> allocate subnet
        # (+VNI) via CAS -> write network/session/{identifier}/meta -> return NetworkInfo
        # carrying {backend, subnet, vni, mtu}.
        raise NotImplementedError("BEP-1055 P2")

    async def destroy_network(self, network_id: str) -> None:
        # P2: delete network/session/{network_id} prefix and release subnet/VNI.
        raise NotImplementedError("BEP-1055 P2")

    async def _select_backend(self, member_agents: list[str]) -> NetworkBackendKind:
        # P2: forced_backend or capability-based (host-gw if all native-capable, else vxlan).
        raise NotImplementedError("BEP-1055 P2")
