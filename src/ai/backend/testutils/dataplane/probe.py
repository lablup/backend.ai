"""Reading a running kernel's network state through a ``Node``, for scenarios that assert on it.

Everything here reads from containerd and the kernel's own netns, never from the manager: a
data-plane scenario asks where a kernel's traffic actually goes, which is exactly what a bug makes
the manager's view lie about. Shared by the isolation and cross-node scenarios so neither imports
the other's test module.
"""

from __future__ import annotations

from ai.backend.testutils.dataplane.nodes import Node


async def session_container_ids(node: Node, session_name: str) -> list[str]:
    """Container ids of this node's kernels for a session, from containerd's own labels.

    Read from the runtime rather than the manager: the question a scenario asks is where the kernels
    actually landed, and taking the manager's word for it would assume the answer.
    """
    listing = await node.run(["ctr", "-n", "backend-ai", "containers", "list", "-q"])
    ids: list[str] = []
    for cid in listing.lines:
        info = await node.run(["ctr", "-n", "backend-ai", "containers", "info", cid])
        if session_name in info.stdout:
            ids.append(cid)
    return ids


async def task_pid(node: Node, container_id: str) -> str:
    """The host PID of a container's task -- the handle into its netns for nsenter.

    From ``ctr tasks ls`` rather than a stored value: a task not in the running list has no netns to
    enter, and asserting against a dead kernel would be meaningless.
    """
    listing = await node.run(["ctr", "-n", "backend-ai", "tasks", "ls"])
    for line in listing.lines:
        columns = line.split()
        if len(columns) >= 2 and columns[0] == container_id:
            return columns[1]
    raise AssertionError(f"no running task for container {container_id}:\n{listing.stdout}")


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


async def local_endpoints(node: Node, session_name: str) -> list[tuple[str, str]]:
    """``[(task pid, LOCAL eth0 address)]`` for the session's kernels on this node."""
    return await _endpoints_on(node, session_name, "eth0")


async def overlay_endpoints(node: Node, session_name: str) -> list[tuple[str, str]]:
    """``[(task pid, OVERLAY baimulti0 address)]`` for the session's kernels on this node.

    Empty when none of the session's kernels landed here -- how a cross-node scenario learns which
    node each kernel is on without trusting the manager's placement.
    """
    return await _endpoints_on(node, session_name, "baimulti0")


async def _endpoints_on(node: Node, session_name: str, ifname: str) -> list[tuple[str, str]]:
    endpoints: list[tuple[str, str]] = []
    for container_id in await session_container_ids(node, session_name):
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
