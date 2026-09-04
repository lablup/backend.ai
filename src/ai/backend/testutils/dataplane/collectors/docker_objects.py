"""Docker-side resources, for running the same scenarios against the reference backend.

The Docker backend is the parity baseline: for anything a user can observe, what Docker does is
the expected value. But its resources have almost no overlap with the containerd backend's,
because the two split network ownership differently — dockerd/swarm owns the overlay data plane,
so the agent's `leave_network` is a no-op and there is no per-session journal, no subnet block and
no VTEP to leak. What *can* leak here is a cluster network the manager never destroyed, a
container record never removed, and the sandbox netns that hangs off one.

**Netns are matched to owners, never listed raw.** `/var/run/docker/netns/` holds one file per
container sandbox plus `default` and swarm's `ingress_sbox`, so a healthy host has as many as it
has containers. Reporting the files themselves would flag every running service as a leak — an
alarm that was in fact raised by hand against this very host before the matching was written. Only
a sandbox no container claims is a resource here.
"""

from __future__ import annotations

import json
from collections.abc import Sequence

from ai.backend.testutils.dataplane.collectors.base import Resource
from ai.backend.testutils.dataplane.nodes import CommandFailed, Node

# The manager names cluster networks `bai-multinode-{ident}` (manager/network/overlay.py) and
# labels them `ai.backend.cluster-network=1`. The label is the reliable marker; the prefix is kept
# as a fallback for a network created by an older manager.
CLUSTER_NETWORK_LABEL = "ai.backend.cluster-network"
CLUSTER_NETWORK_PREFIX = "bai-multinode-"

# Backend.AI kernel containers under the Docker backend.
KERNEL_NAME_PREFIX = "kernel."

# Sandboxes that belong to the host or to swarm itself, not to any one container.
_UNOWNED_SANDBOXES = frozenset({"default", "ingress_sbox"})


def _parse_json_lines(raw: str, *, what: str, node: str) -> list[dict[str, object]]:
    parsed: list[dict[str, object]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parsed.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise CommandFailed(f"[{node}] {what} produced a non-JSON line: {line!r}") from e
    return parsed


class DockerNetworkCollector:
    """Cluster networks the manager created and did not destroy."""

    _node: Node

    def __init__(self, node: Node) -> None:
        self._node = node

    @property
    def kind(self) -> str:
        return "docker-network"

    def parse(self, raw: str) -> set[Resource]:
        found: set[Resource] = set()
        for net in _parse_json_lines(raw, what="docker network ls", node=self._node.name):
            name = str(net.get("Name", ""))
            labels = str(net.get("Labels", "") or "")
            if not (CLUSTER_NETWORK_LABEL in labels or name.startswith(CLUSTER_NETWORK_PREFIX)):
                continue
            found.add(Resource(self.kind, self._node.name, name, str(net.get("Driver", ""))))
        return found

    async def collect(self) -> set[Resource]:
        result = await self._node.run([
            "docker",
            "network",
            "ls",
            "--format",
            "{{json .}}",
        ])
        return self.parse(result.stdout)


class DockerKernelContainerCollector:
    """Kernel containers, running or exited.

    Exited-but-not-removed is the Docker-side counterpart of the containerd backend's
    container-record leak, and it holds the rootfs layer for as long as it lasts.
    """

    _node: Node

    def __init__(self, node: Node) -> None:
        self._node = node

    @property
    def kind(self) -> str:
        return "docker-container"

    def parse(self, raw: str) -> set[Resource]:
        found: set[Resource] = set()
        for c in _parse_json_lines(raw, what="docker ps", node=self._node.name):
            name = str(c.get("Names", "")).lstrip("/")
            if not name.startswith(KERNEL_NAME_PREFIX):
                continue
            # `State` is running/exited/created — part of the detail, not the identity, so a
            # kernel that stops during a scenario is not reported as one resource replacing
            # another.
            found.add(Resource(self.kind, self._node.name, name, str(c.get("State", ""))))
        return found

    async def collect(self) -> set[Resource]:
        result = await self._node.run([
            "docker",
            "ps",
            "-a",
            "--format",
            "{{json .}}",
        ])
        return self.parse(result.stdout)

    async def kernel_ids(self) -> set[str]:
        """Kernel ids Docker still has a container record for, running or exited.

        The container is named `kernel.<runtime>.<kernel_id>`, so the id is the last dotted field.
        Used to decide which scratch directories still have an owner.
        """
        result = await self._node.run([
            "docker",
            "ps",
            "-a",
            "--format",
            "{{json .}}",
        ])
        return {r.ident.rsplit(".", 1)[-1] for r in self.parse(result.stdout)}


class DockerSandboxCollector:
    """Network sandboxes in `/var/run/docker/netns/` that no container claims.

    See the module docstring: the raw file list is not a leak signal. A sandbox is a resource here
    only when nothing in `docker ps -a` names it as its `SandboxKey`.
    """

    _node: Node
    _netns_dir: str

    def __init__(self, node: Node, *, netns_dir: str = "/var/run/docker/netns") -> None:
        self._node = node
        self._netns_dir = netns_dir

    @property
    def kind(self) -> str:
        return "docker-sandbox"

    def parse(self, listing: str, sandbox_keys: str) -> set[Resource]:
        claimed = {key.rsplit("/", 1)[-1] for key in sandbox_keys.split() if key.strip()}
        found: set[Resource] = set()
        for name in listing.split():
            name = name.strip()
            if not name or name in _UNOWNED_SANDBOXES:
                continue
            if name.startswith("1-"):
                # `1-<network-id-prefix>` is an overlay network's own sandbox, owned by the
                # network rather than by a container. DockerNetworkCollector is what notices a
                # network that outlived its session; flagging its sandbox too would report the
                # same leak twice, and report swarm's permanent `ingress` as a leak besides.
                continue
            if name in claimed:
                continue
            found.add(Resource(self.kind, self._node.name, f"{self._netns_dir}/{name}", "unowned"))
        return found

    async def collect(self) -> set[Resource]:
        listing = await self._node.run(["ls", "-1", self._netns_dir], check=False)
        if listing.returncode != 0:
            if "No such file" in listing.stderr:
                return set()  # dockerd has never run here
            listing.check()
        keys = await self._node.run([
            "docker",
            "ps",
            "-a",
            "--format",
            "{{.State}}\t{{.ID}}",
        ])
        # `docker ps` cannot print SandboxKey, so inspect every container in one call.
        ids = [line.split("\t")[-1] for line in keys.lines]
        if not ids:
            return self.parse(listing.stdout, "")
        inspected = await self._node.run([
            "docker",
            "inspect",
            "--format",
            "{{.NetworkSettings.SandboxKey}}",
            *ids,
        ])
        return self.parse(listing.stdout, inspected.stdout)


def docker_collectors(node: Node, *, netns_dir: str = "/var/run/docker/netns") -> Sequence[object]:
    return (
        DockerNetworkCollector(node),
        DockerKernelContainerCollector(node),
        DockerSandboxCollector(node, netns_dir=netns_dir),
    )
