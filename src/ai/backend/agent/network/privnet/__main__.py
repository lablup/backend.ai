"""Entry point for the privnet daemon (privileged network) (BEP-1062).

Capabilities needed (all four, for the reasons noted):

- CAP_NET_ADMIN   — iproute2 / iptables: bridges, veth, FDB/ARP, the service DNAT rules
- CAP_SYS_ADMIN   — enter a container's network namespace (setns) to attach its interface
- CAP_SYS_PTRACE  — open ``/proc/<pid>/ns/net`` of a container whose task runs as root, when the
                    privnet itself runs as a non-root uid (omitting it fails "cannot open container
                    netns")
- CAP_DAC_READ_SEARCH — read those same ``/proc/<pid>`` entries across the uid boundary
- CAP_DAC_OVERRIDE — create the per-kernel cgroup under the root-owned
                    /sys/fs/cgroup/backend-ai. Not a widening in practice: a process holding
                    CAP_SYS_ADMIN can already reach anything this would

Run as a systemd service scoped to exactly those:

    [Service]
    User=backendai-agent
    AmbientCapabilities=CAP_NET_ADMIN CAP_SYS_ADMIN CAP_SYS_PTRACE CAP_DAC_READ_SEARCH CAP_DAC_OVERRIDE
    CapabilityBoundingSet=CAP_NET_ADMIN CAP_SYS_ADMIN CAP_SYS_PTRACE CAP_DAC_READ_SEARCH CAP_DAC_OVERRIDE
    NoNewPrivileges=yes
    ExecStart=/usr/bin/python -m ai.backend.agent.network.privnet ...

For local development, ``setpriv`` drops to the agent's uid while keeping those caps ambient. Two
gotchas: ``--bounding-set`` tokens need the ``+`` prefix (unlike ``--ambient-caps``, a bare name
is "bad capability string"), and dropping to the agent uid with ``--reuid`` is what makes the
socket owned by — and so connectable by — the agent (a root-owned 0600 socket is not):

    CAPS=+net_admin,+sys_admin,+sys_ptrace,+dac_read_search,+dac_override
    sudo setpriv --reuid "$AGENT_UID" --regid "$AGENT_GID" --clear-groups \
        --ambient-caps "$CAPS" --bounding-set "$CAPS" --inh-caps "$CAPS" \
        -- ./py -m ai.backend.agent.network.privnet

Configuration comes from environment variables so the launcher stays trivial:

    BACKENDAI_PRIVNET_SOCKET   unix socket path override (otherwise taken from the agent
                                 config's [agent] network-privnet-socket, else /run default)
    BACKENDAI_PRIVNET_CONFIG   agent config file to read the socket path from (optional)
    BACKENDAI_PRIVNET_UID      uid allowed to connect (default: the invoking SUDO_UID)
    BACKENDAI_PRIVNET_AGENT_ID this node's agent id
    BACKENDAI_PRIVNET_HOST_IP  advertised host IP (VTEP for vxlan)
    BACKENDAI_PRIVNET_CTRD_NS  containerd namespace (default backend-ai)
    BACKENDAI_PRIVNET_UPLINK   uplink interface for vxlan (default: the live interface holding
                                 HOST_IP, so the overlay rides the L2 the VTEP is advertised on;
                                 eth0 if none does)
    BACKENDAI_PRIVNET_LOCAL_POOL   node-local LOCAL subnet pool (otherwise taken from the agent
                                     config's [container] local-network-pool)
    BACKENDAI_PRIVNET_LOCAL_BLOCK  per-session block prefix length within that pool (otherwise
                                     [container] local-network-block-size)
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.containerd.runtime.grpc import ContainerdGrpcRuntime
from ai.backend.agent.containerd.runtime.interface import OciRuntime
from ai.backend.agent.network.backends.bridge import BridgeNetworkPlugin
from ai.backend.agent.network.backends.vxlan import VxlanNetworkPlugin
from ai.backend.agent.network.local_subnet import (
    DEFAULT_BLOCK_PREFIXLEN,
    DEFAULT_LOCAL_POOL,
    LocalSubnetLayout,
    get_local_subnet_allocator,
)
from ai.backend.agent.network.native_attacher import (
    NativeBridgeAttachRunner,
    get_host_local_ipam,
)
from ai.backend.agent.network.privnet.journal import PrivNetJournal
from ai.backend.agent.network.privnet.server import PrivNetServer
from ai.backend.agent.network.vtep import uplink_for_ip, usable_vtep
from ai.backend.agent.types import AgentBackend, get_agent_discovery
from ai.backend.common import config as common_config
from ai.backend.common.network.types import NetworkBackendKind

log = logging.getLogger("ai.backend.agent.network.privnet")

_DEFAULT_SOCKET = "/run/backend.ai/net-privnet.sock"


def _default_uid() -> int:
    sudo_uid = os.environ.get("SUDO_UID")
    return int(sudo_uid) if sudo_uid else os.getuid()


def _read_agent_config() -> Mapping[str, Any]:
    """The agent's own config file, so the two processes cannot drift on the values they must
    agree about. Returns empty (and says so) when it cannot be read: every caller has a default."""
    try:
        cfg_path_env = os.environ.get("BACKENDAI_PRIVNET_CONFIG")
        cfg_path = Path(cfg_path_env) if cfg_path_env else None
        raw_cfg, _ = common_config.read_from_file(cfg_path, "agent")
        return raw_cfg
    except Exception as e:
        log.warning("could not read the agent config: %s", e)
        return {}


def _resolve_socket_path(raw_cfg: Mapping[str, Any]) -> str:
    """The socket path is the single value the privnet and agent must agree on. Resolution
    order: explicit env override, then the agent config's ``[agent] network-privnet-socket``
    (same file the agent reads, so they stay in sync), then the /run default."""
    if env := os.environ.get("BACKENDAI_PRIVNET_SOCKET"):
        return env
    if value := (raw_cfg.get("agent") or {}).get("network-privnet-socket"):
        return str(value)
    return _DEFAULT_SOCKET


def _var_base_path(raw_cfg: Mapping[str, Any]) -> Path | None:
    """The agent's ``var-base-path``, which is what every per-node store must hang off.

    Three stores defaulted to a constant under /var/lib/backend.ai — the containerd log root, the
    LOCAL subnet store, and privnet's own journal. Each broke the same two deployments: a host
    running more than one agent (they collide) and an unprivileged privnet (the directory is
    root-owned). Reading the agent's own setting is what keeps the two processes pointing at the
    same place.
    """
    if base := (raw_cfg.get("agent") or {}).get("var-base-path"):
        return Path(str(base))
    return None


def _resolve_ipam_state_dir(raw_cfg: Mapping[str, Any]) -> Path | None:
    base = _var_base_path(raw_cfg)
    return (base / "net-ipam") if base is not None else None


def _resolve_privnet_state_dir(raw_cfg: Mapping[str, Any]) -> Path | None:
    base = _var_base_path(raw_cfg)
    return (base / "net-privnet") if base is not None else None


def _resolve_local_subnet_state_dir(raw_cfg: Mapping[str, Any]) -> Path | None:
    """Where the node-local subnet store lives, anchored the way the agent anchors it.

    The default is a constant under /var/lib/backend.ai, which is root-owned — and privnet runs as
    the agent's uid, so it cannot write there. Worse, that constant is shared by every agent on the
    host, and the store's second-writer guard (correctly) refuses the second one. The agent anchors
    it under its own `var-base-path`; privnet reads the same config, so it must anchor it the same
    way or the two disagree about which store is the session's.
    """
    base = _var_base_path(raw_cfg)
    return (base / "net-local-subnet") if base is not None else None


def _resolve_local_subnet_layout(raw_cfg: Mapping[str, Any]) -> LocalSubnetLayout:
    """How the node's LOCAL pool is cut. Under a privnet this process owns the pool, so it must cut
    it exactly as the agent's config says — the agent hands it session ids and gets subnets back,
    and a privnet cutting a different pool would answer with addresses no bridge is on."""
    container_cfg = raw_cfg.get("container") or {}
    pool = os.environ.get("BACKENDAI_PRIVNET_LOCAL_POOL") or container_cfg.get("local-network-pool")
    block = os.environ.get("BACKENDAI_PRIVNET_LOCAL_BLOCK") or container_cfg.get(
        "local-network-block-size"
    )
    return LocalSubnetLayout.parse(
        str(pool or DEFAULT_LOCAL_POOL), int(block or DEFAULT_BLOCK_PREFIXLEN)
    )


def _is_rootless(raw_cfg: Mapping[str, Any]) -> bool:
    """Whether this node's backend keeps its container records where the agent can write them."""
    name = (raw_cfg.get("agent") or {}).get("backend") or (raw_cfg.get("agent") or {}).get("mode")
    if not name:
        return False
    return AgentBackend(str(name)) in (AgentBackend.ENROOT, AgentBackend.SINGULARITY)


