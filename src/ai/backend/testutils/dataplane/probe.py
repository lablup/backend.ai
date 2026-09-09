"""Reading a running kernel's network state through a ``Node``, for scenarios that assert on it.

Everything here reads from containerd and the kernel's own netns, never from the manager: a
data-plane scenario asks where a kernel's traffic actually goes, which is exactly what a bug makes
the manager's view lie about. Shared by the isolation and cross-node scenarios so neither imports
the other's test module.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from uuid import UUID

from ai.backend.testutils.dataplane.nodes import CommandResult, Node


@runtime_checkable
class SessionRef(Protocol):
    """What a scenario holds for a running session. `SessionHandle` satisfies it."""

    @property
    def session_id(self) -> UUID: ...

    @property
    def name(self) -> str: ...


def _tokens(session: SessionRef | str) -> tuple[str, ...]:
    """The strings a runtime record might carry for this session.

    Both, because the two runtimes record different ones: containerd's record carries the session
    name, and a Docker container's label carries only the id. Passing one of them and searching for
    it is how a scenario ended up asserting against a node it had found no containers on -- and
    reporting it as a placement failure, which it was not.
    """
    if isinstance(session, str):
        return (session,)
    return (str(session.session_id), session.name)


async def session_container_ids(node: Node, session: SessionRef | str) -> list[str]:
    """Container ids of this node's kernels for a session, from the runtime's own labels.

    Read from the runtime rather than the manager: the question a scenario asks is where the kernels
    actually landed, and taking the manager's word for it would assume the answer.

    Both runtimes, because a node runs one or the other and the scenarios do not care which.
    """
    tokens = _tokens(session)
    ids = await _containerd_session_containers(node, tokens)
    if ids:
        return ids
    return await _docker_session_containers(node, tokens)


async def _containerd_session_containers(node: Node, tokens: tuple[str, ...]) -> list[str]:
    listing = await node.run(["ctr", "-n", "backend-ai", "containers", "list", "-q"], check=False)
    ids: list[str] = []
    for cid in listing.lines:
        info = await node.run(["ctr", "-n", "backend-ai", "containers", "info", cid], check=False)
        if any(token in info.stdout for token in tokens):
            ids.append(cid)
    return ids


async def _docker_session_containers(node: Node, tokens: tuple[str, ...]) -> list[str]:
    listing = await node.run(
        ["docker", "ps", "-q", "--filter", "label=ai.backend.session-id"], check=False
    )
    ids: list[str] = []
    for cid in listing.lines:
        info = await node.run(
            ["docker", "inspect", "--format", "{{json .Config.Labels}}", cid], check=False
        )
        if any(token in info.stdout for token in tokens):
            ids.append(cid)
    return ids


async def task_pid(node: Node, container_id: str) -> str:
    """The host PID of a container's task -- the handle into its netns for nsenter.

    From the runtime's running list rather than a stored value: a task not in it has no netns to
    enter, and asserting against a dead kernel would be meaningless.
    """
    listing = await node.run(["ctr", "-n", "backend-ai", "tasks", "ls"], check=False)
    for line in listing.lines:
        columns = line.split()
        if len(columns) >= 2 and columns[0] == container_id:
            return columns[1]
    docker = await node.run(
        ["docker", "inspect", "--format", "{{.State.Pid}}", container_id], check=False
    )
    pid = docker.stdout.strip()
    if pid.isdigit() and pid != "0":
        return pid
    raise AssertionError(f"no running task for container {container_id}:\n{listing.stdout}")


async def _exec_in_container(
    node: Node, container_id: str, argv: Sequence[str], *, exec_tag: str, check: bool = True
) -> CommandResult:
    """Run ``argv`` inside the container, through whichever runtime owns it.

    Inside, not merely in its netns: a name lookup has to read the container's own
    ``/etc/resolv.conf``, and ``nsenter -n`` would leave it reading the host's.
    """
    docker = await node.run(["docker", "inspect", container_id], check=False)
    if docker.returncode == 0:
        return await node.run(["docker", "exec", container_id, *argv], check=check)
    return await node.run(
        [
            "ctr",
            "-n",
            "backend-ai",
            "tasks",
            "exec",
            "--exec-id",
            f"dp-{exec_tag}-{abs(hash(exec_tag)) % 100000}",
            container_id,
            *argv,
        ],
        check=check,
    )


async def read_container_file(node: Node, container_id: str, path: str) -> str:
    """Read a file through the runtime that owns ``container_id``."""
    result = await _exec_in_container(node, container_id, ["cat", path], exec_tag=f"read{path}")
    return result.stdout


async def resolves_in_container(node: Node, container_id: str, hostname: str) -> bool:
    """Does ``hostname`` resolve from inside the kernel, the way its runner resolves peers?

    The peer map left ``/etc/hosts`` in f51f3d6038 (resolver-only peer names), so reading that
    file answers a question nothing asks any more. Resolution is the contract: the session's
    cluster resolver for containerd, dockerd's embedded DNS for Docker — and ``getent hosts``
    goes through whichever of them the container is pointed at.
    """
    result = await _exec_in_container(
        node,
        container_id,
        ["getent", "hosts", hostname],
        exec_tag=f"resolve{hostname}",
        check=False,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


async def interface_address(node: Node, pid: str, ifname: str) -> str:
    """The IPv4 address of one interface inside a kernel's netns (``eth0`` LOCAL, ``baimulti0``
    OVERLAY)."""
    out = await node.run(["nsenter", "-t", pid, "-n", "ip", "-o", "-4", "addr", "show", ifname])
    tokens = out.stdout.split()
    if "inet" in tokens:
        return tokens[tokens.index("inet") + 1].split("/")[0]
    raise AssertionError(f"no IPv4 address on {ifname} in pid {pid}: {out.stdout!r}")


async def default_gateway(node: Node, pid: str) -> str:
    """The default gateway inside a kernel's netns (its LOCAL bridge, i.e. the host)."""
    out = await node.run(["nsenter", "-t", pid, "-n", "ip", "-o", "-4", "route", "show", "default"])
    tokens = out.stdout.split()
    if "via" in tokens:
        return tokens[tokens.index("via") + 1]
    raise AssertionError(f"no default gateway in pid {pid}: {out.stdout!r}")


