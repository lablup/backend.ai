from __future__ import annotations

import json
import signal
from collections.abc import Mapping, Sequence
from typing import Any

from ai.backend.agent.containerd.network import CommandResult
from ai.backend.agent.containerd.rpc.types import (
    ContainerRecord,
    ImageTarget,
    MountSpec,
    RuntimeOptions,
    TaskInfo,
    TaskState,
)
from ai.backend.agent.errors.containerd import (
    ContainerdImageInvalid,
    ContainerdImageNotFound,
    ContainerdOperationFailed,
    KernelNetworkSetupFailed,
)


class FakeContainerd:
    """An in-memory containerd: images, blobs, containers and tasks."""

    images: dict[str, ImageTarget]
    blobs: dict[str, bytes]
    containers: dict[str, ContainerRecord]
    snapshots: dict[str, Sequence[MountSpec]]
    specs: dict[str, tuple[str, Mapping[str, Any]]]
    runtime_options: dict[str, RuntimeOptions | None]
    tasks: dict[str, TaskInfo]
    calls: list[str]
    closed: bool
    connected: bool
    ignore_filters: bool
    failing_tasks: set[str]
    failing: set[str]
    exits_on_sigterm: bool
    snapshotter = "overlayfs"
    namespace = "fake-ns"

    def __init__(self, *, exits_on_sigterm: bool = True) -> None:
        self.images = {}
        self.blobs = {}
        self.containers = {}
        self.snapshots = {}
        self.specs = {}
        self.runtime_options = {}
        self.tasks = {}
        self.calls = []
        self.closed = False
        self.connected = True
        self.ignore_filters = False
        self.failing_tasks = set()
        self.failing = set()
        self.exits_on_sigterm = exits_on_sigterm

    async def connect(self) -> None:
        self.connected = True

    def _call(self, op: str) -> None:
        self.calls.append(op)
        if op in self.failing:
            raise ContainerdOperationFailed(f"{op}: injected failure")

    async def close(self) -> None:
        self.closed = True

    async def list_containers(self, labels: Mapping[str, str]) -> Sequence[ContainerRecord]:
        self.calls.append("list_containers")
        if self.ignore_filters:
            return list(self.containers.values())
        return [
            c
            for c in self.containers.values()
            if all(k in c.labels and (not v or c.labels[k] == v) for k, v in labels.items())
        ]

    async def get_task(self, container_id: str) -> TaskInfo | None:
        self.calls.append("get_task")
        if container_id in self.failing_tasks:
            raise RuntimeError("get_task failed")
        return self.tasks.get(container_id)

    async def get_image_target(self, image_ref: str) -> ImageTarget:
        self.calls.append("get_image_target")
        if image_ref not in self.images:
            raise ContainerdImageNotFound(image_ref)
        return self.images[image_ref]

    async def read_blob(self, digest: str) -> bytes:
        self.calls.append("read_blob")
        if digest not in self.blobs:
            raise ContainerdImageInvalid(f"the blob {digest} is not in the content store")
        return self.blobs[digest]

    async def prepare_snapshot(self, key: str, parent: str) -> Sequence[MountSpec]:
        self._call("prepare_snapshot")
        self.snapshots[key] = [MountSpec("overlay", "overlay", (f"lowerdir={parent}",))]
        return self.snapshots[key]

    async def remove_snapshot(self, key: str) -> None:
        self._call("remove_snapshot")
        self.snapshots.pop(key, None)

    async def create_container(
        self,
        record: ContainerRecord,
        runtime: str,
        spec: Mapping[str, Any],
        runtime_options: RuntimeOptions | None = None,
    ) -> None:
        self._call("create_container")
        self.containers[record.id] = record
        self.specs[record.id] = (runtime, spec)
        self.runtime_options[record.id] = runtime_options

    async def get_container(self, container_id: str) -> ContainerRecord | None:
        return self.containers.get(container_id)

    async def delete_container(self, container_id: str) -> None:
        self._call("delete_container")
        self.containers.pop(container_id, None)

    async def create_task(self, container_id: str, *_: Any) -> int:
        self._call("create_task")
        self.tasks[container_id] = TaskInfo(pid=1000, state=TaskState.CREATED, exit_status=0)
        return 1000

    async def start_task(self, container_id: str) -> None:
        self._call("start_task")
        self.tasks[container_id] = TaskInfo(pid=1000, state=TaskState.RUNNING, exit_status=0)

    async def kill_task(self, container_id: str, signum: int, *, all_processes: bool) -> None:
        self._call(f"kill_task:{signal.Signals(signum).name}")
        if container_id in self.tasks and (signum == signal.SIGKILL or self.exits_on_sigterm):
            self.tasks[container_id] = TaskInfo(pid=1000, state=TaskState.STOPPED, exit_status=137)

    async def delete_task(self, container_id: str) -> None:
        self._call("delete_task")
        self.tasks.pop(container_id, None)

    def add_image(
        self,
        image_ref: str,
        *,
        diff_ids: Sequence[str],
        env: Sequence[str] = (),
        runtime: Mapping[str, Any] | None = None,
    ) -> None:
        """Register a single-manifest image; `runtime` adds image config keys (Cmd, ...)."""
        config = {
            "rootfs": {"diff_ids": list(diff_ids)},
            "config": {"Env": list(env), **(runtime or {})},
        }
        self.blobs["sha256:config"] = json.dumps(config).encode()
        self.blobs["sha256:manifest"] = json.dumps({"config": {"digest": "sha256:config"}}).encode()
        self.images[image_ref] = ImageTarget(
            "sha256:manifest", "application/vnd.oci.image.manifest.v1+json"
        )


class FakeCommandRunner:
    """Records host commands; the longest scripted argv prefix answers, else success."""

    calls: list[tuple[str, ...]]
    results: dict[tuple[str, ...], CommandResult]

    def __init__(self) -> None:
        self.calls = []
        self.results = {}

    def script(self, prefix: Sequence[str], stdout: str = "", returncode: int = 0) -> None:
        self.results[tuple(prefix)] = CommandResult(returncode, stdout, "")

    async def __call__(self, *argv: str, check: bool = True) -> CommandResult:
        self.calls.append(argv)
        matches = [p for p in self.results if argv[: len(p)] == p]
        result = self.results[max(matches, key=len)] if matches else CommandResult(0, "", "")
        if check and result.returncode != 0:
            raise KernelNetworkSetupFailed(f"{argv}: exit {result.returncode}")
        return result

    def matching(self, *prefix: str) -> list[tuple[str, ...]]:
        return [c for c in self.calls if c[: len(prefix)] == prefix]
