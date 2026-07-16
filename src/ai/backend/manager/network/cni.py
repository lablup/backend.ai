"""Runtime-neutral cluster-network manager plugin (CNI/etcd control plane).

Replaces the Swarm-based `OverlayNetworkPlugin` for containerd and other host-native
runtimes. This plugin owns the *control plane*: it allocates a per-session subnet
(and a VNI for the vxlan backend), selects the data-plane backend (the portable vxlan
overlay unless the operator pins one), and writes the session network descriptor to etcd.
The data plane itself is realized by the agent-side v2 plugins (see BEP-1062/agent-plugin-v2.md).
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
    agent_vtep_key,
    member_key,
    session_meta_key,
    session_prefix,
)
from ai.backend.common.network.types import (
    Member,
    NetworkBackendKind,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.network import ForcedBackendUnsupported
from ai.backend.manager.network.ipam import (
    DEFAULT_BLOCK_PREFIXLEN,
    DEFAULT_IPAM_POOL,
    EndpointAllocator,
    SubnetAllocator,
    VNIAllocator,
)
from ai.backend.manager.network.pairing import require_members_can_serve_driver
from ai.backend.manager.plugin.network import AbstractNetworkManagerPlugin, NetworkInfo

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# The underlay (uplink) MTU. The overlay MTU handed to every kernel is this minus the VXLAN
# encapsulation overhead, so a full-size inner frame still fits the tunnel — the same 1450 default
# Docker Swarm's overlay uses. Setting the container NIC to the underlay 1500 (as this used to) lets
# a 1500-byte frame reach a 1450-MTU VXLAN port, where it is silently dropped with no ICMP (L2
# bridging), i.e. a PMTUD black hole: handshakes pass, bulk transfers (NCCL/mpirun) hang.
_DEFAULT_UNDERLAY_MTU = 1500
_VXLAN_OVERHEAD = 50  # IPv4 VXLAN: 20 IP + 8 UDP + 8 VXLAN + 14 inner Ethernet


class CNINetworkPlugin(AbstractNetworkManagerPlugin):
    """Control-plane plugin for the runtime-neutral cluster network (BEP-1062)."""

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
        # The overlay pool is the operator's: it is stretched across the session's nodes, so it
        # must not collide with anything those nodes already route.
        inter_container = (self.local_config.get("network") or {}).get("inter-container") or {}
        self._subnet_allocator = SubnetAllocator(
            self._etcd,
            pool=str(inter_container.get("ipam-pool") or DEFAULT_IPAM_POOL),
            block_prefixlen=int(inter_container.get("ipam-block-size") or DEFAULT_BLOCK_PREFIXLEN),
        )
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
        # its overlay IP centrally (BEP-1062) so per-node IPs are disjoint.
        endpoints = list(options.get("endpoints", []))
        # Optional explicit subnet (like `docker network create --subnet`): when set, the
        # allocator claims exactly this block and fails on overlap instead of auto-sizing.
        requested_subnet = options.get("subnet")

        await self._require_members_cni_capable(member_agents)
        backend = self._select_backend(forced_backend)
        # Size the session subnet to hold every endpoint (removes the fixed-/24 254 cap).
        # A failure to acquire the subnet claims nothing, so it needs no rollback; every
        # subsequent claim (VNI, endpoint IPs, meta/member keys) is undone on any failure so a
        # partial create never leaks a block/VNI or lets a retry consume fresh ones.
        subnet = await self._subnet_allocator.acquire(
            session_id,
            host_count=max(len(endpoints), 1),
            subnet=str(requested_subnet) if requested_subnet else None,
        )
        vni: int | None = None
        try:
            if backend is NetworkBackendKind.VXLAN:
                vni = await self._vni_allocator.acquire(session_id)
            # `mtu` in plugin_config is the UNDERLAY MTU; the overlay MTU (what the kernel's NIC
            # gets) is that minus the tunnel overhead. Only the VXLAN backend encapsulates, so only
            # it pays the overhead; a non-encapsulating backend would keep the underlay MTU.
            underlay_mtu = int(self.plugin_config.get("mtu") or _DEFAULT_UNDERLAY_MTU)
            mtu = (
                underlay_mtu - _VXLAN_OVERHEAD
                if backend is NetworkBackendKind.VXLAN
                else underlay_mtu
            )

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
        """Refuse a member agent whose backend cannot serve the 'cni' driver.

        The symmetric check for 'overlay' lives in OverlayNetworkPlugin; both call the same guard
        so the two drivers cannot drift apart on what they accept.
        """
        await require_members_can_serve_driver(self._require_etcd(), "cni", member_agents)

    def _select_backend(self, forced_backend: NetworkBackendKind | None) -> NetworkBackendKind:
        """The operator's forced backend wins; otherwise every multi-node cluster session uses
        the portable vxlan overlay.

        This control plane only ever provisions multi-node sessions — single-node sessions never
        reach it (the agent selects their node-local bridge backend directly). The bridge backend
        is node-local and ignores the manager's central IPAM, so pinning it here would provision a
        session whose /etc/hosts names overlay IPs no container holds. Reject it rather than hand
        back unusable networking; 'vxlan' (or an unset override) is the only valid choice here.
        """
        if forced_backend is NetworkBackendKind.BRIDGE:
            raise ForcedBackendUnsupported(
                "the 'bridge' data-plane backend is node-local (single-node) and cannot serve a"
                " multi-node cluster session; use 'vxlan' (the default) or leave forced-backend unset."
            )
        return forced_backend if forced_backend is not None else NetworkBackendKind.VXLAN
