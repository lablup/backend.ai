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
from ai.backend.testutils.dataplane.guard import LeakGuard
from ai.backend.testutils.dataplane.nodes import Node
from ai.backend.testutils.dataplane.session import SessionDriver, SessionSpec

CLUSTER_SIZE = 3


@pytest.fixture
def single_node_cluster_spec(session_spec: SessionSpec) -> SessionSpec:
    return replace(
        session_spec, cluster_size=CLUSTER_SIZE, cluster_mode=ClusterModeEnum.SINGLE_NODE
    )


async def _read_in_kernel(node: Node, container_id: str, path: str) -> str:
    """Read a file from inside a running kernel.

    Through the runtime rather than from the host: the point of these assertions is what the
    *kernel* sees. A single-node cluster's /etc/hosts is written into the container, and reading
    the host's copy would assert on the wrong file.
    """
    result = await node.run([
        "ctr",
        "-n",
        "backend-ai",
        "tasks",
        "exec",
        "--exec-id",
        f"dp-read-{abs(hash(path)) % 100000}",
        container_id,
        "cat",
        path,
    ])
    return result.stdout


class TestSingleNodeClusterSession:
    async def test_g9_peers_resolve_and_every_kernel_sees_the_whole_cluster(
        self,
        leak_guard: LeakGuard,
        session_driver: SessionDriver,
        single_node_cluster_spec: SessionSpec,
        node: Node,
    ) -> None:
        """Three things at once, because they share one root cause when they break.

        `/etc/hosts` must name every peer, and must not have the kernel's own hostname rewritten
        to a loopback address -- that rewrite is what stranded torchrun. `BACKENDAI_CLUSTER_HOSTS`
        must agree across kernels, since the manager generates it once per session and a kernel
        that disagrees is reading a locally-derived copy. And the addresses must be the node-local
        block's, not an overlay's.
        """
        async with session_driver.session(single_node_cluster_spec, "dp-g9") as handle:
            container_ids = await _cluster_container_ids(node, handle.name)
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

            hosts_files = {
                cid: await _read_in_kernel(node, cid, "/etc/hosts") for cid in container_ids
            }
            for cid, contents in hosts_files.items():
                resolved = _hosts_names(contents)
                for peer in peers:
                    assert peer in resolved, (
                        f"kernel {cid} cannot resolve peer {peer}; /etc/hosts was written from an "
                        f"incomplete peer map (peers={peers})\n{contents}"
                    )
                assert "127.0.1.1" not in contents, (
                    f"kernel {cid} has its own hostname pinned to loopback -- the regression that "
                    f"made a torchrun master unreachable to its workers\n{contents}"
                )


async def _cluster_container_ids(node: Node, session_name: str) -> list[str]:
    """Container ids of this node's kernels for a session.

    Read from containerd's own labels rather than from the manager: the question this scenario
    asks is where the kernels actually landed, and taking the manager's word for it would assume
    the answer.
    """
    result = await node.run([
        "ctr",
        "-n",
        "backend-ai",
        "containers",
        "list",
        "-q",
    ])
    ids: list[str] = []
    for cid in result.lines:
        info = await node.run(["ctr", "-n", "backend-ai", "containers", "info", cid])
        if session_name in info.stdout:
            ids.append(cid)
    return ids


def _hosts_names(etc_hosts: str) -> set[str]:
    """The hostnames /etc/hosts actually resolves, so a peer check matches a whole name and not a
    substring — ``main`` must not count as present just because ``main1`` is."""
    names: set[str] = set()
    for line in etc_hosts.splitlines():
        parts = line.split()
        names.update(parts[1:])  # every alias after the address column
    return names


def _env_value(raw_environ: str, key: str) -> str:
    for entry in raw_environ.split("\0"):
        name, _, value = entry.partition("=")
        if name == key:
            return value
    return ""
