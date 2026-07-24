"""G10. Cross-session isolation on one node.

Two different sessions co-located on one agent must not reach each other over the LOCAL (egress)
bridge. Overlay isolation is VNI-based and holds by construction; the LOCAL bridge is where it does
NOT -- a per-session bridge does not isolate on its own, because with ``ip_forward=1`` (on for NAT
egress) the host L3-routes between the sessions' /26s. A live two-node run surfaced exactly this
(master Decision Log 2026-07-24): under the old blanket ``-i/-o bridge -j ACCEPT`` a kernel in one
session reached another session's LOCAL address. The fix mirrors Docker -- accept only egress to
the uplink, its established return, and intra-bridge; drop everything else destined to a bridge.

This is the scenario that would have caught that leak, and the one that pins the fix against a
regression. Single-node -- two sessions on one agent -- so it needs no second node.
"""

from __future__ import annotations

from ai.backend.testutils.dataplane.guard import LeakGuard
from ai.backend.testutils.dataplane.nodes import Node
from ai.backend.testutils.dataplane.session import SessionDriver, SessionSpec


class TestCrossSessionIsolation:
    async def test_g10_two_sessions_on_one_node_cannot_reach_each_other_over_local(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        session_spec: SessionSpec,
        node: Node,
    ) -> None:
        """Two single-node sessions on one agent; assert cross-session LOCAL is blocked both ways.

        The `leak_guard` fixture doubles the value: it baselines before and asserts back-to-baseline
        after, so this also proves the two sessions' bridges, iptables rules, and IPAM claims are
        fully torn down -- a cross-session rule left behind would be its own leak.
        """
        async with (
            session_driver.session(session_spec, "dp-g10-a") as a,
            session_driver.session(session_spec, "dp-g10-b") as b,
        ):
            pid_a, ip_a, gw_a = await _local_endpoint(node, a.name)
            pid_b, ip_b, gw_b = await _local_endpoint(node, b.name)
            assert ip_a != ip_b, (
                f"both sessions were handed the same LOCAL address {ip_a}; the per-session block "
                "allocation collided, and an isolation check between identical addresses is vacuous"
            )

            # Sanity first: each kernel's LOCAL interface is live -- it reaches its own gateway (the
            # host). Without this, a "cannot reach the peer" result is indistinguishable from a
            # kernel whose network never came up, and the isolation assertions would pass for the
            # wrong reason.
            assert await _reaches(node, pid_a, gw_a), (
                f"session A ({ip_a}) cannot reach its own LOCAL gateway {gw_a}: its networking did "
                "not come up, so the isolation check below would be vacuous"
            )
            assert await _reaches(node, pid_b, gw_b), (
                f"session B ({ip_b}) cannot reach its own LOCAL gateway {gw_b}: ditto"
            )

            # The actual isolation, both directions: neither session reaches the other over LOCAL.
            assert not await _reaches(node, pid_a, ip_b), (
                f"session A reached session B's LOCAL address {ip_b} -- cross-session LOCAL leak: "
                "the host is L3-routing between the per-session bridges and the FORWARD isolation "
                "rules are missing or too broad (see native_attacher._forward_accept_rules)"
            )
            assert not await _reaches(node, pid_b, ip_a), (
                f"session B reached session A's LOCAL address {ip_a} -- cross-session LOCAL leak"
            )


async def _local_endpoint(node: Node, session_name: str) -> tuple[str, str, str]:
    """``(task pid, LOCAL eth0 address, LOCAL gateway)`` for a single-node session's one kernel.

    Read from containerd and the kernel's own netns, never the manager: the question is where the
    kernel's traffic actually goes, which is exactly what a leak would make the manager's view lie
    about.
    """
    container_id = await _sole_container_id(node, session_name)
    pid = await _task_pid(node, container_id)
    addr = await node.run(["nsenter", "-t", pid, "-n", "ip", "-o", "-4", "addr", "show", "eth0"])
    route = await node.run([
        "nsenter",
        "-t",
        pid,
        "-n",
        "ip",
        "-o",
        "-4",
        "route",
        "show",
        "default",
    ])
    return pid, _inet_addr(addr.stdout), _default_gateway(route.stdout)


async def _sole_container_id(node: Node, session_name: str) -> str:
    ids = await _session_container_ids(node, session_name)
    assert len(ids) == 1, (
        f"expected exactly one kernel for {session_name} on this node, found {len(ids)}: {ids}"
    )
    return ids[0]


async def _session_container_ids(node: Node, session_name: str) -> list[str]:
    """Container ids of this node's kernels for a session, from containerd's own labels.

    The same ground-truth read as the cluster scenario: taking the manager's placement on faith
    would assume the answer the scenario exists to check.
    """
    listing = await node.run(["ctr", "-n", "backend-ai", "containers", "list", "-q"])
    ids: list[str] = []
    for cid in listing.lines:
        info = await node.run(["ctr", "-n", "backend-ai", "containers", "info", cid])
        if session_name in info.stdout:
            ids.append(cid)
    return ids


async def _task_pid(node: Node, container_id: str) -> str:
    """The host PID of a container's task -- the handle into its netns for nsenter.

    From ``ctr tasks ls`` rather than a stored value: a task that is not in the running list has no
    netns to enter, and asserting isolation against a dead kernel would be meaningless.
    """
    listing = await node.run(["ctr", "-n", "backend-ai", "tasks", "ls"])
    for line in listing.lines:
        columns = line.split()
        if len(columns) >= 2 and columns[0] == container_id:
            return columns[1]
    raise AssertionError(f"no running task for container {container_id}:\n{listing.stdout}")


async def _reaches(node: Node, pid: str, target: str) -> bool:
    """Can the container at ``pid`` reach ``target``? One bounded ping from inside its netns.

    ``nsenter`` (not an in-container exec) because the ping traverses the very host FORWARD path the
    isolation rules live on, and the host always has ``ping`` while a minimal image may not.
    """
    result = await node.run(
        ["nsenter", "-t", pid, "-n", "ping", "-c", "1", "-W", "2", target], check=False
    )
    return result.returncode == 0


def _inet_addr(ip_output: str) -> str:
    """The IPv4 address from an ``ip -o -4 addr show`` line (``... inet 172.30.0.2/26 ...``)."""
    tokens = ip_output.split()
    if "inet" in tokens:
        return tokens[tokens.index("inet") + 1].split("/")[0]
    raise AssertionError(f"no IPv4 address on the LOCAL interface: {ip_output!r}")


def _default_gateway(route_output: str) -> str:
    """The gateway from an ``ip -o -4 route show default`` line (``default via 172.30.0.1 ...``)."""
    tokens = route_output.split()
    if "via" in tokens:
        return tokens[tokens.index("via") + 1]
    raise AssertionError(f"no default gateway on the LOCAL interface: {route_output!r}")
