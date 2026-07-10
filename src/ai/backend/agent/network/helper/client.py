"""Agent-side client + proxies for the privileged network helper (BEP-1058).

These let the *unprivileged* agent keep its normal composition (SessionNetworkCoordinator
owns etcd membership; the orchestrator drives per-container attach) while every privileged
side effect is delegated to the helper as a semantic verb. The agent sends only
``session_id`` / ``container_id``; it never builds argv, device names, netns paths, or CNI
config — so it holds no CAP_NET_ADMIN / CAP_SYS_ADMIN.

- ``HelperClient`` — one short-lived unix-socket round trip per request.
- ``HelperBackendProxy`` — an ``AbstractNetworkAgentPluginV2`` whose privileged methods
  (setup/teardown) become RPCs; overlay peer/endpoint programming is handled helper-side.
- ``HelperProvisioner`` — the per-container attach/detach path, replacing
  ``ContainerNetworkProvisioner`` when the helper is enabled.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, override

from ai.backend.agent.network.caps import probe_caps
from ai.backend.agent.network.helper.protocol import (
    HelperOp,
    HelperRequest,
    HelperResponse,
)
from ai.backend.agent.plugin.network_v2 import AbstractNetworkAgentPluginV2
from ai.backend.common.network.types import (
    AgentNetworkCaps,
    EndpointPlan,
    Member,
    NetworkRole,
    SessionNetMeta,
)

if TYPE_CHECKING:
    from ai.backend.agent.kernel import AbstractKernel
    from ai.backend.common.types import ClusterInfo, KernelCreationConfig


class HelperClientError(RuntimeError):
    """The helper refused or failed a request. Carries the helper's generic reason."""


class HelperClient:
    _socket_path: str

    def __init__(self, socket_path: str) -> None:
        self._socket_path = socket_path

    async def call(self, req: HelperRequest) -> HelperResponse:
        reader, writer = await asyncio.open_unix_connection(self._socket_path)
        try:
            writer.write(req.encode())
            await writer.drain()
            line = await reader.readline()
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
        resp = HelperResponse.decode(line)
        if not resp.ok:
            raise HelperClientError(resp.error or "helper request failed")
        return resp


def _network_config_from_meta(meta: SessionNetMeta) -> dict[str, Any]:
    return {
        "backend": str(meta.backend),
        "subnet": meta.subnet or None,
        "vni": meta.vni,
        "mtu": meta.mtu,
    }


class HelperBackendProxy(AbstractNetworkAgentPluginV2["AbstractKernel"]):
    """Backend facade the agent's coordinator drives; privileged host ops go to the helper.

    Single-node overlay concerns (peers/endpoints) are no-ops here because the helper owns
    the overlay data plane; they are wired as helper verbs when multi-node lands."""

    _client: HelperClient
    _uplink: str

    def __init__(
        self, plugin_config: Any, local_config: Any, *, client: HelperClient, uplink: str = "eth0"
    ) -> None:
        super().__init__(plugin_config, local_config)
        self._client = client
        self._uplink = uplink

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
        # Non-privileged NIC feature probe stays agent-side.
        return await probe_caps(self._uplink)

    @override
    async def setup_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        await self._client.call(
            HelperRequest(
                op=HelperOp.SETUP_SESSION,
                session_id=meta.session_id,
                network_config=_network_config_from_meta(meta),
            )
        )

    @override
    async def teardown_session_network(self, session_id: str) -> None:
        await self._client.call(HelperRequest(op=HelperOp.TEARDOWN_SESSION, session_id=session_id))

    @override
    async def add_peer(self, session_id: str, peer: Member) -> None:
        if peer.vtep_ip is None:
            return  # non-overlay peer (bridge/host-gw): nothing to program on the overlay
        await self._client.call(
            HelperRequest(op=HelperOp.ADD_PEER, session_id=session_id, vtep_ip=peer.vtep_ip)
        )

    @override
    async def del_peer(self, session_id: str, peer: Member) -> None:
        if peer.vtep_ip is None:
            return
        await self._client.call(
            HelperRequest(op=HelperOp.DEL_PEER, session_id=session_id, vtep_ip=peer.vtep_ip)
        )

    @override
    async def add_endpoint(self, session_id: str, *, ip: str, mac: str, vtep_ip: str) -> None:
        await self._client.call(
            HelperRequest(
                op=HelperOp.ADD_ENDPOINT, session_id=session_id, ip=ip, mac=mac, vtep_ip=vtep_ip
            )
        )

    @override
    async def del_endpoint(self, session_id: str, *, ip: str, mac: str, vtep_ip: str) -> None:
        await self._client.call(
            HelperRequest(
                op=HelperOp.DEL_ENDPOINT, session_id=session_id, ip=ip, mac=mac, vtep_ip=vtep_ip
            )
        )

    @override
    async def attach_endpoint(
        self,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
        *,
        meta: SessionNetMeta,
    ) -> EndpointPlan:
        # Attach is driven through HelperProvisioner (a semantic ATTACH verb), not here.
        raise HelperClientError("attach_endpoint must go through the helper provisioner")

    @override
    async def detach_endpoint(self, kernel: AbstractKernel) -> None:
        pass


class HelperProvisioner:
    """Drop-in for ``ContainerNetworkProvisioner`` that routes per-container attach/detach to
    the helper. The agent-supplied ``task_pid`` is intentionally ignored: the helper resolves
    the PID from containerd itself and pins the netns, so a stale/forged PID cannot mislead it.
    """

    _client: HelperClient
    _session_of: dict[str, str]

    def __init__(self, client: HelperClient) -> None:
        self._client = client
        self._session_of = {}

    async def attach(
        self,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
        *,
        meta: SessionNetMeta,
        container_id: str,
        task_pid: int,
    ) -> tuple[EndpointPlan, dict[NetworkRole, str]]:
        # Relay the manager-assigned overlay IP (present for multi-node vxlan sessions) so the
        # helper attaches the container at its central, disjoint address instead of a per-node
        # host-local one. The helper re-validates it is within the session subnet; None (single
        # node) leaves the helper on its host-local fallback. The MAC is derived from the IP
        # helper-side, so it is not sent.
        overlay_ip = kernel_config.get("cluster_network_ip")
        resp = await self._client.call(
            HelperRequest(
                op=HelperOp.ATTACH_CONTAINER,
                session_id=meta.session_id,
                container_id=container_id,
                ip=overlay_ip,
            )
        )
        self._session_of[container_id] = meta.session_id
        assigned: dict[NetworkRole, str] = {}
        for role_name, ip in (resp.assigned or {}).items():
            try:
                assigned[NetworkRole(role_name)] = ip
            except ValueError:
                continue
        # The concrete plan lives helper-side (kept for detach); the agent only needs a
        # handle to pass back to detach, so an empty plan is sufficient.
        return EndpointPlan(attachments=[]), assigned

    async def detach(self, plan: EndpointPlan, *, container_id: str, task_pid: int) -> None:
        session_id = self._session_of.pop(container_id, None)
        if session_id is None:
            return
        await self._client.call(
            HelperRequest(
                op=HelperOp.DETACH_CONTAINER,
                session_id=session_id,
                container_id=container_id,
            )
        )
