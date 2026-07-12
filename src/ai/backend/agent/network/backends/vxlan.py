"""VXLAN cluster-network backend (BEP-1062).

Portable default data plane: per-session VXLAN VNI + bridge, with unicast head-end
replication (FDB) driven by the SessionNetworkCoordinator's etcd membership watch.

The side-effecting ``ip``/``bridge`` invocations are isolated behind an injectable
runner; the command builders and CNI-config assembly are pure and unit-tested.
"""

from __future__ import annotations

import asyncio
import ipaddress
import logging
from collections.abc import Awaitable, Callable, Sequence
from typing import Any, override

from ai.backend.agent.errors.network import OverlayAddressNotAssigned
from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.network.caps import probe_caps
from ai.backend.agent.network.local_subnet import LocalSubnetAllocator, get_local_subnet_allocator
from ai.backend.agent.plugin.network_v2 import AbstractNetworkAgentPluginV2
from ai.backend.common.network.types import (
    AgentNetworkCaps,
    AttachKind,
    EndpointPlan,
    Member,
    NetworkAttachSpec,
    NetworkBackendKind,
    NetworkRole,
    SessionNetMeta,
    mac_for_ip,
)
from ai.backend.common.types import ClusterInfo, KernelCreationConfig
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

VXLAN_DSTPORT = 4789
OVERLAY_IFNAME = "baimulti0"
_BROADCAST_MAC = "00:00:00:00:00:00"

Runner = Callable[[Sequence[str]], Awaitable[None]]


# --- naming (kept within the 15-char interface name limit) ---


def vxlan_dev(vni: int) -> str:
    return f"baivx{vni}"


def bridge_dev(vni: int) -> str:
    return f"baibr{vni}"


# --- pure command builders ---


def vxlan_link_add_args(vni: int, uplink: str, *, dstport: int = VXLAN_DSTPORT) -> list[str]:
    return [
        "ip", "link", "add", vxlan_dev(vni),
        "type", "vxlan",
        "id", str(vni),
        "dev", uplink,
        "dstport", str(dstport),
        "nolearning",
    ]  # fmt: skip


def bridge_link_add_args(vni: int) -> list[str]:
    return ["ip", "link", "add", bridge_dev(vni), "type", "bridge"]


def set_master_args(vni: int) -> list[str]:
    return ["ip", "link", "set", vxlan_dev(vni), "master", bridge_dev(vni)]


def link_up_args(dev: str) -> list[str]:
    return ["ip", "link", "set", dev, "up"]


def link_del_args(dev: str) -> list[str]:
    return ["ip", "link", "del", dev]


def fdb_append_args(vni: int, dst: str, *, mac: str = _BROADCAST_MAC) -> list[str]:
    return ["bridge", "fdb", "append", mac, "dev", vxlan_dev(vni), "dst", dst]


def fdb_del_args(vni: int, dst: str, *, mac: str = _BROADCAST_MAC) -> list[str]:
    return ["bridge", "fdb", "del", mac, "dev", vxlan_dev(vni), "dst", dst]


# --- proactive endpoint programming (unicast FDB + ARP; replaces BUM flooding) ---


def fdb_replace_args(vni: int, mac: str, dst: str) -> list[str]:
    """Program the exact unicast MAC→VTEP forwarding entry for a known remote endpoint."""
    return ["bridge", "fdb", "replace", mac, "dev", vxlan_dev(vni), "dst", dst]


def neigh_replace_args(vni: int, ip: str, mac: str) -> list[str]:
    """Program a permanent ARP entry (IP→MAC) on the overlay bridge — ARP suppression, so
    a known remote endpoint never triggers a broadcast ARP over the tunnel."""
    return ["ip", "neigh", "replace", ip, "lladdr", mac, "dev", bridge_dev(vni), "nud", "permanent"]


def neigh_del_args(vni: int, ip: str) -> list[str]:
    return ["ip", "neigh", "del", ip, "dev", bridge_dev(vni)]


# --- pure CNI config assembly ---


def _overlay_ipam(meta: SessionNetMeta, ip: str) -> dict[str, Any]:
    """Static IPAM at the manager-assigned endpoint IP.

    The overlay subnet is stretched across every node in the session, so the address MUST come
    from the manager's central ``endpoints/`` table — which hands each endpoint a disjoint IP by
    construction. A per-node host-local pick would give every node the same first address and
    collide across the tunnel. There is no local fallback: this backend is multi-node only (the
    single-node path uses the bridge backend), and the manager assigns an endpoint IP to every
    kernel that has an agent, so a missing IP here is a control-plane bug, not a fallback case —
    the caller raises rather than silently attach a colliding address."""
    prefixlen = ipaddress.ip_network(meta.subnet).prefixlen
    return {"type": "static", "addresses": [{"address": f"{ip}/{prefixlen}"}]}