async def local_endpoints(node: Node, session: SessionRef | str) -> list[tuple[str, str]]:
    """``[(task pid, LOCAL eth0 address)]`` for the session's kernels on this node."""
    return await _endpoints_on(node, session, "eth0")


async def overlay_endpoints(node: Node, session: SessionRef | str) -> list[tuple[str, str]]:
    """``[(task pid, OVERLAY baimulti0 address)]`` for the session's kernels on this node.

    Empty when none of the session's kernels landed here -- how a cross-node scenario learns which
    node each kernel is on without trusting the manager's placement.
    """
    return await _endpoints_on(node, session, "baimulti0")


async def _endpoints_on(
    node: Node, session: SessionRef | str, ifname: str
) -> list[tuple[str, str]]:
    endpoints: list[tuple[str, str]] = []
    for container_id in await session_container_ids(node, session):
        pid = await task_pid(node, container_id)
        endpoints.append((pid, await interface_address(node, pid, ifname)))
    return endpoints


async def fdb_has_remote(node: Node, mac: str) -> bool:
    """Whether the host has a unicast FDB entry sending ``mac`` to a remote VTEP (a ``dst`` on a
    vxlan device).

    This is the proactive MAC->VTEP programming the coordinator does from the manager's endpoints
    table, so known unicast reaches its host directly instead of flooding every peer -- Swarm's
    gossip-programmed neighbour tables, done from etcd.
    """
    out = await node.run(["bridge", "fdb", "show"])
    return any(line.lower().startswith(mac.lower()) and " dst " in line for line in out.lines)


async def reaches(node: Node, pid: str, target: str) -> bool:
    """Can the container at ``pid`` reach ``target``? One bounded ping from inside its netns.

    ``nsenter`` (not an in-container exec) because the packet traverses the very host FORWARD/overlay
    path under test, and the host always has ``ping`` while a minimal image may not.
    """
    result = await node.run(
        ["nsenter", "-t", pid, "-n", "ping", "-c", "1", "-W", "2", target], check=False
    )
    return result.returncode == 0


async def interface_mtu(node: Node, pid: str, ifname: str) -> int:
    """The MTU of one interface inside a kernel's netns.

    The overlay's MTU is the underlay's minus the vxlan overhead; a scenario that asserts a full-MTU
    frame crosses reads the number the interface actually carries rather than hard-coding 1450, so a
    future MTU change moves the assertion with it instead of quietly making it test the wrong size.
    """
    out = await node.run(["nsenter", "-t", pid, "-n", "ip", "-o", "link", "show", ifname])
    tokens = out.stdout.split()
    if "mtu" in tokens:
        return int(tokens[tokens.index("mtu") + 1])
    raise AssertionError(f"no mtu on {ifname} in pid {pid}: {out.stdout!r}")


async def reaches_at_size(
    node: Node, pid: str, target: str, *, payload: int, dont_fragment: bool = False
) -> bool:
    """Can ``pid`` reach ``target`` with an ICMP payload of ``payload`` bytes?

    A minimal ping rides whatever small path a broken underlay still passes; a full-MTU frame is the
    one that must survive encapsulation intact. ``dont_fragment`` sets DF, so a frame the overlay
    advertises but whose encapsulation exceeds the underlay MTU is dropped here instead of being
    silently fragmented -- the misconfiguration a plain reachability check sails straight through.
    """
    argv = ["nsenter", "-t", pid, "-n", "ping", "-c", "1", "-W", "2", "-s", str(payload)]
    if dont_fragment:
        argv += ["-M", "do"]
    argv.append(target)
    result = await node.run(argv, check=False)
    return result.returncode == 0


