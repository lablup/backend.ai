"""Node-local bridge cluster-network backend (BEP-1062).

Single-node data plane: a per-session CNI bridge on a node-local NAT subnet, with no
cross-node overlay. It gives a single-node container a host-reachable IP (the host is the
bridge gateway) — the pure-CNI replacement for the former nerdctl-managed bridge, so the
containerd runtime never shells out to nerdctl.

Reuses the vxlan backend's node-local bridge helpers (naming, host-local CNI config); it
implements only the LOCAL attachment and no-ops every overlay concern (peers, FDB, remote
endpoints), since a single node has no peers.
"""

from __future__ import annotations

import logging
from typing import Any, override

from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.network.backends.vxlan import (
    Runner,
    _run_command,
    link_del_args,
    local_bridge_dev,
    local_cni_config,
)
from ai.backend.agent.network.caps import probe_caps
from ai.backend.agent.network.local_subnet import LocalSubnetAllocator, get_local_subnet_allocator
from ai.backend.agent.plugin.network_v2 import AbstractNetworkAgentPluginV2
from ai.backend.common.network.types import (
    AgentNetworkCaps,
    AttachKind,
    EndpointPlan,
    Member,
    NetworkAttachSpec,
    NetworkRole,
    SessionNetMeta,
)
from ai.backend.common.types import ClusterInfo, KernelCreationConfig
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class BridgeNetworkPlugin(AbstractNetworkAgentPluginV2[AbstractKernel]):
    """Node-local per-session bridge (no overlay)."""

    _runner: Runner
    _uplink: str
    _local_pool_prefix: str
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
        # Defaults to the store's single process-wide owner (see the vxlan backend's __init__).
        self._local_subnets = local_subnets or get_local_subnet_allocator()

    async def _index(self, session_id: str) -> int:
        """Claim the session's node-local /24 index (idempotent, durable across restarts)."""
        return await self._local_subnets.allocate(session_id)

    async def _subnet(self, session_id: str) -> str:
        return f"{self._local_pool_prefix}.{await self._index(session_id)}.0/24"

    async def _bridge(self, session_id: str) -> str:
        return local_bridge_dev(await self._index(session_id))

    async def _delete_link_quiet(self, dev: str) -> None:
        try:
            await self._runner(link_del_args(dev))
        except RuntimeError:
            pass

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

    @override
    async def setup_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        # The CNI bridge plugin creates the bridge on attach; only clear a stale device of
        # the same name (a reused subnet index) so it cannot carry a prior gateway IP that
        # would make CNI ADD fail with "already has an IP address different from ...".
        # Safe because the index is claimed from the durable allocator: a freshly assigned
        # index is never one a live session (including one that predates an agent restart)
        # still holds, so this cannot delete a running session's bridge.
        await self._delete_link_quiet(await self._bridge(meta.session_id))

    @override
    async def adopt_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        # The bridge backend keeps no per-session memory: the device name and subnet are both
        # derived from the journalled index, which survives the restart. Re-claim it so the index
        # is not handed to another session, and leave the live bridge alone.
        await self._index(meta.session_id)

    @override
    async def teardown_session_network(self, session_id: str) -> None:
        # lookup, not allocate: an unknown session must not mint an index and then delete
        # the bridge that index names.
        index = await self._local_subnets.lookup(session_id)
        if index is None:
            return
        await self._delete_link_quiet(local_bridge_dev(index))
        await self._local_subnets.release(session_id)

    @override
    async def add_peer(self, session_id: str, peer: Member) -> None:
        pass  # single-node: no peers

    @override
    async def del_peer(self, session_id: str, peer: Member) -> None:
        pass

    @override
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
                        bridge=await self._bridge(meta.session_id),
                        subnet=await self._subnet(meta.session_id),
                    ),
                ),
            ]
        )

    @override
    async def detach_endpoint(self, kernel: AbstractKernel) -> None:
        pass
