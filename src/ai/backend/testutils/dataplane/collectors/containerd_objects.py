"""containerd objects in the agent's namespace, on one node.

Containers, tasks and snapshots are collected separately rather than as one "container" resource,
because they leak *independently* and each points at a different bug. A task with no container is
a shim that outlived its delete; a container with no task is a create that failed after the
container record; an Active snapshot with neither is a rootfs whose delete never ran. Collapsing
them would report one leak where three distinct defects live.

Images and content blobs are deliberately not collected: the image cache is meant to be durable
across sessions. A scenario that asserts on committed images should pull and warm up **before**
the baseline snapshot, so the cache lands in the baseline and only the session's own objects can
show up as a delta.

**These four listings are not one atomic view.** `ctr` offers no combined query, so a container
created between `containers list` and `tasks list` appears here as a task with no container — a
phantom that reads exactly like the shim-outlived-its-delete leak. Do not conclude anything from
cross-referencing a single snapshot; `LeakGuard.baseline` requires the picture to repeat before
trusting it, and `settle` polls. The production code hits the same hazard and answers it by taking
its two views from one listing (`session_network._live_and_own_containers`), which is not
available across process boundaries.
"""

from __future__ import annotations

from collections.abc import Sequence

from ai.backend.testutils.dataplane.collectors.base import Resource
from ai.backend.testutils.dataplane.nodes import Node

DEFAULT_NAMESPACE = "backend-ai"
DEFAULT_ADDRESS = "/run/containerd/containerd.sock"


def _rows(raw: str, header_token: str) -> list[list[str]]:
    """Split `ctr`'s column output into token rows, dropping its header line.

    `ctr` has no stable machine-readable output for these commands, so the header is identified by
    its first token rather than by position — that keeps an added trailing column (which
    containerd has done between minor versions) from shifting anything we read.
    """
    rows: list[list[str]] = []
    for line in raw.splitlines():
        tokens = line.split()
        if not tokens:
            continue
        if tokens[0] == header_token:
            continue
        rows.append(tokens)
    return rows


class ContainerdObjectCollector:
    _node: Node
    _address: str
    _namespace: str

    def __init__(
        self,
        node: Node,
        *,
        address: str = DEFAULT_ADDRESS,
        namespace: str = DEFAULT_NAMESPACE,
    ) -> None:
        self._node = node
        self._address = address
        self._namespace = namespace

    @property
    def kind(self) -> str:
        return "containerd"

    def _ctr(self, *args: str) -> list[str]:
        return ["ctr", "-a", self._address, "-n", self._namespace, *args]

    def parse_containers(self, raw: str) -> set[Resource]:
        return {
            Resource(self.kind, self._node.name, f"container {row[0]}", " ".join(row[1:]))
            for row in _rows(raw, "CONTAINER")
        }

    def parse_tasks(self, raw: str) -> set[Resource]:
        found: set[Resource] = set()
        for row in _rows(raw, "TASK"):
            # TASK PID STATUS — the PID changes across a restart of the same logical task, so it
            # belongs in the detail, not the identity.
            detail = f"pid={row[1]} {row[2]}" if len(row) >= 3 else " ".join(row[1:])
            found.add(Resource(self.kind, self._node.name, f"task {row[0]}", detail))
        return found

    def parse_snapshots(self, raw: str, *, kinds: Sequence[str] | None = None) -> set[Resource]:
        found: set[Resource] = set()
        for row in _rows(raw, "KEY"):
            snapshot_kind = row[-1] if len(row) >= 2 else ""
            if kinds is not None and snapshot_kind not in kinds:
                continue
            found.add(Resource(self.kind, self._node.name, f"snapshot {row[0]}", snapshot_kind))
        return found

    def parse_leases(self, raw: str) -> set[Resource]:
        return {
            Resource(self.kind, self._node.name, f"lease {row[0]}", " ".join(row[1:]))
            for row in _rows(raw, "ID")
        }

    async def kernel_ids(self) -> set[str]:
        """Kernel ids containerd still has a *container record* for.

        Record, not task: a kernel that exited still owns its scratch until its container is
        removed, so a scratch directory is orphaned only once the record is gone. The agent uses
        the kernel id as the container id (BEP-1062), so no translation is needed.
        """
        result = await self._node.run(self._ctr("containers", "list"))
        return {row[0] for row in _rows(result.stdout, "CONTAINER")}

    async def collect(self) -> set[Resource]:
        containers = await self._node.run(self._ctr("containers", "list"))
        tasks = await self._node.run(self._ctr("tasks", "list"))
        snapshots = await self._node.run(self._ctr("snapshots", "list"))
        leases = await self._node.run(self._ctr("leases", "list"))
        return (
            self.parse_containers(containers.stdout)
            | self.parse_tasks(tasks.stdout)
            | self.parse_snapshots(snapshots.stdout)
            | self.parse_leases(leases.stdout)
        )
