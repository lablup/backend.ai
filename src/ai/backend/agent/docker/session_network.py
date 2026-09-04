"""Session networking (BEP-1062) for the Docker backend.

The data plane is the same vxlan the containerd backend uses, and so is the code that sets it up:
``ensure_session``, ``teardown_session`` and the restart recovery never touch a container runtime,
and the four things they do ask about containers are exactly what a
:class:`~ai.backend.agent.network.locator.ContainerLocator` answers. So Docker borrows that half
whole, brings its own locator, and keeps its own container lifecycle -- which is the part that
genuinely differs, because Docker's API takes its own container config rather than an OCI spec.

What Docker must add on top is the two-phase start the attach needs (see
:mod:`ai.backend.agent.docker.gate`) and one decision at network-apply time: a session with a
BEP-1062 backend gets ``NetworkMode: none`` and is attached by PID, instead of being handed to
Docker's own networking.

Measured end to end on Docker 29.1.3: two ``--network=none`` containers, a vxlan device built in
each node's netns and moved into the container, carry traffic between 10.128.5.1 and 10.128.5.2
with 0% loss, and the underlay shows ``VXLAN, flags [I] (0x08), vni 4097`` on UDP 4789. No Swarm is
involved -- BAI already has the control plane Swarm would otherwise provide.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Final

from ai.backend.agent.docker.locator import DockerContainerLocator
from ai.backend.agent.network.local_subnet import LocalSubnetLayout
from ai.backend.agent.network.session_network import (
    SessionNetwork,
    build_session_network,
)
from ai.backend.common.etcd import AbstractKVStore
from ai.backend.common.types import ClusterInfo

__all__ = (
    "NO_NETWORK_MODE",
    "build_docker_session_network",
    "is_session_networked",
    "make_docker_locator",
)

#: What Docker is told when BAI attaches the container itself. The container then starts with only
#: ``lo`` (and the kernel's ``tunl0``), and everything it reaches is something the agent moved in.
NO_NETWORK_MODE: Final = "none"


def is_session_networked(cluster_info: ClusterInfo) -> bool:
    """Whether this session's network is BAI's to build.

    The discriminator is the same one the containerd backend uses: a ``backend`` key in the
    manager's network config names a BEP-1062 data plane (vxlan, or a node-local bridge). Its
    absence means either no cluster network at all or a v1 driver -- ``mode`` names that one, and
    'overlay' there is Docker Swarm, which is Docker's to run and not ours to intercept.
    """
    network_config: Mapping[str, Any] = (
        (cluster_info.get("network_config") or {}) if cluster_info else {}
    )
    return bool(network_config.get("backend"))


def make_docker_locator() -> DockerContainerLocator:
    """The locator a Docker session network is built with.

    A function rather than the class inline so the wiring reads as a choice: Docker brings a locator
    and no runtime, which is what the session network's two-collaborator split is for.
    """
    return DockerContainerLocator()


def build_docker_session_network(
    etcd: AbstractKVStore,
    *,
    agent_id: str,
    host_ip: str,
    uplink: str = "eth0",
    privnet_socket: str | None = None,
    local_subnet_layout: LocalSubnetLayout | None = None,
    agent_state_dir: Path | None = None,
    vtep_ip: str | None = None,
    configured_dns: Sequence[str] = (),
) -> SessionNetwork:
    """The session network a Docker node runs: the shared session half, and nothing else.

    A locator and no runtime. That is not a shortcut around an unimplemented client -- it is the
    accurate statement: Docker keeps its own container lifecycle, so a runtime here would be a
    second way to create and kill the same containers. Reaching one of those methods on this object
    raises rather than silently taking the other path (ContainerLifecycleUnavailable).
    """
    return build_session_network(
        etcd,
        agent_id=agent_id,
        host_ip=host_ip,
        uplink=uplink,
        locator=make_docker_locator(),
        privnet_socket=privnet_socket,
        local_subnet_layout=local_subnet_layout,
        agent_state_dir=agent_state_dir,
        vtep_ip=vtep_ip,
        configured_dns=configured_dns,
    )
