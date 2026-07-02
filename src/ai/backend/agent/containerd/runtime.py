"""Low-level containerd runtime client contract (BEP-1055).

This is the **containerd-only** management surface: image and container/task
lifecycle over containerd's native API (NOT CRI — CRI's RunPodSandbox couples the
runtime to CNI, which BEP-1055 owns separately). It imports nothing from the network
layer and knows nothing about CNI, vxlan, or sessions.

The single value that crosses the runtime↔network boundary is a task's network
namespace, exposed here as ``TaskHandle.pid`` (the network layer derives
``/proc/{pid}/ns/net`` via ``agent.network.cni_runner.netns_path_for_pid``). The
`ContainerdAgent` is the sole place that composes this client with the network
subsystem; neither side references the other.

Concrete implementations (containerd gRPC services, or a subprocess-based client) live
behind this interface so the transport can be chosen/replaced without touching the
agent or the network stack.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TaskHandle:
    """A created containerd task. ``pid`` is the boundary contract to the network layer."""

    container_id: str
    pid: int


class ContainerdRuntimeClient(ABC):
    """Containerd-only lifecycle operations. No network/CNI concerns."""

    # --- image service ---
    @abstractmethod
    async def image_exists(self, image_ref: str) -> bool: ...

    @abstractmethod
    async def pull_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None: ...

    @abstractmethod
    async def list_images(self) -> Sequence[str]: ...

    @abstractmethod
    async def remove_image(self, image_ref: str) -> None: ...

    # --- container/task lifecycle ---
    @abstractmethod
    async def create_container(
        self, container_id: str, *, image_ref: str, oci_spec: Mapping[str, Any]
    ) -> None:
        """Create a container from an image and an OCI runtime spec.

        The spec MUST request an isolated (empty) network namespace so the task starts
        with only loopback; the network layer attaches interfaces afterward.
        """

    @abstractmethod
    async def create_task(self, container_id: str) -> TaskHandle:
        """Create the task (runc process) for a container and return its PID.

        The task is created but not started, so the network layer can attach CNI to the
        task's netns before the workload process runs.
        """

    @abstractmethod
    async def start_task(self, container_id: str) -> None: ...

    @abstractmethod
    async def kill_task(self, container_id: str, *, signal: int) -> None: ...

    @abstractmethod
    async def delete_task(self, container_id: str) -> None: ...

    @abstractmethod
    async def delete_container(self, container_id: str) -> None: ...

    # --- introspection ---
    @abstractmethod
    async def list_containers(self) -> Sequence[str]: ...

    @abstractmethod
    async def task_pid(self, container_id: str) -> int | None:
        """Return the running task's PID, or None if the container has no live task."""
