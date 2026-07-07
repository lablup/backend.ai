"""Low-level containerd runtime client contract (BEP-1058).

This is the **containerd-only** management surface: image and container/task lifecycle
over containerd's native tooling/API (NOT CRI — CRI's RunPodSandbox couples the runtime
to CNI, which BEP-1058 owns separately). It imports nothing from the network layer and
knows nothing about CNI, vxlan, or sessions.

The single value that crosses the runtime↔network boundary is a task's network
namespace, exposed here as ``TaskHandle.pid`` (the network layer derives
``/proc/{pid}/ns/net``). The ``ContainerdKernelOrchestrator`` is the sole place that
composes this client with the network subsystem; neither side references the other.

Lifecycle model: a container is created with an **isolated, empty network namespace**
(only loopback) and then started; the running task's PID is returned so the network
layer can attach CNI into its netns. (A future containerd-gRPC implementation may attach
in the pre-start "created" state; the tooling-based client cannot expose a PID before
start, so networking attaches immediately after start — validated to work in
BEP-1058/verification.md §5.)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TaskHandle:
    """A started containerd task. ``pid`` is the boundary contract to the network layer."""

    container_id: str
    pid: int


class ContainerdRuntimeClient(ABC):
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
    async def pull_image(
        self, image_ref: str, *, auth: Mapping[str, str] | None = None
    ) -> None: ...

    @abstractmethod
    async def list_images(self) -> Sequence[str]: ...

    @abstractmethod
    async def remove_image(self, image_ref: str) -> None: ...

    @abstractmethod
    async def push_image(self, image_ref: str) -> None: ...

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
    async def start_container(self, container_id: str) -> TaskHandle:
        """Start the container's task and return its handle (incl. PID)."""

    @abstractmethod
    async def kill_container(self, container_id: str, *, signal: int) -> None: ...

    @abstractmethod
    async def remove_container(self, container_id: str) -> None:
        """Remove the task + container (force)."""

    # --- introspection ---
    @abstractmethod
    async def list_containers(self) -> Sequence[str]: ...

    @abstractmethod
    async def container_pid(self, container_id: str) -> int | None:
        """Return the running task's PID, or None if the container has no live task."""

    @abstractmethod
    async def container_status(self, container_id: str) -> str | None:
        """Return the container's status string (e.g. 'running'), or None if absent."""
