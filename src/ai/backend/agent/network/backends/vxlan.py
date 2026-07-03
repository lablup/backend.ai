"""VXLAN cluster-network backend (BEP-1055).

Portable default data plane: per-session VXLAN VNI + bridge, with unicast head-end
replication (FDB) driven by the SessionNetworkCoordinator's etcd membership watch.

The side-effecting ``ip``/``bridge`` invocations are isolated behind an injectable
runner; the command builders and CNI-config assembly are pure and unit-tested.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.network.caps import probe_caps
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


# --- pure CNI config assembly ---


def overlay_cni_config(meta: SessionNetMeta) -> dict[str, Any]:
    """CNI 'bridge' config attaching the container to this session's overlay bridge,
    with host-local IPAM confined to the session subnet."""
    assert meta.vni is not None
    return {
        "cniVersion": "1.0.0",
        "name": f"bai-overlay-{meta.session_id}",
        "type": "bridge",
        "bridge": bridge_dev(meta.vni),
        "isGateway": False,
        "ipMasq": False,
        "mtu": meta.mtu,
        "ipam": {
            "type": "host-local",
            "subnet": meta.subnet,
        },
    }


def local_bridge_dev(vni: int) -> str:
    return f"bailo{vni}"


def local_cni_config(session_id: str, *, bridge: str, subnet: str) -> dict[str, Any]:
    """CNI 'bridge' config for the host-local interface: agent<->container control
    channel plus egress NAT, carrying the default route.

    Per BEP-1055 Decision Log (2026-07-03): the LOCAL bridge is **per session**, on a
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
    _local_subnets: dict[str, str]

    def __init__(
        self,
        plugin_config: Any,
        local_config: Any,
        *,
        uplink: str = "eth0",
        runner: Runner | None = None,
        local_pool_prefix: str = "172.30",
    ) -> None:
        super().__init__(plugin_config, local_config)
        self._uplink = uplink
        self._runner = runner or _run_command
        self._local_pool_prefix = local_pool_prefix
        self._sessions = {}
        self._local_subnets = {}

    def _alloc_local_subnet(self, session_id: str) -> str:
        """Assign a node-local /24 for the session's LOCAL/egress bridge (idempotent).

        Node-local (behind NAT, never stretched across nodes), so it needs no cross-node
        coordination and cannot collide with another node's LOCAL subnet. TODO: use a
        larger pool / smaller blocks if >256 concurrent sessions per node are expected.
        """
        if (existing := self._local_subnets.get(session_id)) is not None:
            return existing
        used = set(self._local_subnets.values())
        for i in range(256):
            candidate = f"{self._local_pool_prefix}.{i}.0/24"
            if candidate not in used:
                self._local_subnets[session_id] = candidate
                return candidate
        raise RuntimeError("node-local LOCAL subnet pool exhausted (>256 sessions/node)")

    async def init(self, context: Any = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def update_plugin_config(self, plugin_config: Any) -> None:
        self.plugin_config = plugin_config

    async def probe_caps(self) -> AgentNetworkCaps:
        return await probe_caps(self._uplink)

    async def setup_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        if meta.backend is not NetworkBackendKind.VXLAN or meta.vni is None:
            raise ValueError(f"VxlanNetworkPlugin requires a vxlan meta with a VNI: {meta}")
        vni = meta.vni
        await self._runner(vxlan_link_add_args(vni, self._uplink))
        await self._runner(bridge_link_add_args(vni))
        await self._runner(set_master_args(vni))
        await self._runner(link_up_args(vxlan_dev(vni)))
        await self._runner(link_up_args(bridge_dev(vni)))
        self._sessions[meta.session_id] = meta

    async def teardown_session_network(self, session_id: str) -> None:
        meta = self._sessions.pop(session_id, None)
        self._local_subnets.pop(session_id, None)
        if meta is None or meta.vni is None:
            return
        # delete the overlay bridge/vxlan and the per-session LOCAL bridge; ignore missing
        devs = [bridge_dev(meta.vni), vxlan_dev(meta.vni), local_bridge_dev(meta.vni)]
        for dev in devs:
            try:
                await self._runner(link_del_args(dev))
            except RuntimeError:
                log.debug("link {} already gone during teardown of {}", dev, session_id)

    async def add_peer(self, session_id: str, peer: Member) -> None:
        meta = self._sessions.get(session_id)
        if meta is None or meta.vni is None or peer.vtep_ip is None:
            return
        await self._runner(fdb_append_args(meta.vni, peer.vtep_ip))

    async def del_peer(self, session_id: str, peer: Member) -> None:
        meta = self._sessions.get(session_id)
        if meta is None or meta.vni is None or peer.vtep_ip is None:
            return
        try:
            await self._runner(fdb_del_args(meta.vni, peer.vtep_ip))
        except RuntimeError:
            log.debug("fdb entry for {} already gone in session {}", peer.vtep_ip, session_id)

    async def attach_endpoint(
        self,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
        *,
        meta: SessionNetMeta,
    ) -> EndpointPlan:
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
                        subnet=self._alloc_local_subnet(meta.session_id),
                    ),
                ),
                NetworkAttachSpec(
                    kind=AttachKind.CNI,
                    interface_name=OVERLAY_IFNAME,
                    role=NetworkRole.OVERLAY,
                    cni_config=overlay_cni_config(meta),
                ),
            ]
        )

    async def detach_endpoint(self, kernel: AbstractKernel) -> None:
        pass
