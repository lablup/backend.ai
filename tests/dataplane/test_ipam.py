"""G17. Central endpoint IPAM and proactive FDB programming (P9).

Overlay endpoint IPs are assigned centrally by the manager, one per kernel, not agent-locally: two
nodes running host-local IPAM would each hand out the first address of the stretched subnet and
collide (verification.md caught exactly this). And because the manager knows every endpoint's
IP->VTEP, the coordinators pre-program the FDB from the ``endpoints/`` table, so known unicast never
floods -- Swarm's gossip-programmed neighbour tables, done from etcd.

This pins both halves: the two kernels get disjoint IPs (always checkable), and, when they land on
two nodes, each host has the peer's MAC pointed at the peer's VTEP (a real cross-node run only).
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.common.network.types import mac_for_ip
from ai.backend.testutils.dataplane import probe
from ai.backend.testutils.dataplane.guard import LeakGuard
from ai.backend.testutils.dataplane.nodes import Node
from ai.backend.testutils.dataplane.session import SessionDriver, SessionSpec


class TestCentralIpam:
    @pytest.fixture
    def multi_node_spec(self, session_spec: SessionSpec, agent_ids: tuple[str, ...]) -> SessionSpec:
        return replace(
            session_spec,
            cpu="10",
            cluster_size=2,
            cluster_mode=ClusterModeEnum.MULTI_NODE,
            agent_list=agent_ids,
        )

    async def test_g17_endpoints_get_disjoint_ips_and_a_peer_fdb_across_nodes(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        multi_node_spec: SessionSpec,
        node_pair: tuple[Node, Node],
    ) -> None:
        async with session_driver.session(multi_node_spec, "dp-g17") as handle:
            per_node = {n: await probe.overlay_endpoints(n, handle.name) for n in node_pair}
            all_ips = [ip for eps in per_node.values() for _pid, ip in eps]
            assert len(all_ips) == 2, (
                f"expected two overlay endpoints for the session, found {len(all_ips)}: {all_ips}"
            )

            # Disjoint IPs: the whole reason IPAM is central. Two nodes with host-local IPAM would
            # both allocate the subnet's first address; a single authority guarantees they differ.
            assert all_ips[0] != all_ips[1], (
                f"both endpoints were assigned the same overlay IP {all_ips[0]} -- the manager did "
                "not allocate centrally, or two nodes ran host-local IPAM and collided"
            )

            occupied = {n: eps for n, eps in per_node.items() if eps}
            if len(occupied) < 2:
                pytest.skip(
                    "the session was not spread across both nodes (endpoints per node: "
                    f"{ {n.name: len(eps) for n, eps in per_node.items()} }); the FDB-programming "
                    "half needs a remote peer. Give the pair room so the scheduler places one on "
                    "each (the disjoint-IP half above already ran)."
                )

            # Proactive FDB: on each host, the *other* node's endpoint MAC must point at that node's
            # VTEP -- programmed from the endpoints table before any traffic, so unicast never floods.
            (node_a, eps_a), (node_b, eps_b) = list(occupied.items())
            _pid_a, ip_a = eps_a[0]
            _pid_b, ip_b = eps_b[0]
            assert await probe.fdb_has_remote(node_a, mac_for_ip(ip_b)), (
                f"{node_a.name} has no FDB entry sending the peer {ip_b}'s MAC "
                f"({mac_for_ip(ip_b)}) to its VTEP; the coordinator did not program the endpoints "
                "table proactively, so that peer would only be reachable by BUM flooding"
            )
            assert await probe.fdb_has_remote(node_b, mac_for_ip(ip_a)), (
                f"{node_b.name} has no FDB entry for the peer {ip_a}'s MAC ({mac_for_ip(ip_a)})"
            )
