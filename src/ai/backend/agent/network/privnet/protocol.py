"""Wire protocol for the privnet daemon (BEP-1062).

The unprivileged agent and the privileged (CAP_NET_ADMIN) privnet speak a small,
**semantic** RPC over a unix socket: newline-delimited JSON, one request and one
response per line. The vocabulary is deliberately tiny and carries only opaque
identifiers (``session_id`` / ``container_id``) plus the manager-provided network
parameters — never argv, device names, netns paths, or CNI config. The privnet
derives every side-effecting value itself (see ``server.py``), so a compromised
agent cannot inject commands, target an arbitrary namespace, or name an arbitrary
device: the attack surface is the enum of verbs below, nothing more.

Keeping this module pure (dataclasses + encode/decode, no I/O) makes the protocol
unit-testable on both ends.
"""

from __future__ import annotations

import enum
import json
from dataclasses import dataclass
from typing import Any


class PrivNetOp(enum.StrEnum):
    SETUP_SESSION = "setup_session"
    TEARDOWN_SESSION = "teardown_session"
    ATTACH_CONTAINER = "attach_container"
    DETACH_CONTAINER = "detach_container"
    # Multi-node overlay (vxlan): program peer VTEP + remote-endpoint FDB/ARP. The agent's
    # coordinator drives these off its etcd membership/endpoint watch; only the privileged
    # ``bridge fdb`` / ``ip neigh`` execution is delegated here.
    ADD_PEER = "add_peer"
    DEL_PEER = "del_peer"
    ADD_ENDPOINT = "add_endpoint"
    DEL_ENDPOINT = "del_endpoint"
    # Host-port ingress: publish a container's service ports on host ports (DNAT), and withdraw
    # them. The agent sends only the port pairing; the DNAT destination is the LOCAL address the
    # privnet itself assigned at attach, so a lying agent cannot redirect a host port anywhere else.
    PUBLISH_PORTS = "publish_ports"
    UNPUBLISH_PORTS = "unpublish_ports"
    # Node-wide: every published port, so a restarted agent can take them back out of its port
    # pool. Read-only, and the agent installed them all in the first place.
    LIST_PORTS = "list_ports"
    # A session's node-local LOCAL /26. Read-only: the agent asks which block the privnet ALREADY
    # assigned (to write /etc/hosts for a single-node cluster), it does not declare one — the
    # inverse of the trust concern the rest of this protocol guards against.
    LOCAL_SUBNET = "local_subnet"
    # Cluster DNS: redirect the session gateway's :53 to the agent's unprivileged resolver, which
    # binds an ephemeral loopback port (127.0.0.1:<dns_port>) and sends that port here. The privnet
    # derives the gateway/bridge from the session it owns; the agent supplies only the loopback port
    # it bound — it cannot point :53 at anything but its own loopback. See cluster-name-resolution.md.
    # A rootless backend has no daemon to create its containers' cgroups: containerd/dockerd
    # declare `cgroupsPath` in the OCI spec and their ROOT daemon makes it, while enroot and
    # apptainer have no cgroup integration at all, so the agent must do it — and an
    # unprivileged agent cannot. Delegated here, to the process that already holds the
    # capabilities. Without it the kernel simply stays in the agent's own cgroup: no memory
    # limit, no cpuset pin, and no per-kernel stats.
    CONFINE_CONTAINER = "confine_container"
    RELEASE_CONTAINER = "release_container"
    SETUP_DNS_REDIRECT = "setup_dns_redirect"
    TEARDOWN_DNS_REDIRECT = "teardown_dns_redirect"


class ProtocolError(RuntimeError):
    """Malformed frame or unknown/typed field — a client that violates the wire
    contract. Never carries privileged detail back to the caller."""


def _decode_ports(raw: Any) -> tuple[tuple[int, int, str | None, str], ...] | None:
    """Shape-check only; the *values* are the policy layer's business.

    Each entry is ``[host_port, container_port]``, ``[host_port, container_port, host_ip]`` or
    ``[host_port, container_port, host_ip, protocol]``, where ``host_ip`` (the interface the service
    is published on) is a string or null and ``protocol`` is ``"tcp"``/``"udp"``. The shorter forms
    are accepted for compatibility and default to every-local-address / tcp."""
    if raw is None:
        return None
    if not isinstance(raw, list):
        raise ProtocolError("ports must be an array")
    entries: list[tuple[int, int, str | None, str]] = []
    for entry in raw:
        if not isinstance(entry, list) or len(entry) not in (2, 3, 4):
            raise ProtocolError(
                "each port entry must be [host_port, container_port(, host_ip(, protocol))]"
            )
        host_port, container_port = entry[0], entry[1]
        host_ip = entry[2] if len(entry) >= 3 else None
        protocol = entry[3] if len(entry) == 4 else "tcp"
        if not isinstance(host_port, int) or not isinstance(container_port, int):
            raise ProtocolError("ports must be integers")
        if host_ip is not None and not isinstance(host_ip, str):
            raise ProtocolError("host_ip must be a string or null")
        if not isinstance(protocol, str):
            raise ProtocolError("protocol must be a string")
        entries.append((host_port, container_port, host_ip, protocol))
    return tuple(entries)