def _build_runtime(raw_cfg: Mapping[str, Any], ctrd_ns: str) -> OciRuntime:
    """The runtime client for THIS node's backend, not containerd's by assumption.

    privnet answers `_attach` by asking the runtime for a container's PID, and hard-coding the
    containerd client meant it asked a daemon that has never heard of an enroot or apptainer
    container — so a rootless agent could not delegate its networking at all and had to run
    privileged, which is the opposite of the point. The backend already publishes its own client
    through the discovery (the same dispatch that fixed the equivalent bug in the commit path,
    e2202cb5a); use it.

    Falls back to containerd when there is no agent config to read, which is the only case where
    the backend is genuinely unknown — and the historical default.
    """
    backend_name = (raw_cfg.get("agent") or {}).get("backend") or (raw_cfg.get("agent") or {}).get(
        "mode"
    )
    if not backend_name:
        log.warning(
            "no agent config to read the backend from; assuming containerd. "
            "Set BACKENDAI_PRIVNET_CONFIG so a rootless backend gets its own runtime client."
        )
        return ContainerdGrpcRuntime(namespace=ctrd_ns)
    local_config = AgentUnifiedConfig.model_validate(raw_cfg)
    backend = AgentBackend(str(backend_name))
    log.info("privnet driving the %s runtime", backend.value)
    return get_agent_discovery(backend).create_oci_runtime(local_config)


