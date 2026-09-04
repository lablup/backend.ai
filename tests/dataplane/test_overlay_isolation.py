"""G15/G16. Cross-session overlay isolation (different VNI).

Two sessions on the vxlan overlay must not reach each other: each is given its own VNI, so their
traffic rides separate L2 segments even when their subnets are carved from the same pool. This is
the multi-tenant guarantee for the overlay -- the analog of the LOCAL cross-session block G10
pins, and what Swarm gives via separate overlay networks. G14 already shows a session reaching
*itself* across nodes; these show it cannot reach *another session*, whether that peer is one bridge
over on the same host (G15) or a vxlan hop away on the other (G16).

Both variants pin placement with ``agent_list`` -- a MULTI_NODE session confined to one agent still
gets an overlay, and pinning makes "co-located" vs "split" deterministic without a capacity-tuned
filler.
"""

from __future__ import annotations

from dataclasses import replace

from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.testutils.dataplane import probe
from ai.backend.testutils.dataplane.guard import LeakGuard
from ai.backend.testutils.dataplane.nodes import Node
from ai.backend.testutils.dataplane.session import SessionDriver, SessionSpec


def _overlay_session(spec: SessionSpec, agent_id: str) -> SessionSpec:
    """A two-kernel MULTI_NODE session pinned to one agent: it gets a VNI and an overlay bridge, and
    the pin fixes where its kernels land so a scenario knows which node to read."""
    return replace(
        spec,
        cpu="1",
        cluster_size=2,
        cluster_mode=ClusterModeEnum.MULTI_NODE,
        agent_list=(agent_id,),
    )


class TestCrossSessionOverlaySameNode:
    async def test_g15_two_overlay_sessions_on_one_node_cannot_reach_each_other(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        session_spec: SessionSpec,
        primary_agent_id: str,
        node: Node,
    ) -> None:
        """Two overlay sessions co-located on one agent; each VNI is its own L2 segment.

        Same node, so the two overlay bridges sit side by side on one host -- the case where a leak
        is most likely, because nothing but the VNI (and the absence of a host route to the other
        subnet) keeps them apart.
        """
        spec = _overlay_session(session_spec, primary_agent_id)
        async with (
            session_driver.session(spec, "dp-g15-a") as a,
            session_driver.session(spec, "dp-g15-b") as b,
        ):
            a_eps = await probe.overlay_endpoints(node, a.name)
            b_eps = await probe.overlay_endpoints(node, b.name)
            assert len(a_eps) == 2 and len(b_eps) == 2, (
                f"expected both sessions' two kernels on {node.name} "
                f"(A={len(a_eps)}, B={len(b_eps)}); the pin to one agent did not hold"
            )
            (pid_a0, ip_a0), (_pid_a1, ip_a1) = a_eps
            (_pid_b0, ip_b0), _ = b_eps

            # Sanity: session A's own kernels reach each other over the overlay, so a "cannot reach
            # the other session" result is isolation and not a dead overlay bridge.
            assert await probe.reaches(node, pid_a0, ip_a1), (
                f"session A's own kernels cannot reach each other over the overlay ({ip_a0} -> "
                f"{ip_a1}); its vxlan bridge is broken and the isolation check would be vacuous"
            )
            # Isolation: A must not reach B's overlay address, and vice versa.
            assert not await probe.reaches(node, pid_a0, ip_b0), (
                f"session A ({ip_a0}) reached session B's overlay address {ip_b0} -- cross-session "
                "overlay leak: the per-session VNI is not isolating the two L2 segments"
            )
            assert not await probe.reaches(node, b_eps[0][0], ip_a0), (
                f"session B ({ip_b0}) reached session A's overlay address {ip_a0} -- cross-session "
                "overlay leak"
            )


class TestCrossSessionOverlayCrossNode:
    async def test_g16_overlay_sessions_on_different_nodes_cannot_reach_each_other(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        session_spec: SessionSpec,
        agent_ids: tuple[str, ...],
        node_pair: tuple[Node, Node],
    ) -> None:
        """One session pinned to each node; a kernel on one host must not reach a different
        session's kernel on the other over the overlay.

        This is the rigorous VNI check: the two sessions' traffic shares the underlay (both encap to
        UDP/4789 between the same two hosts), so only the VNI keeps a frame from one from being
        decapped into the other's bridge. If it leaks, it leaks across the wire.
        """
        n0, n1 = node_pair
        async with (
            session_driver.session(_overlay_session(session_spec, agent_ids[0]), "dp-g16-a") as a,
            session_driver.session(_overlay_session(session_spec, agent_ids[1]), "dp-g16-b") as b,
        ):
            a_eps = await probe.overlay_endpoints(n0, a.name)
            b_eps = await probe.overlay_endpoints(n1, b.name)
            assert a_eps and b_eps, (
                f"the pinned sessions did not land on their nodes (A on {n0.name}={len(a_eps)}, "
                f"B on {n1.name}={len(b_eps)}); cross-node isolation cannot be checked"
            )
            (pid_a, ip_a), *_ = a_eps
            (pid_b, ip_b), *_ = b_eps
            assert not await probe.reaches(n0, pid_a, ip_b), (
                f"a kernel on {n0.name} ({ip_a}) reached a different session's kernel on {n1.name} "
                f"({ip_b}) over the overlay -- VNI isolation failed across the underlay: a frame for "
                "one VNI was decapped into the other's bridge"
            )
            assert not await probe.reaches(n1, pid_b, ip_a), (
                f"a kernel on {n1.name} ({ip_b}) reached a different session's kernel on {n0.name} "
                f"({ip_a}) over the overlay (reverse direction)"
            )
