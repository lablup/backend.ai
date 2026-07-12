"""OCI container runtime interface (BEP-1058).

This is the **container-only** management surface: image and container/task lifecycle over
containerd's native gRPC API (Containers/Tasks/Images/Content/Snapshots services).

Terminology — this is deliberately NOT the CRI path:
- **CRI** (Container Runtime Interface) is Kubernetes' gRPC *interface* (a spec); containerd
  implements it with a higher-level *cri plugin* that layers a pod/sandbox model on top of
  the native services.
- That CRI implementation hides the network namespace behind ``RunPodSandbox`` and drives
  CNI itself — the runtime would own the network. BEP-1058 owns the network separately
  (multi-attach LOCAL/OVERLAY, central IPAM, vxlan), so we call the **native** API directly.

This interface therefore imports nothing from the network layer and knows nothing about CNI,
vxlan, or sessions. The single value that crosses the runtime↔network boundary is a task's
network namespace, exposed as ``TaskHandle.pid`` (the network layer derives
``/proc/{pid}/ns/net``). The ``ContainerdKernelOrchestrator`` is the sole place that composes
a runtime with the network subsystem; neither side references the other.

Lifecycle model: a container is created with an **isolated, empty network namespace** (only
loopback). Its task is then created (``create_task``) — the init process and namespaces exist
but the user command has not exec'd yet ('created' state — the task's PID is returned here) —
the network layer attaches CNI into that netns, and only then is the task started
(``start_task``). Attaching in the created window (rather than after start) means the user
process begins with its network already in place, closing the attach-after-start race.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TaskHandle:
    """A started containerd task. ``pid`` is the boundary contract to the network layer."""

    container_id: str
    pid: int


@dataclass(frozen=True)
class ImageInfo:
    """Metadata for one locally-stored image, as needed to build the agent's image scan.

    ``labels``/``architecture`` come from the OCI image *config* (not the runtime's image
    record), which is where kernel-spec/base-distro labels live."""

    name: str
    digest: str
    architecture: str
    labels: Mapping[str, str]


@dataclass(frozen=True)
class ContainerInfo:
    """A container as seen by the runtime, for lifecycle reconciliation on agent restart.

    ``status`` is the containerd task status string ('running'/'stopped'/'created'/...);
    the agent maps it to its own ContainerStatus."""

    id: str
    image: str
    labels: Mapping[str, str]
    status: str


@dataclass(frozen=True)
class TaskEvent:
    """A container task lifecycle event from the runtime's event stream.

    ``kind`` is 'start' | 'exit' | 'oom'; ``exit_code`` is meaningful for 'exit'."""

    kind: str
    container_id: str
    exit_code: int = 0


class OciRuntime(ABC):
    """Containerd-only lifecycle operations. No network/CNI concerns."""

    # --- lifecycle ---
    async def open(self) -> None:
        """Open any underlying connection (e.g. the containerd gRPC channel). Default no-op
        for clients that need no setup; idempotent."""

    async def close(self) -> None:
        """Release the underlying connection. Default no-op; idempotent."""

    # --- image service ---
    @abstractmethod
    async def image_exists(self, image_ref: str) -> bool: ...

    @abstractmethod
    async def image_digest(self, image_ref: str) -> str | None:
        """Return the local image's content digest (its manifest/index digest), or None if
        the image is not present."""

    @abstractmethod
    async def pull_image(
        self, image_ref: str, *, auth: Mapping[str, str] | None = None
    ) -> None: ...

    @abstractmethod
    async def list_images(self) -> Sequence[str]: ...

    @abstractmethod
    async def list_image_infos(self) -> Sequence[ImageInfo]:
        """List locally-stored images with their config labels + architecture (for the
        agent's image scan). Reads each image's OCI config to surface the labels."""

    @abstractmethod
    async def remove_image(self, image_ref: str) -> None: ...

    @abstractmethod
    async def push_image(
        self, image_ref: str, *, auth: Mapping[str, str] | None = None
    ) -> None: ...

    @abstractmethod
    async def image_entrypoint(self, image_ref: str) -> list[str] | None:
        """Return the image's Entrypoint (or Cmd if no entrypoint), or None if unknown."""

    # --- container/task lifecycle ---
    @abstractmethod
    async def create_container(
        self,
        container_id: str,
        *,
        image_ref: str,
        command: Sequence[str],
        oci_spec: Mapping[str, Any],
        network: str = "none",
    ) -> None:
        """Create a container (not started) with an isolated netns; the network layer
        attaches CNI to the task after start (``network`` is retained for interface
        compatibility and is otherwise "none")."""

    @abstractmethod
    async def create_task(self, container_id: str) -> TaskHandle:
        """Create the container's task (containerd Tasks.Create) and return its handle
        (incl. PID). The task is in the 'created' state: its init process and namespaces —
        including the network namespace — exist, but the user command has not exec'd yet.
        The network layer attaches CNI to ``/proc/{pid}/ns/net`` in this window; ``start_task``
        then resumes execution, so the process starts with its network already present."""

    @abstractmethod
    async def start_task(self, container_id: str) -> None:
        """Start (exec) the previously created task (containerd Tasks.Start)."""

    @abstractmethod
    async def kill_container(self, container_id: str, *, signal: int) -> None: ...

    @abstractmethod
    async def stop_container(self, container_id: str, *, grace_period: float) -> None:
        """Gracefully stop the task: SIGTERM, wait up to ``grace_period`` for it to exit, then SIGKILL
        if it is still running. Docker parity for the destroy phase (``container.stop()``)."""

    @abstractmethod
    async def remove_container(self, container_id: str) -> None:
        """Remove the task + container (force)."""

    @abstractmethod
    async def commit_container(
        self,
        container_id: str,
        *,
        base_image_ref: str,
        target_ref: str,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        """Commit a container's rootfs into a new local image ``target_ref`` (a flattened
        single-layer image derived from the base image's config), via Diff + Content +
        Images.Create."""

    # --- introspection ---
    @abstractmethod
    async def list_containers(self) -> Sequence[str]: ...

    @abstractmethod
    async def list_container_infos(self) -> Sequence[ContainerInfo]:
        """List containers with labels + image + task status (for restart reconciliation)."""

    @abstractmethod
    def subscribe_task_events(self) -> AsyncIterator[TaskEvent]:
        """Stream container task lifecycle events (start/exit/oom) for real-time reconciliation.
        The stream ends when the connection drops; the caller re-subscribes."""

    @abstractmethod
    async def container_pid(self, container_id: str) -> int | None:
        """Return the running task's PID, or None if the container has no live task."""

    @abstractmethod
    async def container_status(self, container_id: str) -> str | None:
        """Return the container's status string (e.g. 'running'), or None if absent."""
