"""Runtime-neutral cluster-network manager plugin (CNI/etcd control plane).

Replaces the Swarm-based `OverlayNetworkPlugin` for containerd and other host-native
runtimes. This plugin owns the *control plane*: it allocates a per-session subnet
(and a VNI for the vxlan backend), selects the data-plane backend from agent
capabilities, and writes the session network descriptor to etcd. The data plane
itself is realized by the agent-side v2 plugins (see BEP-1055/agent-plugin-v2.md).
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from typing import Any

from ai.backend.common.configs.etcd import EtcdConfig
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.network.types import NetworkBackendKind
from ai.backend.manager.errors.network import NetworkBackendMismatch
from ai.backend.manager.network.ipam import SubnetAllocator, VNIAllocator
from ai.backend.manager.plugin.network import AbstractNetworkManagerPlugin, NetworkInfo

_DEFAULT_MTU = 1500

# Agent backends whose network stack can serve the BEP-1055 'cni' driver.
_CNI_COMPATIBLE_BACKENDS = frozenset({"containerd"})


def _session_meta_key(session_id: str) -> str:
    return f"network/session/{session_id}/meta"


class CNINetworkPlugin(AbstractNetworkManagerPlugin):
    """Control-plane plugin for the runtime-neutral cluster network (BEP-1055)."""

    _etcd: AsyncEtcd | None
    _subnet_allocator: SubnetAllocator
    _vni_allocator: VNIAllocator
    _forced_backend: NetworkBackendKind | None

    def __init__(self, plugin_config: Mapping[str, Any], local_config: Mapping[str, Any]) -> None:
        super().__init__(plugin_config, local_config)
        self._etcd = None
        self._forced_backend = None

    async def init(self, context: Any = None) -> None:
        # Build a dedicated AsyncEtcd from the manager's etcd config (same pattern as
        # OverlayNetworkPlugin constructing its own Docker client). local_config is the
        # by-alias dump of ManagerUnifiedConfig, whose `etcd` section round-trips through
        # EtcdConfig. The operator's forced_backend is passed per-call via create_network
        # options by the launcher (which holds the typed config), so it is not parsed here.
        etcd_config = EtcdConfig.model_validate(self.local_config["etcd"]).to_dataclass()
        self._etcd = AsyncEtcd.create_from_config(etcd_config)
        await self._etcd.open()
        self._subnet_allocator = SubnetAllocator(self._etcd)
        self._vni_allocator = VNIAllocator(self._etcd)

    async def cleanup(self) -> None:
        if self._etcd is not None:
            await self._etcd.close()
            self._etcd = None

    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        return await super().update_plugin_config(plugin_config)

    def _require_etcd(self) -> AsyncEtcd:
        if self._etcd is None:
            raise RuntimeError("CNINetworkPlugin is not initialized (call init() first)")
        return self._etcd

    async def create_network(
        self, *, identifier: str | None = None, options: dict[str, Any] | None = None
    ) -> NetworkInfo:
        etcd = self._require_etcd()
        session_id = identifier or str(uuid.uuid4())
        options = options or {}
        member_agents = list(options.get("member_agents", []))
        forced_raw = options.get("forced_backend")
        forced_backend = NetworkBackendKind(forced_raw) if forced_raw else None

        await self._require_members_cni_capable(member_agents)
        backend = await self._select_backend(member_agents, forced_backend)
        subnet = await self._subnet_allocator.acquire(session_id)
        vni = (
            await self._vni_allocator.acquire(session_id)
            if backend is NetworkBackendKind.VXLAN
            else None
        )
        mtu = int(self.plugin_config.get("mtu") or _DEFAULT_MTU)

        meta: dict[str, Any] = {
            "subnet": subnet,
            "vni": vni,
            "backend": str(backend),
            "mtu": mtu,
        }
        await etcd.put(
            _session_meta_key(session_id), json.dumps(meta), scope=ConfigScopes.GLOBAL
        )
        return NetworkInfo(network_id=session_id, options=meta)

    async def destroy_network(self, network_id: str) -> None:
        etcd = self._require_etcd()
        raw = await etcd.get(_session_meta_key(network_id), scope=ConfigScopes.GLOBAL)
        if raw is not None:
            meta = json.loads(raw)
            if subnet := meta.get("subnet"):
                await self._subnet_allocator.release(subnet)
            if (vni := meta.get("vni")) is not None:
                await self._vni_allocator.release(int(vni))
        await etcd.delete_prefix(f"network/session/{network_id}", scope=ConfigScopes.GLOBAL)

    async def _require_members_cni_capable(self, member_agents: list[str]) -> None:
        """Enforce the deployment invariant that all member agents can serve the 'cni'
        network driver (their backend must be one of CNI_COMPATIBLE_BACKENDS).

        Agents publish their backend under network/agent/{id}/backend at startup. We reject
        only on a *known* incompatible backend (e.g. a docker/overlay agent under the 'cni'
        driver, which would break the multi-node overlay); an unpublished backend is treated
        as unknown-but-allowed so the guard stays safe before the publish path is wired.
        """
        etcd = self._require_etcd()
        for agent_id in member_agents:
            backend = await etcd.get(
                f"network/agent/{agent_id}/backend", scope=ConfigScopes.GLOBAL
            )
            if backend is not None and backend not in _CNI_COMPATIBLE_BACKENDS:
                raise NetworkBackendMismatch(
                    f"agent '{agent_id}' runs the '{backend}' backend, which cannot serve the "
                    "'cni' cluster network driver. Multi-node sessions require a uniform "
                    "network fabric — pair the containerd backend with default_driver='cni' "
                    "(or the docker backend with 'overlay')."
                )

    async def _select_backend(
        self, member_agents: list[str], forced_backend: NetworkBackendKind | None
    ) -> NetworkBackendKind:
        """Operator override wins; otherwise host-gw only if every member advertises
        native-routing capability, else the portable vxlan default."""
        if forced_backend is not None:
            return forced_backend
        if not member_agents:
            return NetworkBackendKind.VXLAN
        etcd = self._require_etcd()
        for agent_id in member_agents:
            raw = await etcd.get(f"network/agent/{agent_id}/caps", scope=ConfigScopes.GLOBAL)
            if raw is None:
                return NetworkBackendKind.VXLAN
            caps = json.loads(raw)
            if not caps.get("native_routing_ok", False):
                return NetworkBackendKind.VXLAN
        return NetworkBackendKind.HOST_GW
