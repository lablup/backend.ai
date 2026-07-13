"""Entry point for the privileged network helper daemon (BEP-1062).

Capabilities needed (all four, for the reasons noted):

- CAP_NET_ADMIN   — iproute2 / iptables: bridges, veth, FDB/ARP, the service DNAT rules
- CAP_SYS_ADMIN   — enter a container's network namespace (setns) to attach its interface
- CAP_SYS_PTRACE  — open ``/proc/<pid>/ns/net`` of a container whose task runs as root, when the
                    helper itself runs as a non-root uid (omitting it fails "cannot open container
                    netns")
- CAP_DAC_READ_SEARCH — read those same ``/proc/<pid>`` entries across the uid boundary

Run as a systemd service scoped to exactly those:

    [Service]
    User=backendai-agent
    AmbientCapabilities=CAP_NET_ADMIN CAP_SYS_ADMIN CAP_SYS_PTRACE CAP_DAC_READ_SEARCH
    CapabilityBoundingSet=CAP_NET_ADMIN CAP_SYS_ADMIN CAP_SYS_PTRACE CAP_DAC_READ_SEARCH
    NoNewPrivileges=yes
    ExecStart=/usr/bin/python -m ai.backend.agent.network.helper ...

For local development, ``setpriv`` drops to the agent's uid while keeping those caps ambient. Two
gotchas: ``--bounding-set`` tokens need the ``+`` prefix (unlike ``--ambient-caps``, a bare name
is "bad capability string"), and dropping to the agent uid with ``--reuid`` is what makes the
socket owned by — and so connectable by — the agent (a root-owned 0600 socket is not):

    CAPS=+net_admin,+sys_admin,+sys_ptrace,+dac_read_search
    sudo setpriv --reuid "$AGENT_UID" --regid "$AGENT_GID" --clear-groups \
        --ambient-caps "$CAPS" --bounding-set "$CAPS" --inh-caps "$CAPS" \
        -- ./py -m ai.backend.agent.network.helper

Configuration comes from environment variables so the launcher stays trivial:

    BACKENDAI_NETHELPER_SOCKET   unix socket path override (otherwise taken from the agent
                                 config's [agent] network-helper-socket, else /run default)
    BACKENDAI_NETHELPER_CONFIG   agent config file to read the socket path from (optional)
    BACKENDAI_NETHELPER_UID      uid allowed to connect (default: the invoking SUDO_UID)
    BACKENDAI_NETHELPER_AGENT_ID this node's agent id
    BACKENDAI_NETHELPER_HOST_IP  advertised host IP (VTEP for vxlan)
    BACKENDAI_NETHELPER_CTRD_NS  containerd namespace (default backend-ai)
    BACKENDAI_NETHELPER_UPLINK   uplink interface for vxlan (default eth0)
    BACKENDAI_NETHELPER_LOCAL_POOL   node-local LOCAL subnet pool (otherwise taken from the agent
                                     config's [container] local-network-pool)
    BACKENDAI_NETHELPER_LOCAL_BLOCK  per-session block prefix length within that pool (otherwise
                                     [container] local-network-block-size)
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ai.backend.agent.containerd.runtime.grpc import ContainerdGrpcRuntime
from ai.backend.agent.network.backends.bridge import BridgeNetworkPlugin
from ai.backend.agent.network.backends.vxlan import VxlanNetworkPlugin
from ai.backend.agent.network.helper.server import NetworkHelperServer
from ai.backend.agent.network.local_subnet import (
    DEFAULT_BLOCK_PREFIXLEN,
    DEFAULT_LOCAL_POOL,
    LocalSubnetLayout,
    get_local_subnet_allocator,
)
from ai.backend.agent.network.native_attacher import NativeBridgeAttachRunner
from ai.backend.common import config as common_config
from ai.backend.common.network.types import NetworkBackendKind

log = logging.getLogger("ai.backend.agent.network.helper")

_DEFAULT_SOCKET = "/run/backend.ai/net-helper.sock"


def _default_uid() -> int:
    sudo_uid = os.environ.get("SUDO_UID")
    return int(sudo_uid) if sudo_uid else os.getuid()


def _read_agent_config() -> Mapping[str, Any]:
    """The agent's own config file, so the two processes cannot drift on the values they must
    agree about. Returns empty (and says so) when it cannot be read: every caller has a default."""
    try:
        cfg_path_env = os.environ.get("BACKENDAI_NETHELPER_CONFIG")
        cfg_path = Path(cfg_path_env) if cfg_path_env else None
        raw_cfg, _ = common_config.read_from_file(cfg_path, "agent")
        return raw_cfg
    except Exception as e:
        log.warning("could not read the agent config: %s", e)
        return {}


def _resolve_socket_path(raw_cfg: Mapping[str, Any]) -> str:
    """The socket path is the single value the helper and agent must agree on. Resolution
    order: explicit env override, then the agent config's ``[agent] network-helper-socket``
    (same file the agent reads, so they stay in sync), then the /run default."""
    if env := os.environ.get("BACKENDAI_NETHELPER_SOCKET"):
        return env
    if value := (raw_cfg.get("agent") or {}).get("network-helper-socket"):
        return str(value)
    return _DEFAULT_SOCKET


def _resolve_local_subnet_layout(raw_cfg: Mapping[str, Any]) -> LocalSubnetLayout:
    """How the node's LOCAL pool is cut. Under a helper this process owns the pool, so it must cut
    it exactly as the agent's config says — the agent hands it session ids and gets subnets back,
    and a helper cutting a different pool would answer with addresses no bridge is on."""
    container_cfg = raw_cfg.get("container") or {}
    pool = os.environ.get("BACKENDAI_NETHELPER_LOCAL_POOL") or container_cfg.get(
        "local-network-pool"
    )
    block = os.environ.get("BACKENDAI_NETHELPER_LOCAL_BLOCK") or container_cfg.get(
        "local-network-block-size"
    )
    return LocalSubnetLayout.parse(
        str(pool or DEFAULT_LOCAL_POOL), int(block or DEFAULT_BLOCK_PREFIXLEN)
    )


async def _amain() -> None:
    raw_cfg = _read_agent_config()
    socket_path = _resolve_socket_path(raw_cfg)
    allowed_uid = int(os.environ.get("BACKENDAI_NETHELPER_UID") or _default_uid())
    agent_id = os.environ.get("BACKENDAI_NETHELPER_AGENT_ID", "")
    host_ip = os.environ.get("BACKENDAI_NETHELPER_HOST_IP", "127.0.0.1")
    ctrd_ns = os.environ.get("BACKENDAI_NETHELPER_CTRD_NS", "backend-ai")
    uplink = os.environ.get("BACKENDAI_NETHELPER_UPLINK", "eth0")

    Path(socket_path).parent.mkdir(parents=True, exist_ok=True)

    runtime = ContainerdGrpcRuntime(namespace=ctrd_ns)
    # This helper is the node's single owner of every privileged network op, so it is also the
    # single owner of the node-local pool both backends carve their LOCAL block out of.
    local_subnets = get_local_subnet_allocator(layout=_resolve_local_subnet_layout(raw_cfg))
    backends = {
        str(NetworkBackendKind.VXLAN): VxlanNetworkPlugin(
            {}, {}, uplink=uplink, local_subnets=local_subnets
        ),
        str(NetworkBackendKind.BRIDGE): BridgeNetworkPlugin(
            {}, {}, uplink=uplink, local_subnets=local_subnets
        ),
    }
    server = NetworkHelperServer(
        socket_path=socket_path,
        allowed_uid=allowed_uid,
        agent_id=agent_id,
        host_ip=host_ip,
        runtime=runtime,
        cni_runner=NativeBridgeAttachRunner(),
        backends=backends,
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
