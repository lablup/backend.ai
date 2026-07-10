"""Runtime-neutral cluster-network agent plugin (v2).

Unlike v1 (`agent/plugin/network.py`), whose `join_network()` returns a Docker
container-config dict, v2 separates host-level *session-network lifecycle* (the agent
builds the vxlan/bridge/routes itself) from runtime-specific *endpoint attach*, and
returns a runtime-neutral `NetworkAttachSpec` that a Docker or containerd provisioner
interprets. See proposals/BEP-1058/agent-plugin-v2.md.
"""

from abc import ABCMeta, abstractmethod
from collections.abc import Iterable
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

    A concrete backend (vxlan / host-gw / wireguard) implements this once and works
    under any runtime; runtime specifics live in the provisioner that consumes
    `NetworkAttachSpec`.

    Contract: implementations are stateless data-plane executors. They must NOT start
    their own etcd ``members/`` watch. A per-session, runtime-neutral
    ``SessionNetworkCoordinator`` owns membership watching and drives ``add_peer`` /
    ``del_peer`` (which must be idempotent). See BEP-1058/agent-plugin-v2.md.
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
        survived it. It restores whatever per-session bookkeeping the backend keeps, and must
        NOT touch host devices: `setup_session_network` deletes and recreates them by name, so
        running it here would cut the surviving containers off the network.
        """
        raise NotImplementedError

    @abstractmethod
    async def teardown_session_network(self, session_id: str) -> None:
        """Tear down all host-level state for the session. Must be idempotent."""
        raise NotImplementedError

    @abstractmethod
    async def add_peer(self, session_id: str, peer: Member) -> None:
        """Reflect a newly joined peer (vxlan: FDB append / host-gw: route add)."""
        raise NotImplementedError

    @abstractmethod
    async def del_peer(self, session_id: str, peer: Member) -> None:
        """Reflect a departed peer. Must be idempotent (lease-driven recovery)."""
        raise NotImplementedError

    async def add_endpoint(self, session_id: str, *, ip: str, mac: str, vtep_ip: str) -> None:
        """Proactively program forwarding + ARP for a known remote container endpoint,
        from the manager-assigned ``endpoints/`` table (no BUM flood).

        Overlay-specific (vxlan programs unicast FDB + neighbor). Backends whose peers are
        node-granular (host-gw routes) do not need per-endpoint programming; default no-op.
        Must be idempotent."""
        pass

    async def del_endpoint(self, session_id: str, *, ip: str, mac: str, vtep_ip: str) -> None:
        """Remove a departed endpoint's forwarding + ARP state. Idempotent; default no-op."""
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
