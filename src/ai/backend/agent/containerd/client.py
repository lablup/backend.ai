"""A thin async client over the vendored containerd gRPC stubs."""

from __future__ import annotations

import asyncio
import enum
import json
import logging
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Final, Protocol

import grpc
from google.protobuf import any_pb2

from ai.backend.agent.containerd._grpcapi.api.services.containers.v1 import (
    containers_pb2,
    containers_pb2_grpc,
)
from ai.backend.agent.containerd._grpcapi.api.services.content.v1 import (
    content_pb2,
    content_pb2_grpc,
)
from ai.backend.agent.containerd._grpcapi.api.services.images.v1 import images_pb2, images_pb2_grpc
from ai.backend.agent.containerd._grpcapi.api.services.snapshots.v1 import (
    snapshots_pb2,
    snapshots_pb2_grpc,
)
from ai.backend.agent.containerd._grpcapi.api.services.tasks.v1 import tasks_pb2, tasks_pb2_grpc
from ai.backend.agent.containerd._grpcapi.api.types import mount_pb2
from ai.backend.agent.errors.containerd import (
    ContainerdImageNotFound,
    ContainerdOperationFailed,
    ContainerdUnavailableError,
)
from ai.backend.common.exception import BackendAIError
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

NAMESPACE_HEADER: Final = "containerd-namespace"
SPEC_TYPE_URL: Final = "types.containerd.io/opencontainers/runtime-spec/1/Spec"
DEFAULT_CALL_TIMEOUT: Final = 30.0

_NOT_FOUND: Final = frozenset({grpc.StatusCode.NOT_FOUND})


class TaskState(enum.StrEnum):
    UNKNOWN = "unknown"
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    PAUSING = "pausing"


_TASK_STATES: Final[Mapping[int, TaskState]] = {
    0: TaskState.UNKNOWN,
    1: TaskState.CREATED,
    2: TaskState.RUNNING,
    3: TaskState.STOPPED,
    4: TaskState.PAUSED,
    5: TaskState.PAUSING,
}


@dataclass(frozen=True)
class ContainerdClientConfig:
    address: str
    namespace: str
    snapshotter: str
    call_timeout: float = DEFAULT_CALL_TIMEOUT


@dataclass(frozen=True)
class ImageTarget:
    digest: str
    media_type: str


@dataclass(frozen=True)
class MountSpec:
    type: str
    source: str
    options: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContainerRecord:
    id: str
    image: str
    snapshotter: str
    snapshot_key: str
    labels: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskInfo:
    pid: int
    state: TaskState
    exit_status: int


class ContainerdAPI(Protocol):
    """The containerd calls the agent uses; the fake client in the tests implements it."""

    @property
    def snapshotter(self) -> str: ...

    async def close(self) -> None: ...

    async def get_image_target(self, image_ref: str) -> ImageTarget: ...

    async def read_blob(self, digest: str) -> bytes: ...

    async def prepare_snapshot(self, key: str, parent: str) -> Sequence[MountSpec]: ...

    async def remove_snapshot(self, key: str) -> None: ...

    async def create_container(
        self, record: ContainerRecord, runtime: str, spec: Mapping[str, Any]
    ) -> None: ...

    async def get_container(self, container_id: str) -> ContainerRecord | None: ...

    async def list_containers(self, labels: Mapping[str, str]) -> Sequence[ContainerRecord]: ...

    async def delete_container(self, container_id: str) -> None: ...

    async def create_task(
        self, container_id: str, rootfs: Sequence[MountSpec], stdout: str, stderr: str
    ) -> int: ...

    async def start_task(self, container_id: str) -> None: ...

    async def get_task(self, container_id: str) -> TaskInfo | None: ...

    async def kill_task(self, container_id: str, signum: int, *, all_processes: bool) -> None: ...

    async def delete_task(self, container_id: str) -> None: ...


def _grpc_target(address: str) -> str:
    if "://" in address or address.startswith("unix:"):
        return address
    return f"unix://{address}"


def _quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _label_filter(labels: Mapping[str, str]) -> str:
    # An empty value matches containers that carry the label, whatever its value.
    return ",".join(
        f"labels.{_quote(k)}=={_quote(v)}" if v else f"labels.{_quote(k)}"
        for k, v in labels.items()
    )


