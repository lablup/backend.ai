from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from ai.backend.agent.containerd.rpc.types import ContainerRecord, ImageTarget, TaskInfo
from ai.backend.agent.errors.containerd import ContainerdImageInvalid, ContainerdImageNotFound


class FakeContainerd:
    """An in-memory containerd: images, blobs, containers and tasks."""

    images: dict[str, ImageTarget]
    blobs: dict[str, bytes]
    containers: dict[str, ContainerRecord]
    tasks: dict[str, TaskInfo]
    calls: list[str]
    closed: bool
    connected: bool
    ignore_filters: bool
    failing_tasks: set[str]

    def __init__(self) -> None:
        self.images = {}
        self.blobs = {}
        self.containers = {}
        self.tasks = {}
        self.calls = []
        self.closed = False
        self.connected = True
        self.ignore_filters = False
        self.failing_tasks = set()

    async def connect(self) -> None:
        self.connected = True

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
