"""Native containerd gRPC ``ContainerdRuntimeClient`` (BEP-1055).

Talks to the containerd daemon directly over its gRPC API (unix socket) instead of
shelling out to the ``nerdctl`` CLI, avoiding CLI overhead and CLI-imposed limits (e.g.
nerdctl's 4 KiB ``nerdctl/mounts`` label). Drop-in for ``NerdctlRuntimeClient``: it
implements the same ``ContainerdRuntimeClient`` ABC, so the orchestrator and network
layers are unchanged.

Built incrementally (see BEP-1055): this module currently covers the connection + the
read-only container/task introspection; container/task creation, snapshots, and image
ops land in subsequent phases. Unimplemented methods raise NotImplementedError so the
class stays importable and independently testable meanwhile.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any, override

import grpc

from ai.backend.agent.containerd.runtime import ContainerdRuntimeClient, TaskHandle
from ai.backend.logging import BraceStyleAdapter

from ._grpcapi.api.services.containers.v1 import containers_pb2, containers_pb2_grpc
from ._grpcapi.api.services.tasks.v1 import tasks_pb2, tasks_pb2_grpc

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_ADDRESS = "unix:///run/containerd/containerd.sock"
# containerd multiplexes all objects by namespace; every RPC must carry it as metadata.
_NAMESPACE_HEADER = "containerd-namespace"

# containerd task status enum (api/types/task/task.proto) -> our string status.
_TASK_STATUS = {0: "unknown", 1: "created", 2: "running", 3: "stopped", 4: "paused", 5: "pausing"}


class ContainerdGrpcRuntimeClient(ContainerdRuntimeClient):
    _address: str
    _namespace: str
    _channel: grpc.aio.Channel | None
    _containers: containers_pb2_grpc.ContainersStub | None
    _tasks: tasks_pb2_grpc.TasksStub | None

    def __init__(self, *, address: str = DEFAULT_ADDRESS, namespace: str = "backend-ai") -> None:
        self._address = address
        self._namespace = namespace
        self._channel = None
        self._containers = None
        self._tasks = None

    async def open(self) -> None:
        """Establish the gRPC channel and service stubs (idempotent)."""
        if self._channel is not None:
            return
        self._channel = grpc.aio.insecure_channel(self._address)
        self._containers = containers_pb2_grpc.ContainersStub(self._channel)
        self._tasks = tasks_pb2_grpc.TasksStub(self._channel)

    async def close(self) -> None:
        if self._channel is not None:
            await self._channel.close()
            self._channel = None
            self._containers = self._tasks = None

    @property
    def _md(self) -> list[tuple[str, str]]:
        return [(_NAMESPACE_HEADER, self._namespace)]

    def _containers_stub(self) -> containers_pb2_grpc.ContainersStub:
        if self._containers is None:
            raise RuntimeError("ContainerdGrpcRuntimeClient is not open (call open() first)")
        return self._containers

    def _tasks_stub(self) -> tasks_pb2_grpc.TasksStub:
        if self._tasks is None:
            raise RuntimeError("ContainerdGrpcRuntimeClient is not open (call open() first)")
        return self._tasks

    # --- container/task introspection (Phase 1) ---

    @override
    async def list_containers(self) -> Sequence[str]:
        resp: containers_pb2.ListContainersResponse = await self._containers_stub().List(
            containers_pb2.ListContainersRequest(), metadata=self._md
        )
        return [c.id for c in resp.containers]

    @override
    async def container_status(self, container_id: str) -> str | None:
        try:
            resp: tasks_pb2.GetResponse = await self._tasks_stub().Get(
                tasks_pb2.GetRequest(container_id=container_id), metadata=self._md
            )
        except grpc.aio.AioRpcError as e:
            if e.code() is grpc.StatusCode.NOT_FOUND:
                return None
            raise
        return _TASK_STATUS.get(resp.process.status, "unknown")

    @override
    async def container_pid(self, container_id: str) -> int | None:
        try:
            resp = await self._tasks_stub().Get(
                tasks_pb2.GetRequest(container_id=container_id), metadata=self._md
            )
        except grpc.aio.AioRpcError as e:
            if e.code() is grpc.StatusCode.NOT_FOUND:
                return None
            raise
        return resp.process.pid or None

    # --- not yet implemented (later phases) ---

    @override
    async def image_exists(self, image_ref: str) -> bool:
        raise NotImplementedError("containerd-grpc image ops: Phase 3")

    @override
    async def pull_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None:
        raise NotImplementedError("containerd-grpc image ops: Phase 3")

    @override
    async def list_images(self) -> Sequence[str]:
        raise NotImplementedError("containerd-grpc image ops: Phase 3")

    @override
    async def remove_image(self, image_ref: str) -> None:
        raise NotImplementedError("containerd-grpc image ops: Phase 3")

    @override
    async def push_image(self, image_ref: str) -> None:
        raise NotImplementedError("containerd-grpc image ops: Phase 3")

    @override
    async def image_entrypoint(self, image_ref: str) -> list[str] | None:
        raise NotImplementedError("containerd-grpc image ops: Phase 3")

    @override
    async def create_container(
        self,
        container_id: str,
        *,
        image_ref: str,
        command: Sequence[str],
        oci_spec: Mapping[str, Any],
        network: str = "none",
    ) -> None:
        raise NotImplementedError("containerd-grpc container/task lifecycle: Phase 2")

    @override
    async def start_container(self, container_id: str) -> TaskHandle:
        raise NotImplementedError("containerd-grpc container/task lifecycle: Phase 2")

    @override
    async def kill_container(self, container_id: str, *, signal: int) -> None:
        raise NotImplementedError("containerd-grpc container/task lifecycle: Phase 2")

    @override
    async def remove_container(self, container_id: str) -> None:
        raise NotImplementedError("containerd-grpc container/task lifecycle: Phase 2")

    @override
    async def container_ip(self, container_id: str) -> str | None:
        # The BEP-1055 network layer owns CNI/addressing; the runtime does not resolve IPs.
        return None

    @override
    async def create_network(self, name: str) -> None:
        # containerd has no "network" object (unlike nerdctl's named networks); the BEP-1055
        # network layer attaches CNI directly. Nothing to create at the runtime level.
        return None

    @override
    async def remove_network(self, name: str) -> None:
        return None
