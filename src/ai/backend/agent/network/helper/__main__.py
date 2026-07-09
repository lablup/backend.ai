"""Entry point for the privileged network helper daemon (BEP-1058).

Run as a systemd service with only the needed capabilities, e.g.

    [Service]
    AmbientCapabilities=CAP_NET_ADMIN CAP_SYS_ADMIN
    CapabilityBoundingSet=CAP_NET_ADMIN CAP_SYS_ADMIN
    NoNewPrivileges=yes
    ExecStart=/usr/bin/python -m ai.backend.agent.network.helper ...

For local development, launch it with just those caps via ``setpriv``:

    sudo setpriv --ambient-caps +net_admin,+sys_admin \
        --bounding-set net_admin,sys_admin --inh-caps +net_admin,+sys_admin \
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
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from ai.backend.agent.containerd.runtime.grpc import ContainerdGrpcRuntime
from ai.backend.agent.network.backends.bridge import BridgeNetworkPlugin
from ai.backend.agent.network.backends.vxlan import VxlanNetworkPlugin
from ai.backend.agent.network.helper.server import NetworkHelperServer
from ai.backend.agent.network.native_attacher import NativeBridgeAttachRunner
from ai.backend.common import config as common_config
from ai.backend.common.network.types import NetworkBackendKind

log = logging.getLogger("ai.backend.agent.network.helper")

_DEFAULT_SOCKET = "/run/backend.ai/net-helper.sock"


def _default_uid() -> int:
    sudo_uid = os.environ.get("SUDO_UID")
    return int(sudo_uid) if sudo_uid else os.getuid()


def _resolve_socket_path() -> str:
    """The socket path is the single value the helper and agent must agree on. Resolution
    order: explicit env override, then the agent config's ``[agent] network-helper-socket``
    (same file the agent reads, so they stay in sync), then the /run default."""
    if env := os.environ.get("BACKENDAI_NETHELPER_SOCKET"):
        return env
    try:
        cfg_path_env = os.environ.get("BACKENDAI_NETHELPER_CONFIG")
        cfg_path = Path(cfg_path_env) if cfg_path_env else None
        raw_cfg, _ = common_config.read_from_file(cfg_path, "agent")
        if value := (raw_cfg.get("agent") or {}).get("network-helper-socket"):
            return str(value)
    except Exception as e:
        log.warning("could not read network-helper-socket from agent config: %s", e)
    return _DEFAULT_SOCKET


async def _amain() -> None:
    socket_path = _resolve_socket_path()
    allowed_uid = int(os.environ.get("BACKENDAI_NETHELPER_UID") or _default_uid())
    agent_id = os.environ.get("BACKENDAI_NETHELPER_AGENT_ID", "")
    host_ip = os.environ.get("BACKENDAI_NETHELPER_HOST_IP", "127.0.0.1")
    ctrd_ns = os.environ.get("BACKENDAI_NETHELPER_CTRD_NS", "backend-ai")
    uplink = os.environ.get("BACKENDAI_NETHELPER_UPLINK", "eth0")

    Path(socket_path).parent.mkdir(parents=True, exist_ok=True)

    runtime = ContainerdGrpcRuntime(namespace=ctrd_ns)
    backends = {
        str(NetworkBackendKind.VXLAN): VxlanNetworkPlugin({}, {}, uplink=uplink),
        str(NetworkBackendKind.BRIDGE): BridgeNetworkPlugin({}, {}, uplink=uplink),
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
