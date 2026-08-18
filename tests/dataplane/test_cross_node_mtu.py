"""G17/G18. Cross-node overlay data-path integrity, beyond a single ping.

G14 shows one packet crosses the two-host overlay. Necessary, but not sufficient: the faults this
data plane actually ships are the ones a one-byte ping survives.

- **G17 (MTU).** The overlay advertises an MTU (underlay minus vxlan overhead). A frame that fills
  it must cross intact. If the encapsulation pushes the underlay frame past the underlay's own MTU,
  a DF full-size ping is dropped while a small one sails through -- the textbook "ping works, the
  bulk transfer stalls" report. The interface's own MTU is read, so the assertion follows the
  configured value instead of a hard-coded 1450.
- **G18 (sustained).** A stateful underlay fault -- a checksum offload that misfires under load, an
  accelerator that mangles only an *established* flow -- passes the first packet and drops the
  rest. A burst of full-size packets surfaces it; a single ping cannot.

Both reuse G14's placement guard: a MULTI_NODE session the scheduler packed onto one node exercises
no cross-host path, so they skip -- loudly, with the per-node counts -- rather than pass vacuously.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.testutils.dataplane import probe
from ai.backend.testutils.dataplane.guard import LeakGuard
from ai.backend.testutils.dataplane.nodes import Node
from ai.backend.testutils.dataplane.session import SessionDriver, SessionSpec

_OVERLAY_IFNAME = "baimulti0"
_ICMP_V4_OVERHEAD = 28
"""IPv4 header (20) + ICMP echo header (8): payload = MTU - this fills the frame exactly."""
_STREAM_PACKETS = 200
"""Enough of a burst that a load- or flow-state-gated fault has to show, small enough to stay well
inside the per-command time bound."""
_MIN_DELIVERY = 0.95
"""A healthy overlay loses none; the margin only absorbs the odd incidental drop. The faults this
guards against collapse delivery to near zero, so any sane threshold separates them cleanly."""

# (node, task pid, overlay address) for one kernel of the spread session.
_Endpoint = tuple[Node, str, str]


class TestCrossNodeDataPath:
    @pytest.fixture
    def cross_node_spec(self, session_spec: SessionSpec, agent_ids: tuple[str, ...]) -> SessionSpec:
        return replace(
            session_spec,
            cpu="10",
            cluster_size=2,
            cluster_mode=ClusterModeEnum.MULTI_NODE,
            agent_list=agent_ids,
        )

    async def _spread_endpoints(
        self, node_pair: tuple[Node, Node], session_name: str
    ) -> tuple[_Endpoint, _Endpoint]:
        """Resolve one kernel on each node, or skip if the scheduler packed them onto one.

        Same guard as G14: a MULTI_NODE session that landed on a single node exercises no cross-host
        encap->underlay->decap, and asserting on it would pass for the wrong reason.
        """
        per_node = {n.name: await probe.overlay_endpoints(n, session_name) for n in node_pair}
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
        pid_a, ip_a = eps_a[0]
        pid_b, ip_b = eps_b[0]
        assert ip_a != ip_b, (
            f"both kernels were assigned the same overlay address {ip_a}; the manager's central "
            "IPAM handed a colliding IP across nodes and a data-path check is vacuous"
        )
        return (node_by_name[name_a], pid_a, ip_a), (node_by_name[name_b], pid_b, ip_b)

    async def test_g17_a_full_mtu_frame_crosses_the_overlay(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        cross_node_spec: SessionSpec,
        node_pair: tuple[Node, Node],
    ) -> None:
        async with session_driver.session(cross_node_spec, "dp-g17") as handle:
            (node_a, pid_a, ip_a), (node_b, pid_b, ip_b) = await self._spread_endpoints(
                node_pair, handle.name
            )
            mtu = await probe.interface_mtu(node_a, pid_a, _OVERLAY_IFNAME)
            payload = mtu - _ICMP_V4_OVERHEAD

            # A small DF frame first: it proves the overlay is up, so a full-size failure below is
            # unambiguously about size, not an overlay that never came up.
            assert await probe.reaches_at_size(
                node_a, pid_a, ip_b, payload=64, dont_fragment=True
            ), (
                f"{ip_a} cannot reach {ip_b} with even a small frame; the overlay is down and the "
                "full-MTU assertion would be vacuous"
            )
            assert await probe.reaches_at_size(
                node_a, pid_a, ip_b, payload=payload, dont_fragment=True
            ), (
                f"a full-MTU ({mtu}) frame from {ip_a} did not cross to {ip_b} with DF set: the "
                "vxlan encapsulation pushes the underlay frame past the underlay MTU, so a small "
                "ping works but any full-size packet -- and thus any bulk transfer -- is dropped. "
                "The overlay MTU must leave room for the encapsulation overhead on this fabric."
            )
            assert await probe.reaches_at_size(
                node_b, pid_b, ip_a, payload=payload, dont_fragment=True
            ), (
                f"a full-MTU ({mtu}) frame from {ip_b} did not cross to {ip_a} with DF set "
                "(reverse direction)"
            )

    async def test_g18_a_sustained_full_size_stream_is_not_silently_dropped(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        cross_node_spec: SessionSpec,
        node_pair: tuple[Node, Node],
    ) -> None:
        async with session_driver.session(cross_node_spec, "dp-g18") as handle:
            (node_a, pid_a, ip_a), (node_b, pid_b, ip_b) = await self._spread_endpoints(
                node_pair, handle.name
            )
            mtu = await probe.interface_mtu(node_a, pid_a, _OVERLAY_IFNAME)
            payload = mtu - _ICMP_V4_OVERHEAD

            ratio_ab = await probe.delivery_ratio(
                node_a, pid_a, ip_b, count=_STREAM_PACKETS, payload=payload
            )
            assert ratio_ab >= _MIN_DELIVERY, (
                f"only {ratio_ab:.0%} of a {_STREAM_PACKETS}-packet full-size stream from {ip_a} "
                f"reached {ip_b}: a single ping crosses but a sustained flow is dropped -- a "
                "checksum offload misfiring under load, or an underlay accelerator mangling the "
                "established flow. A healthy overlay loses none."
            )
            ratio_ba = await probe.delivery_ratio(
                node_b, pid_b, ip_a, count=_STREAM_PACKETS, payload=payload
            )
            assert ratio_ba >= _MIN_DELIVERY, (
                f"only {ratio_ba:.0%} of a {_STREAM_PACKETS}-packet full-size stream from {ip_b} "
                f"reached {ip_a} (reverse direction)"
            )
