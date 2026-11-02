"""The containerd client package behind the agent's own error types."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import Any

from ai.backend.agent.containerd.rpc import client as rpc_client
from ai.backend.agent.containerd.rpc import errors as rpc_errors
from ai.backend.agent.containerd.rpc.client import ContainerdAPI
from ai.backend.agent.containerd.rpc.types import (
    ContainerdClientConfig,
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
    ContainerdUnavailableError,
)

__all__ = (
    "ContainerRecord",
    "ContainerdAPI",
    "ContainerdClient",
    "ContainerdClientConfig",
    "ImageTarget",
    "MountSpec",
    "RuntimeOptions",
    "TaskInfo",
    "TaskState",
)


@contextmanager
def _agent_errors() -> Iterator[None]:
    try:
        yield
    except rpc_errors.ContainerdUnavailable as e:
        raise ContainerdUnavailableError(str(e)) from e
    except (rpc_errors.ImageNotFound, rpc_errors.SnapshotParentNotFound) as e:
        raise ContainerdImageNotFound(str(e)) from e
    except rpc_errors.BlobNotFound as e:
        raise ContainerdImageInvalid(str(e)) from e
    except rpc_errors.ContainerdError as e:
        raise ContainerdOperationFailed(str(e)) from e


class ContainerdClient:
    """Implements `ContainerdAPI`; every failure is a `BackendAIError`."""

    _client: rpc_client.ContainerdClient

    def __init__(self, config: ContainerdClientConfig) -> None:
        self._client = rpc_client.ContainerdClient(config)

    @property
    def snapshotter(self) -> str:
        return self._client.snapshotter

    @property
    def namespace(self) -> str:
        return self._client.namespace

    @property
    def connected(self) -> bool:
        return self._client.connected

    async def connect(self) -> None:
        with _agent_errors():
            await self._client.connect()

    async def close(self) -> None:
        await self._client.close()

    async def get_image_target(self, image_ref: str) -> ImageTarget:
        with _agent_errors():
            return await self._client.get_image_target(image_ref)

    async def read_blob(self, digest: str) -> bytes:
        with _agent_errors():
            return await self._client.read_blob(digest)

    async def prepare_snapshot(self, key: str, parent: str) -> Sequence[MountSpec]:
        with _agent_errors():
            return await self._client.prepare_snapshot(key, parent)

    async def remove_snapshot(self, key: str) -> None:
        with _agent_errors():
            await self._client.remove_snapshot(key)

    async def create_container(
        self,
        record: ContainerRecord,
        runtime: str,
        spec: Mapping[str, Any],
        runtime_options: RuntimeOptions | None = None,
    ) -> None:
        with _agent_errors():
            await self._client.create_container(record, runtime, spec, runtime_options)

    async def get_container(self, container_id: str) -> ContainerRecord | None:
        with _agent_errors():
            return await self._client.get_container(container_id)

    async def list_containers(self, labels: Mapping[str, str]) -> Sequence[ContainerRecord]:
        with _agent_errors():
            return await self._client.list_containers(labels)

    async def delete_container(self, container_id: str) -> None:
        with _agent_errors():
            await self._client.delete_container(container_id)

    async def create_task(
        self, container_id: str, rootfs: Sequence[MountSpec], stdout: str, stderr: str
    ) -> int:
        with _agent_errors():
            return await self._client.create_task(container_id, rootfs, stdout, stderr)

    async def start_task(self, container_id: str) -> None:
        with _agent_errors():
            await self._client.start_task(container_id)

    async def get_task(self, container_id: str) -> TaskInfo | None:
        with _agent_errors():
            return await self._client.get_task(container_id)

    async def kill_task(self, container_id: str, signum: int, *, all_processes: bool) -> None:
        with _agent_errors():
            await self._client.kill_task(container_id, signum, all_processes=all_processes)

    async def delete_task(self, container_id: str) -> None:
        with _agent_errors():
            await self._client.delete_task(container_id)