@dataclass(frozen=True)
class _Stubs:
    containers: Any
    content: Any
    images: Any
    snapshots: Any
    tasks: Any


class ContainerdClient:
    """Every RPC carries the namespace header and a timeout; failures are typed errors."""

    _config: ContainerdClientConfig
    _channel: grpc.aio.Channel | None
    _stubs: _Stubs | None

    def __init__(self, config: ContainerdClientConfig) -> None:
        self._config = config
        self._channel = None
        self._stubs = None

    @property
    def snapshotter(self) -> str:
        return self._config.snapshotter

    async def connect(self) -> None:
        if self._channel is not None:
            return
        channel = grpc.aio.insecure_channel(_grpc_target(self._config.address))
        try:
            async with asyncio.timeout(self._config.call_timeout):
                await channel.channel_ready()
        except TimeoutError as e:
            await channel.close()
            raise ContainerdUnavailableError(
                f"containerd at {self._config.address} is not reachable"
            ) from e
        self._channel = channel
        self._stubs = _Stubs(
            containers=containers_pb2_grpc.ContainersStub(channel),
            content=content_pb2_grpc.ContentStub(channel),
            images=images_pb2_grpc.ImagesStub(channel),
            snapshots=snapshots_pb2_grpc.SnapshotsStub(channel),
            tasks=tasks_pb2_grpc.TasksStub(channel),
        )

    async def close(self) -> None:
        channel, self._channel, self._stubs = self._channel, None, None
        if channel is not None:
            await channel.close()

    def _require_stubs(self) -> _Stubs:
        if self._stubs is None:
            raise ContainerdUnavailableError("the containerd client is not connected")
        return self._stubs

    def _metadata(self) -> list[tuple[str, str]]:
        return [(NAMESPACE_HEADER, self._config.namespace)]

    def _failure(self, op: str, e: grpc.aio.AioRpcError) -> BackendAIError:
        if e.code() is grpc.StatusCode.UNAVAILABLE:
            return ContainerdUnavailableError(f"{op}: {e.details()}")
        return ContainerdOperationFailed(f"{op}: {e.code().name}: {e.details()}")

    async def _rpc(
        self,
        op: str,
        method: Callable[..., Awaitable[Any]],
        request: Any,
        *,
        tolerate: frozenset[grpc.StatusCode] = frozenset(),
    ) -> Any:
        """Call a unary RPC; a tolerated status code returns None."""
        try:
            return await method(
                request, metadata=self._metadata(), timeout=self._config.call_timeout
            )
        except grpc.aio.AioRpcError as e:
            if e.code() in tolerate:
                return None
            raise self._failure(op, e) from e

    # Images and content

    async def get_image_target(self, image_ref: str) -> ImageTarget:
        resp = await self._rpc(
            "get_image",
            self._require_stubs().images.Get,
            images_pb2.GetImageRequest(name=image_ref),
            tolerate=_NOT_FOUND,
        )
        if resp is None:
            raise ContainerdImageNotFound(
                f"image {image_ref} is not imported into the containerd namespace"
                f" {self._config.namespace}"
            )
        return ImageTarget(digest=resp.image.target.digest, media_type=resp.image.target.media_type)

    async def read_blob(self, digest: str) -> bytes:
        buf = bytearray()
        try:
            async with asyncio.timeout(self._config.call_timeout):
                async for resp in self._require_stubs().content.Read(
                    content_pb2.ReadContentRequest(digest=digest), metadata=self._metadata()
                ):
                    buf.extend(resp.data)
        except grpc.aio.AioRpcError as e:
            raise self._failure(f"read_content({digest})", e) from e
        except TimeoutError as e:
            raise ContainerdOperationFailed(f"read_content({digest}): timed out") from e
        return bytes(buf)

    # Snapshots

    async def prepare_snapshot(self, key: str, parent: str) -> Sequence[MountSpec]:
        resp = await self._rpc(
            "prepare_snapshot",
            self._require_stubs().snapshots.Prepare,
            snapshots_pb2.PrepareSnapshotRequest(
                snapshotter=self._config.snapshotter, key=key, parent=parent
            ),
        )
        return [
            MountSpec(type=m.type, source=m.source, options=tuple(m.options)) for m in resp.mounts
        ]

    async def remove_snapshot(self, key: str) -> None:
        await self._rpc(
            "remove_snapshot",
            self._require_stubs().snapshots.Remove,
            snapshots_pb2.RemoveSnapshotRequest(snapshotter=self._config.snapshotter, key=key),
            tolerate=_NOT_FOUND,
        )

    # Containers

    async def create_container(
        self, record: ContainerRecord, runtime: str, spec: Mapping[str, Any]
    ) -> None:
        container = containers_pb2.Container(
            id=record.id,
            image=record.image,
            runtime=containers_pb2.Container.Runtime(name=runtime),
            spec=any_pb2.Any(type_url=SPEC_TYPE_URL, value=json.dumps(dict(spec)).encode()),
            snapshotter=record.snapshotter,
            snapshot_key=record.snapshot_key,
            labels=dict(record.labels),
        )
        await self._rpc(
            "create_container",
            self._require_stubs().containers.Create,
            containers_pb2.CreateContainerRequest(container=container),
        )

    @staticmethod
    def _record(container: Any) -> ContainerRecord:
        return ContainerRecord(
            id=container.id,
            image=container.image,
            snapshotter=container.snapshotter,
            snapshot_key=container.snapshot_key,
            labels=dict(container.labels),
        )

    async def get_container(self, container_id: str) -> ContainerRecord | None:
        resp = await self._rpc(
            "get_container",
            self._require_stubs().containers.Get,
            containers_pb2.GetContainerRequest(id=container_id),
            tolerate=_NOT_FOUND,
        )
        return None if resp is None else self._record(resp.container)

    async def list_containers(self, labels: Mapping[str, str]) -> Sequence[ContainerRecord]:
        filters = [_label_filter(labels)] if labels else []
        resp = await self._rpc(
            "list_containers",
            self._require_stubs().containers.List,
            containers_pb2.ListContainersRequest(filters=filters),
        )
        return [self._record(c) for c in resp.containers]

    async def delete_container(self, container_id: str) -> None:
        await self._rpc(
            "delete_container",
            self._require_stubs().containers.Delete,
            containers_pb2.DeleteContainerRequest(id=container_id),
            tolerate=_NOT_FOUND,
        )

    # Tasks

    async def create_task(
        self, container_id: str, rootfs: Sequence[MountSpec], stdout: str, stderr: str
    ) -> int:
        resp = await self._rpc(
            "create_task",
            self._require_stubs().tasks.Create,
            tasks_pb2.CreateTaskRequest(
                container_id=container_id,
                rootfs=[
                    mount_pb2.Mount(type=m.type, source=m.source, options=list(m.options))
                    for m in rootfs
                ],
                stdout=stdout,
                stderr=stderr,
            ),
        )
        return int(resp.pid)

    async def start_task(self, container_id: str) -> None:
        await self._rpc(
            "start_task",
            self._require_stubs().tasks.Start,
            tasks_pb2.StartRequest(container_id=container_id),
        )

    async def get_task(self, container_id: str) -> TaskInfo | None:
        resp = await self._rpc(
            "get_task",
            self._require_stubs().tasks.Get,
            tasks_pb2.GetRequest(container_id=container_id),
            tolerate=_NOT_FOUND,
        )
        if resp is None:
            return None
        process = resp.process
        return TaskInfo(
            pid=int(process.pid),
            state=_TASK_STATES.get(int(process.status), TaskState.UNKNOWN),
            exit_status=int(process.exit_status),
        )

    async def kill_task(self, container_id: str, signum: int, *, all_processes: bool) -> None:
        await self._rpc(
            "kill_task",
            self._require_stubs().tasks.Kill,
            tasks_pb2.KillRequest(container_id=container_id, signal=signum, all=all_processes),
            tolerate=_NOT_FOUND,
        )

    async def delete_task(self, container_id: str) -> None:
        await self._rpc(
            "delete_task",
            self._require_stubs().tasks.Delete,
            tasks_pb2.DeleteTaskRequest(container_id=container_id),
            tolerate=_NOT_FOUND,
        )
