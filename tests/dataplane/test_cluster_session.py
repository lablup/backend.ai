"""G9. Single-node cluster session.

The rest of group G needs two nodes. This one does not, and it is the highest-density defect area
in the branch's history: a cluster session whose kernels all land on one agent takes a completely
different path from the two-node case. Peers are laid out deterministically inside the node's own
/26 block rather than on a stretched overlay, and `/etc/hosts` is written from that layout. M6
produced at least five defects here, including one that made a torchrun master bind to loopback
so no worker could reach it.

Verified live in privnet mode (2026-07-23): it caught BUG6 — ``_peer_host_map`` compared the
cluster mode with ``is not ClusterMode.SINGLE_NODE`` against a value that arrives over RPC as a
plain string, so the identity check was always true and peer resolution was skipped for every
single-node cluster, in both privnet and in-process mode. With that fixed, all three kernels
resolve every peer at the node-local /26 the privnet assigned, and none pins its own name to
loopback.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.testutils.dataplane import probe
from ai.backend.testutils.dataplane.guard import LeakGuard
from ai.backend.testutils.dataplane.nodes import Node
from ai.backend.testutils.dataplane.session import SessionDriver, SessionSpec

CLUSTER_SIZE = 3


@pytest.fixture
def single_node_cluster_spec(session_spec: SessionSpec, primary_agent_id: str) -> SessionSpec:
    """Pinned to the node this scenario reads. Unpinned, the scheduler is free to place it
    anywhere in the resource group, and the read finds no kernel -- reported as "a single-node
    cluster session must not be spread", which is not what happened."""
    return replace(
        session_spec,
        cluster_size=CLUSTER_SIZE,
        cluster_mode=ClusterModeEnum.SINGLE_NODE,
        agent_list=(primary_agent_id,),
    )


async def _read_in_kernel(node: Node, container_id: str, path: str) -> str:
    """Read the file as seen inside the kernel, through its owning runtime."""
    return await probe.read_container_file(node, container_id, path)


class TestSingleNodeClusterSession:
    async def test_g9_peers_resolve_and_every_kernel_sees_the_whole_cluster(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        single_node_cluster_spec: SessionSpec,
        node: Node,
    ) -> None:
        """Three things at once, because they share one root cause when they break.

        Every peer must *resolve* from inside every kernel, and no kernel's own hostname may be
        rewritten to a loopback address -- that rewrite is what stranded torchrun. Resolution, not
        `/etc/hosts`: f51f3d6038 dropped the peer map in favour of the per-session resolver
        (dockerd's embedded DNS on the Docker backend), so the file names only localhost and the
        kernel itself, and asserting on its contents tests a contract that no longer exists.
        `BACKENDAI_CLUSTER_HOSTS` must agree across kernels, since the manager generates it once
        per session and a kernel that disagrees is reading a locally-derived copy. And the
        addresses must be the node-local block's, not an overlay's.
        """
        async with session_driver.session(single_node_cluster_spec, "dp-g9") as handle:
            container_ids = await probe.session_container_ids(node, handle)
            assert len(container_ids) == CLUSTER_SIZE, (
                f"expected {CLUSTER_SIZE} kernels on this node, found {len(container_ids)}; "
                "a single-node cluster session must not be spread"
            )

            environs = {
                cid: await _read_in_kernel(node, cid, "/proc/1/environ") for cid in container_ids
            }
            # The peer names to expect come from BACKENDAI_CLUSTER_HOSTS itself, not a hard-coded
            # guess: the manager decides the naming (main1/sub1/sub2), and a test that hard-coded
            # "main" would pass by substring luck against "main1" while missing a truly absent peer.
            cluster_hosts_values = {
                _env_value(e, "BACKENDAI_CLUSTER_HOSTS") for e in environs.values()
            }
            assert len(cluster_hosts_values) == 1, (
                "kernels disagree on BACKENDAI_CLUSTER_HOSTS; the manager generates it once per "
                f"session, so a disagreement means a kernel derived its own: {cluster_hosts_values}"
            )
            peers = [p for p in next(iter(cluster_hosts_values)).split(",") if p]
            assert len(peers) == CLUSTER_SIZE, f"expected {CLUSTER_SIZE} peers, got {peers}"

            for cid in container_ids:
                for peer in peers:
                    assert await probe.resolves_in_container(node, cid, peer), (
                        f"kernel {cid} cannot resolve peer {peer}; the session resolver was not "
                        f"registered with the whole peer map, or the container is not pointed at "
                        f"it (peers={peers})"
                    )
                contents = await _read_in_kernel(node, cid, "/etc/hosts")
                assert "127.0.1.1" not in contents, (
                    f"kernel {cid} has its own hostname pinned to loopback -- the regression that "
                    f"made a torchrun master unreachable to its workers\n{contents}"
                )


def _env_value(raw_environ: str, key: str) -> str:
    for entry in raw_environ.split("\0"):
        name, _, value = entry.partition("=")
        if name == key:
            return value
    return ""
