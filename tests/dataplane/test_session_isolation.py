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

from dataclasses import replace

import pytest

from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.testutils.dataplane.guard import LeakGuard
from ai.backend.testutils.dataplane.nodes import Node
from ai.backend.testutils.dataplane.session import SessionDriver, SessionSpec, unique_name


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


class TestIntraSessionReachability:
    """A single-node cluster's kernels must reach each other over LOCAL.

    The isolation that blocks cross-session traffic must not also block a session from itself: a
    single-node cluster has no overlay, so its kernels talk over the one LOCAL bridge, and the
    ``-i bridge -o bridge -j ACCEPT`` rule is what keeps that working. A DROP one token too broad
    would strand a torchrun cluster exactly as surely as the cross-session leak let strangers in --
    the two failures are opposite edges of the same rule, so they are worth pinning together.
    """

    @pytest.fixture
    def cluster_spec(self, session_spec: SessionSpec) -> SessionSpec:
        return replace(session_spec, cluster_size=2, cluster_mode=ClusterModeEnum.SINGLE_NODE)

    async def test_g11_same_session_kernels_reach_each_other_over_local(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        cluster_spec: SessionSpec,
        node: Node,
    ) -> None:
        async with session_driver.session(cluster_spec, "dp-g11") as handle:
            container_ids = await _session_container_ids(node, handle.name)
            assert len(container_ids) == 2, (
                f"expected two kernels for the cluster session on this node, found "
                f"{len(container_ids)}; a single-node cluster must not be spread"
            )
            endpoints = [await _endpoint_of(node, cid) for cid in container_ids]
            (pid0, ip0, _), (pid1, ip1, _) = endpoints
            assert await _reaches(node, pid0, ip1) and await _reaches(node, pid1, ip0), (
                f"the two kernels of one session cannot reach each other over LOCAL "
                f"({ip0} <-> {ip1}); the intra-bridge FORWARD accept is missing or the isolation "
                "DROP is too broad -- a single-node cluster would be stranded"
            )


class TestNoCollateralOnTeardown:
    """Tearing down one session must not touch a co-located one.

    The LOCAL bridges are named per session, but the FORWARD rules and the IPAM store are shared
    host state; a teardown that deleted by the wrong key would take a neighbour's bridge or rule
    with it. `guard.py` calls this *collateral* and rates it worse than a leak -- a running session
    silently loses its network. This asserts it functionally: the session we keep still reaches its
    own gateway after its neighbour is destroyed.
    """

    async def test_g12_a_neighbours_teardown_leaves_this_session_intact(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        session_spec: SessionSpec,
        node: Node,
    ) -> None:
        async with session_driver.session(session_spec, "dp-g12-keep") as keep:
            pid, ip, gw = await _local_endpoint(node, keep.name)
            assert await _reaches(node, pid, gw), (
                f"the session under test ({ip}) could not reach its gateway {gw} even before a "
                "neighbour was involved; the collateral check below would be vacuous"
            )
            victim = await session_driver.create(session_spec, "dp-g12-victim")
            await session_driver.destroy(victim.session_id)
            assert await _reaches(node, pid, gw), (
                f"tearing down a co-located session broke this one's LOCAL networking ({ip} can no "
                f"longer reach {gw}): the victim's teardown deleted a device or rule that was not "
                "its own (collateral)"
            )


class TestRepeatedLifecycleLeavesNoResidue:
    """Create-and-destroy, several times over, must return the host to baseline.

    A leak of one rule or one IPAM claim per teardown is caught by a single create/destroy already
    -- but so is nothing subtler. Cycling turns a per-teardown residue into an accumulation, and
    catches the failure a one-shot misses: a bridge index claimed but never released, so a later
    session lands on a subnet an earlier one still 'owns'. The assertion is the `leak_guard`
    fixture's own -- it baselined before the first cycle and asserts back-to-baseline after the last.
    """

    async def test_g13_three_cycles_leave_no_bridge_rule_or_claim_behind(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        session_spec: SessionSpec,
    ) -> None:
        for cycle in range(3):
            handle = await session_driver.create(
                session_spec, unique_name("dp-g13", suffix=str(cycle))
            )
            await session_driver.destroy(handle.session_id)


async def _local_endpoint(node: Node, session_name: str) -> tuple[str, str, str]:
    """``(task pid, LOCAL eth0 address, LOCAL gateway)`` for a single-node session's one kernel."""
    return await _endpoint_of(node, await _sole_container_id(node, session_name))


async def _endpoint_of(node: Node, container_id: str) -> tuple[str, str, str]:
    """``(task pid, LOCAL eth0 address, LOCAL gateway)`` for one kernel container.

    Read from containerd and the kernel's own netns, never the manager: the question is where the
    kernel's traffic actually goes, which is exactly what a leak would make the manager's view lie
    about.
    """
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
