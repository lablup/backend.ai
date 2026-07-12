"""Runtime-neutral cluster-network manager plugin (CNI/etcd control plane).

Replaces the Swarm-based `OverlayNetworkPlugin` for containerd and other host-native
runtimes. This plugin owns the *control plane*: it allocates a per-session subnet
(and a VNI for the vxlan backend), selects the data-plane backend from agent
capabilities, and writes the session network descriptor to etcd. The data plane
itself is realized by the agent-side v2 plugins (see BEP-1058/agent-plugin-v2.md).
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Mapping
from typing import Any, override

from ai.backend.common.configs.etcd import EtcdConfig
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.network.keys import (
    agent_backend_key,
    agent_caps_key,
    agent_vtep_key,
    member_key,
    session_meta_key,
    session_prefix,
)
from ai.backend.common.network.types import (
    IMPLEMENTED_NETWORK_BACKENDS,
    Member,
    NetworkBackendKind,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.network import (
    NetworkBackendMismatch,
    UnsupportedNetworkBackend,
)
from ai.backend.manager.network.ipam import (
    EndpointAllocator,
    SubnetAllocator,
    VNIAllocator,
)
from ai.backend.manager.plugin.network import AbstractNetworkManagerPlugin, NetworkInfo

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_MTU = 1500

# Agent backends whose network stack can serve the BEP-1058 'cni' driver.
_CNI_COMPATIBLE_BACKENDS = frozenset({"containerd"})


class CNINetworkPlugin(AbstractNetworkManagerPlugin):
    """Control-plane plugin for the runtime-neutral cluster network (BEP-1058)."""

    _etcd: AsyncEtcd | None
    _subnet_allocator: SubnetAllocator
    _vni_allocator: VNIAllocator
    _endpoint_allocator: EndpointAllocator
    _forced_backend: NetworkBackendKind | None

    def __init__(self, plugin_config: Mapping[str, Any], local_config: Mapping[str, Any]) -> None:
        super().__init__(plugin_config, local_config)
        self._etcd = None
        self._forced_backend = None

    @override
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
        self._endpoint_allocator = EndpointAllocator(self._etcd)

    @override
    async def cleanup(self) -> None:
        if self._etcd is not None:
            await self._etcd.close()
            self._etcd = None

    @override
    async def update_plugin_config(self, plugin_config: Mapping[str, Any]) -> None:
        return await super().update_plugin_config(plugin_config)

    def _require_etcd(self) -> AsyncEtcd:
        if self._etcd is None:
            raise RuntimeError("CNINetworkPlugin is not initialized (call init() first)")
        return self._etcd

    @override
    async def create_network(
        self, *, identifier: str | None = None, options: dict[str, Any] | None = None
    ) -> NetworkInfo:
        etcd = self._require_etcd()
        session_id = identifier or str(uuid.uuid4())
        options = options or {}
        member_agents = list(options.get("member_agents", []))
        forced_raw = options.get("forced_backend")
        forced_backend = NetworkBackendKind(forced_raw) if forced_raw else None
        # Each endpoint = one container: {"container_id", "agent_id"}. The manager assigns
        # its overlay IP centrally (BEP-1058) so per-node IPs are disjoint.
        endpoints = list(options.get("endpoints", []))

        await self._require_members_cni_capable(member_agents)
        backend = await self._select_backend(member_agents, forced_backend)
        # Size the session subnet to hold every endpoint (removes the fixed-/24 254 cap).
        # A failure to acquire the subnet claims nothing, so it needs no rollback; every
        # subsequent claim (VNI, endpoint IPs, meta/member keys) is undone on any failure so a
        # partial create never leaks a block/VNI or lets a retry consume fresh ones.
        subnet = await self._subnet_allocator.acquire(session_id, host_count=max(len(endpoints), 1))
        vni: int | None = None
        try:
            if backend is NetworkBackendKind.VXLAN:
                vni = await self._vni_allocator.acquire(session_id)
            mtu = int(self.plugin_config.get("mtu") or _DEFAULT_MTU)

            meta: dict[str, Any] = {
                "subnet": subnet,
                "vni": vni,
                "backend": str(backend),
                "mtu": mtu,
            }
            await etcd.put(
                session_meta_key(session_id), json.dumps(meta), scope=ConfigScopes.GLOBAL
            )
            # Assign each endpoint a disjoint overlay IP and record it under endpoints/ (the
            # coordinator programs FDB/ARP from there). Returned map is threaded per-kernel by
            # the launcher into KernelCreationConfig["cluster_network_ip"].
            endpoint_ips: dict[str, str] = {}
            for endpoint in endpoints:
                container_id = str(endpoint["container_id"])
                ip, _mac = await self._endpoint_allocator.assign(
                    session_id, container_id, subnet, agent_id=str(endpoint["agent_id"])
                )
                endpoint_ips[container_id] = ip
            # Pre-seed the membership table so each agent's reconcile-at-start finds every
            # peer's VTEP already present, instead of racing the etcd watch that delivers a
            # peer's self-published member (which can lag a fast worker's cross-node startup).
            # VXLAN only: the member's tunnel endpoint is the agent's published VTEP. Agents
            # whose VTEP is not yet published are skipped — they fall back to self-publish +
            # watch convergence (no regression).
            if backend is NetworkBackendKind.VXLAN:
                await self._preseed_members(session_id, member_agents)
            return NetworkInfo(
                network_id=session_id, options={**meta, "endpoint_ips": endpoint_ips}
            )
        except Exception:
            await self._rollback_create(session_id, subnet, vni)
            raise

    async def _rollback_create(self, session_id: str, subnet: str, vni: int | None) -> None:
        """Undo a partially-created session network: release the VNI and subnet blocks and
        delete every key written under the session (meta / endpoints / ipam / members). Each
        step is best-effort and idempotent (deletes of absent keys are no-ops) so cleanup runs
        to completion regardless of how far create_network got before failing."""
        etcd = self._require_etcd()
        try:
            await etcd.delete_prefix(
                session_prefix(session_id).rstrip("/"), scope=ConfigScopes.GLOBAL
            )
        except Exception:
            log.exception("rollback: failed to delete session keys for {}", session_id)
        if vni is not None:
            try:
                await self._vni_allocator.release(vni)
            except Exception:
                log.exception("rollback: failed to release VNI {} for {}", vni, session_id)
        try:
            await self._subnet_allocator.release(subnet)
        except Exception:
            log.exception("rollback: failed to release subnet {} for {}", subnet, session_id)

    async def _preseed_members(self, session_id: str, member_agents: list[str]) -> None:
        etcd = self._require_etcd()
        for agent_id in member_agents:
            vtep = await etcd.get(agent_vtep_key(agent_id), scope=ConfigScopes.GLOBAL)
            if not vtep:
                continue
            member = Member(agent_id=agent_id, host_ip=vtep, vtep_ip=vtep)
            await etcd.put(
                member_key(session_id, agent_id),
                json.dumps(member.to_etcd_payload()),
                scope=ConfigScopes.GLOBAL,
            )

    @override
    async def destroy_network(self, network_id: str) -> None:
        etcd = self._require_etcd()
        raw = await etcd.get(session_meta_key(network_id), scope=ConfigScopes.GLOBAL)
        if raw is not None:
            meta = json.loads(raw)
            if subnet := meta.get("subnet"):
                await self._subnet_allocator.release(subnet)
            if (vni := meta.get("vni")) is not None:
                await self._vni_allocator.release(int(vni))
        await etcd.delete_prefix(session_prefix(network_id).rstrip("/"), scope=ConfigScopes.GLOBAL)

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
            backend = await etcd.get(agent_backend_key(agent_id), scope=ConfigScopes.GLOBAL)
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
        native-routing capability, else the portable vxlan default. The chosen backend is
        validated against the set that actually has an agent-side implementation, so an
        unimplemented one (host-gw / wireguard) is refused here rather than crashing the agent."""
        backend = await self._resolve_backend(member_agents, forced_backend)
        if backend not in IMPLEMENTED_NETWORK_BACKENDS:
            raise UnsupportedNetworkBackend(
                f"cluster-network backend '{backend}' is declared but not implemented "
                f"(implemented: {sorted(b.value for b in IMPLEMENTED_NETWORK_BACKENDS)})"
            )
        return backend

    async def _resolve_backend(
        self, member_agents: list[str], forced_backend: NetworkBackendKind | None
    ) -> NetworkBackendKind:
        if forced_backend is not None:
            return forced_backend
        if not member_agents:
            return NetworkBackendKind.VXLAN
        etcd = self._require_etcd()
        for agent_id in member_agents:
            raw = await etcd.get(agent_caps_key(agent_id), scope=ConfigScopes.GLOBAL)
            if raw is None:
                return NetworkBackendKind.VXLAN
            caps = json.loads(raw)
            if not caps.get("native_routing_ok", False):
                return NetworkBackendKind.VXLAN
        return NetworkBackendKind.HOST_GW
