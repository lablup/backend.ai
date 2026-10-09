"""What the agent hands a CNI plugin and what it gets back, after the CNI spec's ADD/DEL/STATUS/GC.

The agent plays the CNI runtime: it owns the container and its netns, never the network.
"""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Final

__all__ = (
    "CNI_ARG_KERNEL_ID",
    "CNI_ARG_SESSION_ID",
    "CNI_ARG_CLUSTER_HOSTNAME",
    "CNI_IFNAME",
    "CNI_TYPE_KEY",
    "CniAttachment",
    "CniDns",
    "CniInterface",
    "CniIpConfig",
    "CniPortMapping",
    "CniRequest",
    "CniResult",
    "CniRoute",
    "CniRuntimeConfig",
    "CniStatus",
    "netns_path_for_pid",
    "pid_of_netns_path",
)

#: The key of a session's network config naming the CNI plugin that serves it (CNI's ``type``).
CNI_TYPE_KEY: Final = "type"

#: The interface the agent asks for in every container; the plugin may add more.
CNI_IFNAME: Final = "eth0"

#: ``CNI_ARGS`` the agent always passes: which session and kernel the container is.
CNI_ARG_SESSION_ID: Final = "BAI_SESSION_ID"
CNI_ARG_KERNEL_ID: Final = "BAI_KERNEL_ID"
CNI_ARG_CLUSTER_HOSTNAME: Final = "BAI_CLUSTER_HOSTNAME"

_NETNS_OF_PID: Final = re.compile(r"/proc/([1-9][0-9]*)/ns/net")


def netns_path_for_pid(pid: int) -> str:
    """The netns path of a process, the form every runtime of this agent hands over."""
    return f"/proc/{pid}/ns/net"


def pid_of_netns_path(netns: str) -> int | None:
    """The PID in a ``/proc/<pid>/ns/net`` path, or None for any other form (or none)."""
    if (m := _NETNS_OF_PID.fullmatch(netns)) is None:
        return None
    return int(m.group(1))


@dataclass(frozen=True)
class CniPortMapping:
    """A host port to forward to the container (CNI ``portMappings`` capability)."""

    host_port: int
    container_port: int
    protocol: str = "tcp"
    host_ip: str | None = None


@dataclass(frozen=True)
class CniRuntimeConfig:
    """Per-container capability arguments (CNI ``runtimeConfig``)."""

    port_mappings: Sequence[CniPortMapping] = ()
    #: Addresses the controller assigned this container (CNI ``ips`` capability), with no prefix.
    ips: Sequence[str] = ()


@dataclass(frozen=True)
class CniRequest:
    """One ADD or DEL. ``config`` is the session's network config, opaque to the agent."""

    container_id: str
    #: ``/proc/<pid>/ns/net``; empty on a DEL whose container has no process left.
    netns: str
    ifname: str
    config: Mapping[str, Any]
    #: ``CNI_ARGS``: see the ``CNI_ARG_*`` keys.
    args: Mapping[str, str] = field(default_factory=dict)
    runtime_config: CniRuntimeConfig = field(default_factory=CniRuntimeConfig)


@dataclass(frozen=True)
class CniInterface:
    name: str
    mac: str | None = None
    #: The netns the interface is in; None for a host-side interface.
    sandbox: str | None = None


@dataclass(frozen=True)
class CniIpConfig:
    #: CIDR, e.g. ``10.0.0.5/24``.
    address: str
    gateway: str | None = None
    #: Index into `CniResult.interfaces`.
    interface: int | None = None

    @property
    def ip(self) -> str:
        """The address without its prefix length."""
        return str(ipaddress.ip_interface(self.address).ip)


@dataclass(frozen=True)
class CniRoute:
    dst: str
    gw: str | None = None


@dataclass(frozen=True)
class CniDns:
    nameservers: Sequence[str] = ()
    domain: str | None = None
    search: Sequence[str] = ()
    options: Sequence[str] = ()


@dataclass(frozen=True)
class CniResult:
    """An ADD's result. The first IP is the container's primary address: the agent dials it."""

    interfaces: Sequence[CniInterface] = ()
    ips: Sequence[CniIpConfig] = ()
    routes: Sequence[CniRoute] = ()
    dns: CniDns = field(default_factory=CniDns)

    @property
    def primary_ip(self) -> str | None:
        return self.ips[0].ip if self.ips else None


@dataclass(frozen=True)
class CniStatus:
    """A plugin's STATUS: None means it can serve ADDs, else why it cannot."""

    not_ready_reason: str | None = None


@dataclass(frozen=True)
class CniAttachment:
    """A container the runtime still has, for a GC: what the plugin may keep."""

    container_id: str
    ifname: str
    args: Mapping[str, str] = field(default_factory=dict)