async def _amain() -> None:
    raw_cfg = _read_agent_config()
    socket_path = _resolve_socket_path(raw_cfg)
    allowed_uid = int(os.environ.get("BACKENDAI_PRIVNET_UID") or _default_uid())
    agent_id = os.environ.get("BACKENDAI_PRIVNET_AGENT_ID", "")
    host_ip = os.environ.get("BACKENDAI_PRIVNET_HOST_IP", "127.0.0.1")
    ctrd_ns = os.environ.get("BACKENDAI_PRIVNET_CTRD_NS", "backend-ai")
    # Derive the uplink from the advertised address, as the agent does: a vxlan device built on a
    # hard-coded eth0 that does not carry the VTEP advertises an endpoint peers cannot reach.
    uplink = os.environ.get("BACKENDAI_PRIVNET_UPLINK") or uplink_for_ip(host_ip)

    Path(socket_path).parent.mkdir(parents=True, exist_ok=True)

    runtime = _build_runtime(raw_cfg, ctrd_ns)
    # The rootless runtimes keep their container->PID map in memory, rebuilt from the on-disk
    # journal; opening here is what lets THIS process see containers the agent created.
    await runtime.open()
    # One privnet per agent, but the node-local pool is per NODE: the index it hands out names the
    # bridge device `bailo<index>`, which every process on this host shares. So this reads the
    # node-wide store and tags its claims with the agent it serves, rather than keeping a private
    # index space that would start at 0 alongside everyone else's. See `local_subnet`.
    local_subnets = get_local_subnet_allocator(
        layout=_resolve_local_subnet_layout(raw_cfg),
        owner=agent_id,
        # The store this privnet used before the journal became node-wide; its claims are adopted
        # so a half-upgraded node cannot hand the same block to two agents.
        legacy_dir=_resolve_local_subnet_state_dir(raw_cfg),
    )
    backends = {
        str(NetworkBackendKind.VXLAN): VxlanNetworkPlugin(
            {}, {}, uplink=uplink, local_subnets=local_subnets
        ),
        str(NetworkBackendKind.BRIDGE): BridgeNetworkPlugin(
            {}, {}, uplink=uplink, local_subnets=local_subnets
        ),
    }
    server = PrivNetServer(
        socket_path=socket_path,
        allowed_uid=allowed_uid,
        agent_id=agent_id,
        host_ip=host_ip,
        # Only an address that can actually anchor a tunnel is ever advertised to peers; with none,
        # the privnet refuses vxlan sessions instead of stranding them (see network.vtep).
        vtep_ip=usable_vtep(host_ip),
        runtime=runtime,
        journal=PrivNetJournal(_resolve_privnet_state_dir(raw_cfg)),
        ipam=get_host_local_ipam(_resolve_ipam_state_dir(raw_cfg)),
        cni_runner=NativeBridgeAttachRunner(
            uplink=uplink, ipam_state_dir=_resolve_ipam_state_dir(raw_cfg)
        ),
        backends=backends,
        # The same pool instance both backends carve from, so the LOCAL_SUBNET query reads the very
        # block a session's setup claimed rather than a second view that could drift from it.
        local_subnets=local_subnets,
        # Only the rootless backends need it: containerd's PID comes from a root-owned daemon the
        # agent cannot forge, and its kernels' namespaces are owned by uid 0 like the host's.
        netns_owner_uid=allowed_uid if _is_rootless(raw_cfg) else None,
    )
    await server.serve_forever()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    try:
        asyncio.run(_amain())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