def _decode_forwards(raw: Any) -> tuple[tuple[str, int, str, int], ...] | None:
    if raw is None:
        return None
    if not isinstance(raw, list):
        raise ProtocolError("forwards must be an array")
    out: list[tuple[str, int, str, int]] = []
    for entry in raw:
        if not isinstance(entry, list) or len(entry) != 4:
            raise ProtocolError(
                "each forward must be [container_id, host_port, ip, container_port]"
            )
        container_id, host_port, ip, container_port = entry
        if not (
            isinstance(container_id, str)
            and isinstance(host_port, int)
            and isinstance(ip, str)
            and isinstance(container_port, int)
        ):
            raise ProtocolError("malformed forward entry")
        out.append((container_id, host_port, ip, container_port))
    return tuple(out)


@dataclass(frozen=True)
class PrivNetRequest:
    """A single semantic request. ``network_config`` is only present for
    SETUP_SESSION and is the manager's ``{backend, subnet, vni, mtu}`` — the privnet
    still validates it (untrusted: it arrives via the agent)."""

    op: PrivNetOp
    session_id: str
    container_id: str | None = None
    network_config: dict[str, Any] | None = None
    # Overlay peer/endpoint programming (ADD_PEER/DEL_PEER carry vtep_ip; ADD_ENDPOINT/
    # DEL_ENDPOINT carry ip + mac + vtep_ip). Opaque values the privnet still validates.
    vtep_ip: str | None = None
    ip: str | None = None
    mac: str | None = None
    # ATTACH_CONTAINER only: the LOCAL address a single-node cluster kernel must be PINNED at, so its
    # actual address matches the deterministic /etc/hosts layout the agent wrote (torchrun/MPI bind
    # their rendezvous at their own hostname's address). Distinct from ``ip`` (the multi-node overlay
    # address); a single-node session has no overlay. Opaque — the privnet validates it is within the
    # session's own LOCAL subnet before pinning.
    local_ip: str | None = None
    # PUBLISH_PORTS only: the (host_port, container_port, host_ip, protocol) pairing the agent's port
    # pool produced. host_ip is the interface the service is published on (None = every local
    # address); protocol is "tcp"/"udp"; the DNAT *destination* is never sent — the privnet uses its
    # own assigned LOCAL address (see PrivNetOp.PUBLISH_PORTS), so a compromised agent can pick the
    # publish interface/protocol but not the redirect target.
    ports: tuple[tuple[int, int, str | None, str], ...] | None = None
    # SETUP_DNS_REDIRECT only: the ephemeral loopback port the agent's resolver bound. The redirect
    # destination is fixed to 127.0.0.1:<this> — the agent picks only its own local port, never the
    # host or address.
    dns_port: int | None = None
    # CONFINE_CONTAINER only: the container's top PID and the cgroup limits to write. The PID is
    # checked to belong to the agent's uid before anything is done with it; the limits are the
    # agent's own numbers, exactly as they are when the agent writes the cgroup itself.
    cgroup_pid: int | None = None
    cgroup_limits: dict[str, str] | None = None

    def encode(self) -> bytes:
        payload: dict[str, Any] = {"op": str(self.op), "session_id": self.session_id}
        if self.container_id is not None:
            payload["container_id"] = self.container_id
        if self.network_config is not None:
            payload["network_config"] = self.network_config
        if self.ports is not None:
            payload["ports"] = [list(pair) for pair in self.ports]
        if self.dns_port is not None:
            payload["dns_port"] = self.dns_port
        if self.cgroup_pid is not None:
            payload["cgroup_pid"] = self.cgroup_pid
        if self.cgroup_limits is not None:
            payload["cgroup_limits"] = self.cgroup_limits
        for key in ("vtep_ip", "ip", "mac", "local_ip"):
            value = getattr(self, key)
            if value is not None:
                payload[key] = value
        return json.dumps(payload, separators=(",", ":")).encode() + b"\n"

    @classmethod
    def decode(cls, line: bytes) -> PrivNetRequest:
        try:
            data = json.loads(line)
        except (ValueError, TypeError) as e:
            raise ProtocolError("invalid JSON frame") from e
        if not isinstance(data, dict):
            raise ProtocolError("frame is not an object")
        try:
            op = PrivNetOp(data["op"])
        except (KeyError, ValueError) as e:
            raise ProtocolError("missing or unknown op") from e
        session_id = data.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ProtocolError("missing session_id")
        container_id = data.get("container_id")
        if container_id is not None and not isinstance(container_id, str):
            raise ProtocolError("container_id must be a string")
        network_config = data.get("network_config")
        if network_config is not None and not isinstance(network_config, dict):
            raise ProtocolError("network_config must be an object")
        fields: dict[str, str | None] = {}
        for key in ("vtep_ip", "ip", "mac", "local_ip"):
            value = data.get(key)
            if value is not None and not isinstance(value, str):
                raise ProtocolError(f"{key} must be a string")
            fields[key] = value
        dns_port = data.get("dns_port")
        if dns_port is not None and (not isinstance(dns_port, int) or isinstance(dns_port, bool)):
            raise ProtocolError("dns_port must be an integer")
        cgroup_pid = data.get("cgroup_pid")
        if cgroup_pid is not None and (
            not isinstance(cgroup_pid, int) or isinstance(cgroup_pid, bool) or cgroup_pid <= 1
        ):
            raise ProtocolError("cgroup_pid must be an integer > 1")
        cgroup_limits = data.get("cgroup_limits")
        if cgroup_limits is not None and not (
            isinstance(cgroup_limits, dict)
            and all(isinstance(k, str) and isinstance(v, str) for k, v in cgroup_limits.items())
        ):
            raise ProtocolError("cgroup_limits must be a string map")
        return cls(
            op=op,
            session_id=session_id,
            container_id=container_id,
            network_config=network_config,
            ports=_decode_ports(data.get("ports")),
            dns_port=dns_port,
            cgroup_pid=cgroup_pid,
            cgroup_limits=cgroup_limits,
            **fields,
        )


