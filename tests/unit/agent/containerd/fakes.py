from __future__ import annotations

import json
import signal
from collections.abc import Mapping, Sequence
from typing import Any

from ai.backend.agent.containerd.client import (
    ContainerRecord,
    ImageTarget,
    MountSpec,
    TaskInfo,
    TaskState,
)
from ai.backend.agent.containerd.network import CommandResult
from ai.backend.agent.containerd.profile.base import RuntimeOptions
from ai.backend.agent.errors.containerd import (
    ContainerdImageNotFound,
    ContainerdOperationFailed,
    KernelNetworkSetupFailed,
)


class FakeContainerd:
    """An in-memory containerd: images, blobs, snapshots, containers and tasks."""

    snapshotter: str
    namespace: str
    images: dict[str, ImageTarget]
    blobs: dict[str, bytes]
    snapshots: dict[str, Sequence[MountSpec]]
    containers: dict[str, ContainerRecord]
    specs: dict[str, Mapping[str, Any]]
    runtime_options: dict[str, RuntimeOptions | None]
    tasks: dict[str, TaskInfo]
    calls: list[tuple[str, str]]
    failing: set[str]
    exits_on_sigterm: bool
    closed: bool
    connected: bool

    def __init__(self, *, exits_on_sigterm: bool = True) -> None:
        self.snapshotter = "overlayfs"
        self.namespace = "fake-ns"
        self.images = {}
        self.blobs = {}
        self.snapshots = {}
        self.containers = {}
        self.specs = {}
        self.runtime_options = {}
        self.tasks = {}
        self.calls = []
        self.failing = set()
        self.exits_on_sigterm = exits_on_sigterm
        self.closed = False
        self.connected = True

    async def connect(self) -> None:
        self.connected = True

    def _call(self, op: str, key: str = "") -> None:
        self.calls.append((op, key))
        if op in self.failing:
            raise ContainerdOperationFailed(f"{op}: injected failure")

    async def close(self) -> None:
        self.closed = True

    async def get_image_target(self, image_ref: str) -> ImageTarget:
        self._call("get_image_target", image_ref)
        if image_ref not in self.images:
            raise ContainerdImageNotFound(image_ref)
        return self.images[image_ref]

    async def read_blob(self, digest: str) -> bytes:
        self._call("read_blob", digest)
        return self.blobs[digest]

    async def prepare_snapshot(self, key: str, parent: str) -> Sequence[MountSpec]:
        self._call("prepare_snapshot", key)
        mounts = [MountSpec("overlay", "overlay", (f"lowerdir={parent}",))]
        self.snapshots[key] = mounts
        return mounts

    async def remove_snapshot(self, key: str) -> None:
        self._call("remove_snapshot", key)
        self.snapshots.pop(key, None)

    async def create_container(
        self,
        record: ContainerRecord,
        runtime: str,
        spec: Mapping[str, Any],
        runtime_options: RuntimeOptions | None = None,
    ) -> None:
        self._call("create_container", record.id)
        self.runtime_options[record.id] = runtime_options
        self.containers[record.id] = record
        self.specs[record.id] = spec

    async def get_container(self, container_id: str) -> ContainerRecord | None:
        return self.containers.get(container_id)

    async def list_containers(self, labels: Mapping[str, str]) -> Sequence[ContainerRecord]:
        return [
            c
            for c in self.containers.values()
            if all(k in c.labels and (not v or c.labels[k] == v) for k, v in labels.items())
        ]

    async def delete_container(self, container_id: str) -> None:
        self._call("delete_container", container_id)
        self.containers.pop(container_id, None)

    async def create_task(
        self, container_id: str, rootfs: Sequence[MountSpec], stdout: str, stderr: str
    ) -> int:
        self._call("create_task", container_id)
        self.tasks[container_id] = TaskInfo(pid=1000, state=TaskState.CREATED, exit_status=0)
        return 1000

    async def start_task(self, container_id: str) -> None:
        self._call("start_task", container_id)
        self.tasks[container_id] = TaskInfo(pid=1000, state=TaskState.RUNNING, exit_status=0)

    async def get_task(self, container_id: str) -> TaskInfo | None:
        return self.tasks.get(container_id)

    async def kill_task(self, container_id: str, signum: int, *, all_processes: bool) -> None:
        self._call(f"kill_task:{signal.Signals(signum).name}", container_id)
        if container_id not in self.tasks:
            return
        if signum == signal.SIGKILL or self.exits_on_sigterm:
            self.tasks[container_id] = TaskInfo(pid=1000, state=TaskState.STOPPED, exit_status=137)

    async def delete_task(self, container_id: str) -> None:
        self._call("delete_task", container_id)
        self.tasks.pop(container_id, None)

    def add_image(
        self, image_ref: str, *, diff_ids: Sequence[str], env: Sequence[str] = ()
    ) -> None:
        """Register a single-manifest image."""
        config = {"rootfs": {"diff_ids": list(diff_ids)}, "config": {"Env": list(env)}}
        self.blobs["sha256:config"] = json.dumps(config).encode()
        self.blobs["sha256:manifest"] = json.dumps({"config": {"digest": "sha256:config"}}).encode()
        self.images[image_ref] = ImageTarget(
            "sha256:manifest", "application/vnd.oci.image.manifest.v1+json"
        )


class FakeCommandRunner:
    """Records host commands and answers from scripted results keyed by argv prefix.

    The longest matching prefix wins; an unscripted command succeeds with empty output.
    """

    calls: list[tuple[str, ...]]
    results: dict[tuple[str, ...], CommandResult]
    failing: set[tuple[str, ...]]
    _shared: list[tuple[str, str]] | None

    def __init__(self, shared: list[tuple[str, str]] | None = None) -> None:
        """`shared` also receives ("cmd", argv text), e.g. FakeContainerd.calls, to assert order."""
        self.calls = []
        self.results = {}
        self.failing = set()
        self._shared = shared

    def script(self, prefix: Sequence[str], stdout: str = "", returncode: int = 0) -> None:
        self.results[tuple(prefix)] = CommandResult(returncode, stdout, "")

    async def __call__(self, *argv: str, check: bool = True) -> CommandResult:
        self.calls.append(argv)
        if self._shared is not None:
            self._shared.append(("cmd", " ".join(argv)))
        if any(argv[: len(p)] == p for p in self.failing):
            raise KernelNetworkSetupFailed(f"{argv}: injected failure")
        matches = [p for p in self.results if argv[: len(p)] == p]
        result = self.results[max(matches, key=len)] if matches else CommandResult(0, "", "")
        if check and result.returncode != 0:
            raise KernelNetworkSetupFailed(f"{argv}: exit {result.returncode}")
        return result

    def matching(self, *prefix: str) -> list[tuple[str, ...]]:
        return [c for c in self.calls if c[: len(prefix)] == prefix]
