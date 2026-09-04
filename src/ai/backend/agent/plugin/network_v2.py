"""Runtime-neutral cluster-network agent plugin (v2).

Unlike v1 (`agent/plugin/network.py`), whose `join_network()` returns a Docker
container-config dict, v2 separates host-level *session-network lifecycle* (the agent
builds the vxlan/bridge/routes itself) from runtime-specific *endpoint attach*, and
returns a runtime-neutral `NetworkAttachSpec` that a Docker or containerd provisioner
interprets. See proposals/BEP-1062/agent-plugin-v2.md.
"""

from abc import ABCMeta, abstractmethod
from collections.abc import Iterable, Sequence
from typing import Any

from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.plugin.network import (
    ContainerNetworkCapability,
    ContainerNetworkInfo,
)
from ai.backend.common.network.types import (
    AgentNetworkCaps,
    EndpointPlan,
    Member,
    SessionNetMeta,
)
from ai.backend.common.plugin import AbstractPlugin, BasePluginContext
from ai.backend.common.types import ClusterInfo, KernelCreationConfig


class AbstractNetworkAgentPluginV2[TKernel: AbstractKernel](AbstractPlugin, metaclass=ABCMeta):
    """Runtime-neutral cluster-network backend attached on the agent side.

    A concrete backend (vxlan / bridge) implements this once and works
    under any runtime; runtime specifics live in the provisioner that consumes
    `NetworkAttachSpec`.

    Contract: implementations are stateless data-plane executors. They must NOT start
    their own etcd ``members/`` watch. A per-session, runtime-neutral
    ``SessionNetworkCoordinator`` owns membership watching and drives ``add_peer`` /
    ``del_peer`` (which must be idempotent). See BEP-1062/agent-plugin-v2.md.
    """

    @abstractmethod
    async def probe_caps(self) -> AgentNetworkCaps:
        """Self-diagnose networking capabilities (tunnel offload, native routing, ...).

        The result feeds the manager's per-session backend selection and is published
        under ``network/agent/{agent_id}/caps``.
        """
        raise NotImplementedError

    @abstractmethod
    async def setup_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        """Build this node's host-level data plane for the session (bridge, vxlan, ...).

        Called once per session on each participating node before any endpoint attach.
        """
        raise NotImplementedError

    @abstractmethod
    async def adopt_session_network(self, meta: SessionNetMeta, self_member: Member) -> None:
        """Re-attach this backend to a session whose data plane is already up.

        Called instead of `setup_session_network` when an agent restarts onto containers that
        survived it. It restores whatever per-session bookkeeping the backend keeps, and must not
        delete or recreate host devices: `setup_session_network` does that by name, so running it
        here would cut the surviving containers off the network. A backend may hold a device down
        while it re-establishes a promised security property.
        """
        raise NotImplementedError

    @abstractmethod
    async def teardown_session_network(self, session_id: str) -> None:
        """Tear down all host-level state for the session. Must be idempotent."""
        raise NotImplementedError

    async def ensure_session_security(self, session_id: str, peers: Sequence[Member]) -> None:
        """Re-assert whatever must hold for this session's traffic to be safe, and raise if it
        cannot be made to hold.

        Called on every reconcile pass, independently of whether the membership changed. What the
        backend programmed can be removed under it by anything that touches the host -- an
        `iptables -F`, a firewall reload, an `ip xfrm state flush` -- and none of that shows up as
        a membership diff, so a backend that only acts on peers it has not seen before never
        notices. A default no-op: a backend with nothing to protect has nothing to re-assert.

        ``peers`` is the session's published membership, not a diff, and it is what the backend must
        re-assert against rather than its own memory of what it programmed: a backend that restarted
        has none, and the caller does not resend a peer whose record has not changed.
        """
        return

    async def restore_session_peer_ownership(
        self, session_id: str, peers: Sequence[Member]
    ) -> None:
        """Restore durable peer ownership immediately after adopting a session.

        A privileged executor whose process-local refcounts outlive neither its host devices nor
        XFRM state uses this before security reconciliation or teardown. ``peers`` comes from that
        executor's own journal. Backends without shared peer state need no work.
        """
        return

    async def prepare_recovery(self) -> None:
        """Fail-close surviving host state before a privileged executor reads its journal.

        The default is a no-op for backends without persistent cross-node paths. Overlay backends
        use this before recovery knows which sessions it can safely adopt.
        """
        return

    @abstractmethod
    async def add_peer(self, session_id: str, peer: Member) -> None:
        """Reflect a newly joined peer (vxlan: FDB append)."""
        raise NotImplementedError

    @abstractmethod
    async def del_peer(self, session_id: str, peer: Member) -> None:
        """Reflect a departed peer. Must be idempotent (lease-driven recovery)."""
        raise NotImplementedError

    async def add_endpoint(self, session_id: str, *, ip: str, mac: str, vtep_ip: str) -> None:
        """Proactively program forwarding + ARP for a known remote container endpoint,
        from the manager-assigned ``endpoints/`` table (no BUM flood).

        Overlay-specific (vxlan programs unicast FDB + neighbor). Backends with no cross-node
        overlay (bridge) do not need per-endpoint programming; default no-op.
        Must be idempotent."""
        pass

    async def del_endpoint(self, session_id: str, *, ip: str, mac: str, vtep_ip: str) -> None:
        """Remove a departed endpoint's forwarding + ARP state. Idempotent; default no-op."""
        pass

    async def setup_dns_redirect(self, session_id: str, loopback_port: int) -> None:
        """Redirect the session gateway's ``:53`` to the agent's cluster resolver, which bound
        ``127.0.0.1:<loopback_port>``. The privileged holder (privnet, or the privileged in-process
        backend) derives the gateway from the session and installs the iptables DNAT — the agent
        supplies only the local port it bound. Idempotent (replaces any prior rule); default no-op.
        See cluster-name-resolution.md."""
        pass

    async def teardown_dns_redirect(self, session_id: str) -> None:
        """Remove the session's ``:53`` cluster-DNS redirect. Idempotent; default no-op."""
        pass

    @abstractmethod
    async def attach_endpoint(
        self,
        kernel_config: KernelCreationConfig,
        cluster_info: ClusterInfo,
        *,
        meta: SessionNetMeta,
    ) -> EndpointPlan:
        """Return the ordered interface chain for attaching this container.

        Always contains one LOCAL interface (agent control channel + egress, default
        route). Multi-node sessions additionally contain one OVERLAY interface for
        cross-node session communication.
        """
        raise NotImplementedError

    @abstractmethod
    async def detach_endpoint(self, kernel: TKernel) -> None:
        """Perform extra steps to detach the container from the network."""
        raise NotImplementedError

    async def get_capabilities(self) -> set[ContainerNetworkCapability]:
        """Advertise optional capabilities (e.g. GLOBAL for port forwarding). Empty by default."""
        return set()

    async def prepare_port_forward(
        self,
        kernel: TKernel,
        bind_host: str,
        ports: Iterable[tuple[int, int]],
        **kwargs: Any,
    ) -> None:
        """Prepare port forwarding before spawn. Only used when GLOBAL is advertised."""
        pass

    async def expose_ports(
        self,
        kernel: TKernel,
        bind_host: str,
        ports: Iterable[tuple[int, int]],
        **kwargs: Any,
    ) -> ContainerNetworkInfo | None:
        """Expose ports after start. Only used when GLOBAL is advertised."""
        return None


class NetworkPluginContextV2(BasePluginContext[AbstractNetworkAgentPluginV2[Any]]):
    plugin_group = "backendai_network_agent_v2"
