"""Agent-side client + proxies for the privileged network helper (BEP-1062).

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
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any, override

from ai.backend.agent.network.caps import probe_caps
from ai.backend.agent.network.helper.protocol import (
    HelperOp,
    HelperRequest,
    HelperResponse,
)
from ai.backend.agent.network.port_forward import PortForward
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
    async def adopt_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        # Nothing to do: the helper owns this session's devices, attach plans and backend state,
        # and it recovers them itself — from its own journal reconciled against containerd, not
        # from anything we could tell it (see helper/server.py `recover`). Re-declaring the session
        # here is exactly the move the trust model forbids the agent.
        return

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
        # The live attach goes through HelperProvisioner (a semantic ATTACH verb), so the only
        # caller here is the agent's restart recovery, re-deriving the plan it will later detach
        # with. Under a helper that plan lives helper-side, and detach is a verb naming the
        # container — so the agent needs nothing but a handle, and an empty plan is that handle.
        # (Raising instead, as this used to, aborted recovery for every container on the node and
        # left them all with no detach path: their host veths and addresses then leaked.)
        return EndpointPlan(attachments=[])

    @override
    async def detach_endpoint(self, kernel: AbstractKernel) -> None:
        pass


class HelperProvisioner:
    """Drop-in for ``ContainerNetworkProvisioner`` that routes per-container attach/detach to
    the helper. The agent-supplied ``task_pid`` is intentionally ignored: the helper resolves
    the PID from containerd itself and pins the netns, so a stale/forged PID cannot mislead it.

    One provisioner per session (the session network builds it alongside that session's
    orchestrator), so detach knows its session without having to have witnessed the attach — which
    is what a restarted agent has not done for the kernels that outlived it.
    """

    _client: HelperClient
    _session_id: str

    def __init__(self, client: HelperClient, session_id: str) -> None:
        self._client = client
        self._session_id = session_id

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
        # The plan is ignored: the helper holds the real one (and re-derives it after its own
        # restart). Detach names the container; the helper resolves everything else.
        await self._client.call(
            HelperRequest(
                op=HelperOp.DETACH_CONTAINER,
                session_id=self._session_id,
                container_id=container_id,
            )
        )


# Any valid identifier; LIST_PORTS is node-wide, so the helper only uses it as a lock key.
_LIST_LOCK_KEY = "list-ports"


class HelperPortForwarder:
    """Same shape as ``PortForwarder``, but the iptables work happens in the helper.

    The container's address is deliberately not sent: the helper DNATs to the LOCAL address it
    assigned at attach. So ``install`` drops the ``container_ip`` its argument carries — that is
    the agent's belief, not a fact the helper is willing to act on.
    """

    _client: HelperClient
    # container_id -> session_id; the helper's session lock and its attach record are keyed by it
    _session_of: Callable[[str], str | None]

    def __init__(self, client: HelperClient, session_of: Callable[[str], str | None]) -> None:
        self._client = client
        self._session_of = session_of

    def _session_for(self, container_id: str) -> str:
        session_id = self._session_of(container_id)
        if session_id is None:
            raise HelperClientError(f"no session known for container {container_id}")
        return session_id

    async def install(self, forwards: Sequence[PortForward]) -> None:
        if not forwards:
            return
        container_id = forwards[0].container_id
        await self._client.call(
            HelperRequest(
                op=HelperOp.PUBLISH_PORTS,
                session_id=self._session_for(container_id),
                container_id=container_id,
                ports=tuple((f.host_port, f.container_port, f.host_ip) for f in forwards),
            )
        )

    async def remove_container(self, container_id: str) -> list[int]:
        # The helper finds the rules by their container tag, so an unknown session is not fatal:
        # fall back to the container id as the lock key rather than leak the rules.
        session_id = self._session_of(container_id) or container_id
        resp = await self._client.call(
            HelperRequest(
                op=HelperOp.UNPUBLISH_PORTS,
                session_id=session_id,
                container_id=container_id,
            )
        )
        return list(resp.host_ports or ())

    async def list_forwards(self, *, container_id: str | None = None) -> list[PortForward]:
        resp = await self._client.call(
            HelperRequest(op=HelperOp.LIST_PORTS, session_id=_LIST_LOCK_KEY)
        )
        forwards = [
            PortForward(container_id=cid, host_port=hp, container_ip=ip, container_port=cp)
            for cid, hp, ip, cp in (resp.forwards or ())
        ]
        if container_id is None:
            return forwards
        return [f for f in forwards if f.container_id == container_id]