def overlay_cni_config(meta: SessionNetMeta, ip: str | None = None) -> dict[str, Any]:
    """CNI 'bridge' config attaching the container to this session's overlay bridge.

    ``ip`` is the manager-assigned overlay address and is required: without it the container
    cannot be given a cluster-unique address on the stretched overlay (see _overlay_ipam)."""
    if meta.vni is None:
        raise ValueError(f"overlay_cni_config requires a vxlan meta with a VNI: {meta}")
    if ip is None:
        raise OverlayAddressNotAssigned(
            f"no manager-assigned overlay IP for session {meta.session_id}; "
            "cannot attach to the stretched overlay without a cluster-unique address"
        )
    config: dict[str, Any] = {
        "cniVersion": "1.0.0",
        "name": f"bai-overlay-{meta.session_id}",
        "type": "bridge",
        "bridge": bridge_dev(meta.vni),
        "isGateway": False,
        "ipMasq": False,
        "mtu": meta.mtu,
        "ipam": _overlay_ipam(meta, ip),
    }
    # Pin the overlay NIC's MAC to the same deterministic address the manager programs into
    # every peer's FDB/ARP (mac_for_ip). Without this the veth gets a random MAC, so a peer's
    # unicast frame (dst=02:42:<ip>) arriving over the tunnel would not match the container
    # NIC and be dropped — breaking cross-node overlay traffic. Only meaningful with a static
    # (manager-assigned) IP; host-local fallback has no pre-programmed ARP to match.
    if ip is not None:
        config["mac"] = mac_for_ip(ip)
    return config


def local_bridge_dev(vni: int) -> str:
    return f"bailo{vni}"


def local_cni_config(session_id: str, *, bridge: str, subnet: str) -> dict[str, Any]:
    """CNI 'bridge' config for the host-local interface: agent<->container control
    channel plus egress NAT, carrying the default route.

    Per BEP-1062 Decision Log (2026-07-03): the LOCAL bridge is **per session**, on a
    **node-local** NAT subnet (not the stretched overlay subnet). Cross-session isolation
    comes from separate bridges (verified §8), not ICC-off firewall rules (the stock CNI
    bridge does not implement ICC-off — §9). A node-local subnet also avoids the
    stretched-L2 gateway conflict that folding egress into the overlay bridge would cause
    (option C, rejected in §9)."""
    return {
        "cniVersion": "1.0.0",
        "name": f"bai-local-{session_id}",
        "type": "bridge",
        "bridge": bridge,
        "isGateway": True,
        "isDefaultGateway": True,
        "ipMasq": True,
        "hairpinMode": False,
        "ipam": {
            "type": "host-local",
            "subnet": subnet,
        },
    }


async def _run_command(argv: Sequence[str]) -> None:
    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed (rc={proc.returncode}): {' '.join(argv)}: "
            f"{stderr.decode(errors='replace').strip()}"
        )


