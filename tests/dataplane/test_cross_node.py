"""G14. Cross-node overlay reachability (two nodes).

A MULTI_NODE session's kernels, placed on two different agents, must reach each other over the vxlan
overlay -- the cross-machine data path that replaces Swarm. The LOCAL bridge never leaves a node, so
only the overlay carries inter-node traffic, and only a real second host exercises
encap -> underlay -> decap. This is the two-node counterpart to the single-node isolation scenarios.

Placement is the catch: the concentrated selector packs both kernels onto whichever agent has room,
and a "multi-node" session that landed on one node exercises nothing this scenario is about. Rather
than force a specific placement (which depends on each host's capacity), the test restricts the
session to the pair and skips -- loudly, with the counts -- when the scheduler did not spread, so a
packed run is a clear "give the pair room" message rather than a false failure.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.testutils.dataplane import probe
from ai.backend.testutils.dataplane.guard import LeakGuard
from ai.backend.testutils.dataplane.nodes import Node
from ai.backend.testutils.dataplane.session import SessionDriver, SessionSpec

OVERLAY_IFNAME = "baimulti0"


class TestCrossNodeOverlay:
    @pytest.fixture
    def cross_node_spec(self, session_spec: SessionSpec, agent_ids: tuple[str, ...]) -> SessionSpec:
        return replace(
            session_spec,
            cpu="10",
            cluster_size=2,
            cluster_mode=ClusterModeEnum.MULTI_NODE,
            agent_list=agent_ids,
        )

    async def test_g14_kernels_on_two_nodes_reach_each_other_over_the_overlay(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        cross_node_spec: SessionSpec,
        node_pair: tuple[Node, Node],
    ) -> None:
        async with session_driver.session(cross_node_spec, "dp-g14") as handle:
            per_node = {n.name: await _overlay_endpoints(n, handle.name) for n in node_pair}
            occupied = {name: eps for name, eps in per_node.items() if eps}
            if len(occupied) < 2:
                pytest.skip(
                    "the MULTI_NODE session was not spread across both agents (kernels per node: "
                    f"{ {name: len(eps) for name, eps in per_node.items()} }); the concentrated "
                    "selector packed it onto one. Run against a scaling group where each of the two "
                    "agents has room for exactly one kernel so the scheduler must place one on each."
                )
            node_by_name = {n.name: n for n in node_pair}
            (name_a, eps_a), (name_b, eps_b) = list(occupied.items())
            node_a, (pid_a, ip_a) = node_by_name[name_a], eps_a[0]
            node_b, (pid_b, ip_b) = node_by_name[name_b], eps_b[0]
            assert ip_a != ip_b, (
                f"both kernels were assigned the same overlay address {ip_a}; the manager's central "
                "IPAM handed a colliding IP across nodes and a reachability check is vacuous"
            )

            # Cross-node overlay, both directions: encap on one host, decap on the other.
            assert await probe.reaches(node_a, pid_a, ip_b), (
                f"the kernel on {name_a} ({ip_a}) cannot reach its peer on {name_b} ({ip_b}) over "
                "the overlay: the vxlan tunnel between the two hosts is not carrying traffic (an "
                "unpublished/unusable VTEP, FDB+ARP not programmed from the endpoints table, or the "
                "underlay dropping UDP/4789)"
            )
            assert await probe.reaches(node_b, pid_b, ip_a), (
                f"the kernel on {name_b} ({ip_b}) cannot reach its peer on {name_a} ({ip_a}) over "
                "the overlay (reverse direction)"
            )


async def _overlay_endpoints(node: Node, session_name: str) -> list[tuple[str, str]]:
    """``[(pid, overlay ip)]`` for the session's kernels on this node (empty if none landed here)."""
    endpoints: list[tuple[str, str]] = []
    for container_id in await probe.session_container_ids(node, session_name):
        pid = await probe.task_pid(node, container_id)
        endpoints.append((pid, await probe.interface_address(node, pid, OVERLAY_IFNAME)))
    return endpoints
