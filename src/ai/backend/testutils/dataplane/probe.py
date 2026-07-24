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