class VxlanNetworkPlugin(AbstractNetworkAgentPluginV2[AbstractKernel]):
    """VXLAN data-plane backend."""

    _runner: Runner
    _uplink: str
    _local_pool_prefix: str
    _sessions: dict[str, SessionNetMeta]
    _local_subnets: LocalSubnetAllocator

    def __init__(
        self,
        plugin_config: Any,
        local_config: Any,
        *,
        uplink: str = "eth0",
        runner: Runner | None = None,
        local_pool_prefix: str = "172.30",
        local_subnets: LocalSubnetAllocator | None = None,
    ) -> None:
        super().__init__(plugin_config, local_config)
        self._uplink = uplink
        self._runner = runner or _run_command
        self._local_pool_prefix = local_pool_prefix
        self._sessions = {}
        # Defaults to the store's single process-wide owner, which is also what the bridge backend
        # resolves: both carve their LOCAL /24 out of the same node-local pool, so one owner keeps
        # their indices from colliding on a subnet.
        self._local_subnets = local_subnets or get_local_subnet_allocator()

    async def _local_subnet(self, session_id: str) -> str:
        """The node-local /24 for the session's LOCAL/egress bridge (idempotent, durable).

        Node-local (behind NAT, never stretched across nodes), so it needs no cross-node
        coordination and cannot collide with another node's LOCAL subnet. TODO: use a
        larger pool / smaller blocks if >256 concurrent sessions per node are expected.
        """
        index = await self._local_subnets.allocate(session_id)
        return f"{self._local_pool_prefix}.{index}.0/24"

    @override
    async def init(self, context: Any = None) -> None:
        pass

    @override
    async def cleanup(self) -> None:
        pass

    @override
    async def update_plugin_config(self, plugin_config: Any) -> None:
        self.plugin_config = plugin_config

    @override
    async def probe_caps(self) -> AgentNetworkCaps:
        return await probe_caps(self._uplink)

    async def _delete_link_quiet(self, dev: str) -> None:
        """Delete a link if present; ignore 'does not exist' failures."""
        try:
            await self._runner(link_del_args(dev))
        except RuntimeError:
            pass

    @override
    async def setup_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        if meta.backend is not NetworkBackendKind.VXLAN or meta.vni is None:
            raise ValueError(f"VxlanNetworkPlugin requires a vxlan meta with a VNI: {meta}")
        vni = meta.vni
        # Leftover-safe: a stale device from a crashed/uncleaned prior session would make
        # `ip link add` fail with 'File exists' (and could carry stale FDB/IP). Delete any
        # pre-existing devices of these names first so setup always yields a fresh device.
        # The LOCAL bridge (bailo{vni}) is created later by CNI, but a leftover one keyed by
        # the (reused) vni retains a prior session's gateway IP and makes CNI ADD fail with
        # "already has an IP address different from ..." — so clear it here too.
        await self._delete_link_quiet(bridge_dev(vni))
        await self._delete_link_quiet(vxlan_dev(vni))
        await self._delete_link_quiet(local_bridge_dev(vni))
        await self._runner(vxlan_link_add_args(vni, self._uplink))
        await self._runner(bridge_link_add_args(vni))
        await self._runner(set_master_args(vni))
        await self._runner(link_up_args(vxlan_dev(vni)))
        await self._runner(link_up_args(bridge_dev(vni)))
        self._sessions[meta.session_id] = meta

    @override
    async def adopt_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        if meta.backend is not NetworkBackendKind.VXLAN or meta.vni is None:
            raise ValueError(f"VxlanNetworkPlugin requires a vxlan meta with a VNI: {meta}")
        # Devices are already up and carrying traffic; only the bookkeeping add_peer/add_endpoint
        # read is missing. The LOCAL subnet index is re-claimed from the journal by attach_endpoint,
        # which is idempotent per session.
        self._sessions[meta.session_id] = meta

    @override
    async def teardown_session_network(self, session_id: str) -> None:
        meta = self._sessions.pop(session_id, None)
        await self._local_subnets.release(session_id)
        if meta is None or meta.vni is None:
            return
        # delete the overlay bridge/vxlan and the per-session LOCAL bridge; ignore missing
        devs = [bridge_dev(meta.vni), vxlan_dev(meta.vni), local_bridge_dev(meta.vni)]
        for dev in devs:
            try:
                await self._runner(link_del_args(dev))
            except RuntimeError:
                log.debug("link {} already gone during teardown of {}", dev, session_id)

    @override
    async def add_peer(self, session_id: str, peer: Member) -> None:
        meta = self._sessions.get(session_id)
        if meta is None or meta.vni is None or peer.vtep_ip is None:
            return
        await self._runner(fdb_append_args(meta.vni, peer.vtep_ip))

    @override
    async def del_peer(self, session_id: str, peer: Member) -> None:
        meta = self._sessions.get(session_id)
        if meta is None or meta.vni is None or peer.vtep_ip is None:
            return
        try:
            await self._runner(fdb_del_args(meta.vni, peer.vtep_ip))
        except RuntimeError:
            log.debug("fdb entry for {} already gone in session {}", peer.vtep_ip, session_id)

    @override
    async def add_endpoint(self, session_id: str, *, ip: str, mac: str, vtep_ip: str) -> None:
        """Proactively program a remote endpoint: unicast MAC→VTEP FDB + permanent ARP.

        Idempotent (``replace``). Known unicast then never floods over the tunnel."""
        meta = self._sessions.get(session_id)
        if meta is None or meta.vni is None:
            return
        await self._runner(fdb_replace_args(meta.vni, mac, vtep_ip))
        await self._runner(neigh_replace_args(meta.vni, ip, mac))

    @override
    async def del_endpoint(self, session_id: str, *, ip: str, mac: str, vtep_ip: str) -> None:
        meta = self._sessions.get(session_id)
        if meta is None or meta.vni is None:
            return
        for argv in (fdb_del_args(meta.vni, vtep_ip, mac=mac), neigh_del_args(meta.vni, ip)):
            try:
                await self._runner(argv)
            except RuntimeError:
                log.debug("endpoint entry {} already gone in session {}", ip, session_id)

    @override
    async def attach_endpoint(
        self,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
        *,
        meta: SessionNetMeta,
    ) -> EndpointPlan:
        # Static IP at the manager-assigned overlay address (disjoint across nodes); falls
        # back to host-local only if the manager did not assign one (single-node / legacy).
        overlay_ip = kernel_config.get("cluster_network_ip")
        return EndpointPlan(
            attachments=[
                NetworkAttachSpec(
                    kind=AttachKind.CNI,
                    interface_name="eth0",
                    role=NetworkRole.LOCAL,
                    is_default_route=True,
                    cni_config=local_cni_config(
                        meta.session_id,
                        bridge=local_bridge_dev(meta.vni) if meta.vni is not None else "bailo0",
                        subnet=await self._local_subnet(meta.session_id),
                    ),
                ),
                NetworkAttachSpec(
                    kind=AttachKind.CNI,
                    interface_name=OVERLAY_IFNAME,
                    role=NetworkRole.OVERLAY,
                    cni_config=overlay_cni_config(meta, overlay_ip),
                ),
            ]
        )

    @override
    async def detach_endpoint(self, kernel: AbstractKernel) -> None:
        pass