def _received_fraction(ping_stdout: str) -> float:
    """Parse ``N packets transmitted, M received`` from ping's summary into ``M / N``.

    Raises rather than defaulting: an unparsed summary is a harness fault, and either a 0.0 or a 1.0
    default would silently turn it into a fail or a pass of the wrong test -- the empty-snapshot
    failure mode the suite forbids, in miniature.
    """
    for line in ping_stdout.splitlines():
        if "packets transmitted" in line and "received" in line:
            fields = line.replace(",", " ").split()
            transmitted = int(fields[0])
            received = int(fields[fields.index("received") - 1])
            if transmitted == 0:
                raise AssertionError(f"ping reported zero packets transmitted: {line!r}")
            return received / transmitted
    raise AssertionError(f"no ping summary line to parse:\n{ping_stdout}")


async def delivery_ratio(
    node: Node, pid: str, target: str, *, count: int, payload: int, interval: float = 0.02
) -> float:
    """Fraction of a ``count``-packet, ``payload``-byte stream that makes the round trip.

    A single ping can ride the first-packet path a broken underlay still passes -- a stateful
    accelerator that mangles only an established flow, a checksum offload that misfires under load.
    A sustained stream of full-size packets is what such a fault actually drops, so the caller
    asserts the ratio is ~1.0: a healthy overlay loses none.
    """
    result = await node.run(
        [
            "nsenter",
            "-t",
            pid,
            "-n",
            "ping",
            "-c",
            str(count),
            "-i",
            str(interval),
            "-W",
            "2",
            "-s",
            str(payload),
            target,
        ],
        check=False,
    )
    return _received_fraction(result.stdout)


async def vtep_interface(node: Node, vtep_ip: str) -> str:
    """The interface that holds ``vtep_ip`` on this node.

    Deliberately not a route lookup. A node with a second default route -- a laptop with both
    Ethernet and Wi-Fi up, which is exactly what one of the nodes here is -- answers
    ``ip route get`` with the wrong one, and a capture on it records nothing while the tunnel is
    busy on the other. The backend picks its uplink the same way, from the address.
    """
    result = await node.run(["ip", "-o", "-4", "addr", "show"])
    for line in result.stdout.splitlines():
        tokens = line.split()
        if len(tokens) >= 4 and tokens[3].split("/")[0] == vtep_ip:
            return tokens[1]
    raise AssertionError(f"no interface on {node.name} holds {vtep_ip}")


@dataclass(frozen=True)
class UnderlayCapture:
    """What a node saw on the wire for one VXLAN port."""

    esp: int
    plaintext: int

    @property
    def is_encrypted_only(self) -> bool:
        return self.esp > 0 and self.plaintext == 0


async def capture_underlay(
    node: Node,
    iface: str,
    generate: Callable[[], Awaitable[None]],
    *,
    port: int = 4789,
    seconds: int = 12,
) -> UnderlayCapture:
    """Count ESP against plaintext VXLAN on ``iface`` while ``generate`` runs.

    tcpdump only flushes its buffer when it exits, so the capture is read after waiting out the
    whole window rather than as soon as the traffic stops -- reading early reports zero of both
    and looks exactly like a dead tunnel.
    """
    path = "/tmp/bai-dataplane-underlay.pcap"
    await node.run(["sudo", "-n", "rm", "-f", path], check=False)
    await node.run([
        "sudo", "-n", "sh", "-c",
        f"nohup timeout {seconds} tcpdump -ni {iface} -w {path} "
        f"'esp or (udp port {port})' >/dev/null 2>&1 &",
    ])  # fmt: skip
    await asyncio.sleep(2)
    await generate()
    await asyncio.sleep(seconds)
    esp = await node.run(["sudo", "-n", "tcpdump", "-nr", path, "esp"], check=False)
    plain = await node.run(["sudo", "-n", "tcpdump", "-nr", path, f"udp port {port}"], check=False)
    await node.run(["sudo", "-n", "rm", "-f", path], check=False)
    return UnderlayCapture(
        esp=len([line for line in esp.stdout.splitlines() if line.strip()]),
        plaintext=len([line for line in plain.stdout.splitlines() if line.strip()]),
    )


async def iptables_rules(node: Node, table: str, chain: str) -> list[str]:
    result = await node.run(["sudo", "-n", "iptables", "-t", table, "-S", chain], check=False)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


async def jump_position(node: Node, table: str, builtin: str, chain: str) -> int | None:
    """1-based index of the jump to ``chain`` within ``builtin``, or None when it is absent.

    Position, not presence: an ACCEPT above the jump bypasses the chain while ``iptables -C``
    still reports it there.
    """
    index = 0
    for line in await iptables_rules(node, table, builtin):
        tokens = line.split()
        if not tokens or tokens[0] != "-A" or tokens[1] != builtin:
            continue
        index += 1
        if tokens[-2:] == ["-j", chain]:
            return index
    return None