@dataclass(frozen=True)
class PrivNetResponse:
    """Result of one request. ``assigned`` maps a NetworkRole name to the assigned
    IP (only for ATTACH). ``host_ports`` are the ports UNPUBLISH_PORTS withdrew, so the agent can
    return them to its pool. ``error`` is a short, non-privileged reason string."""

    ok: bool
    assigned: dict[str, str] | None = None
    host_ports: tuple[int, ...] | None = None
    # LIST_PORTS: (container_id, host_port, container_ip, container_port) per published rule.
    forwards: tuple[tuple[str, int, str, int], ...] | None = None
    # LOCAL_SUBNET: the session's node-local LOCAL CIDR, or None when it holds no block.
    subnet: str | None = None
    error: str | None = None

    def encode(self) -> bytes:
        payload: dict[str, Any] = {"ok": self.ok}
        if self.assigned is not None:
            payload["assigned"] = self.assigned
        if self.host_ports is not None:
            payload["host_ports"] = list(self.host_ports)
        if self.forwards is not None:
            payload["forwards"] = [list(f) for f in self.forwards]
        if self.subnet is not None:
            payload["subnet"] = self.subnet
        if self.error is not None:
            payload["error"] = self.error
        return json.dumps(payload, separators=(",", ":")).encode() + b"\n"

    @classmethod
    def decode(cls, line: bytes) -> PrivNetResponse:
        try:
            data = json.loads(line)
        except (ValueError, TypeError) as e:
            raise ProtocolError("invalid JSON frame") from e
        if not isinstance(data, dict) or "ok" not in data:
            raise ProtocolError("malformed response")
        assigned = data.get("assigned")
        if assigned is not None and not isinstance(assigned, dict):
            raise ProtocolError("assigned must be an object")
        raw_ports = data.get("host_ports")
        if raw_ports is not None and not (
            isinstance(raw_ports, list) and all(isinstance(p, int) for p in raw_ports)
        ):
            raise ProtocolError("host_ports must be an array of integers")
        subnet = data.get("subnet")
        if subnet is not None and not isinstance(subnet, str):
            raise ProtocolError("subnet must be a string or null")
        error = data.get("error")
        return cls(
            ok=bool(data["ok"]),
            assigned=assigned,
            host_ports=tuple(raw_ports) if raw_ports is not None else None,
            forwards=_decode_forwards(data.get("forwards")),
            subnet=subnet,
            error=error,
        )
