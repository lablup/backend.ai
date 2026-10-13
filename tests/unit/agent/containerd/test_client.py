"""The client against an in-process gRPC server speaking the vendored containerd services."""

from __future__ import annotations

import asyncio
import json
import tempfile
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any

import grpc
import pytest

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
from ai.backend.agent.containerd._grpcapi.api.types import descriptor_pb2, mount_pb2
from ai.backend.agent.containerd._grpcapi.api.types.task import task_pb2
from ai.backend.agent.containerd.client import (
    NAMESPACE_HEADER,
    SPEC_TYPE_URL,
    ContainerdClient,
    ContainerdClientConfig,
    ContainerRecord,
    MountSpec,
    TaskState,
)
from ai.backend.agent.errors.containerd import (
    ContainerdImageNotFound,
    ContainerdOperationFailed,
    ContainerdUnavailableError,
)


class Backend:
    """What the fake containerd services answer, and what they saw."""

    namespaces: list[str]
    created: list[Any]
    list_filters: list[list[str]]
    task_state: int | None
    fail_code: grpc.StatusCode | None
    delay_sec: float

    def __init__(self) -> None:
        self.namespaces = []
        self.created = []
        self.list_filters = []
        self.task_state = None
        self.fail_code = None
        self.delay_sec = 0.0

    async def enter(self, context: Any) -> None:
        self.namespaces.append(dict(context.invocation_metadata()).get(NAMESPACE_HEADER, ""))
        if self.delay_sec:
            await asyncio.sleep(self.delay_sec)
        if self.fail_code is not None:
            await context.abort(self.fail_code, "injected")


class Servicer:
    """The generated add_*_to_server looks every method up by name; unimplemented ones abort."""

    def __getattr__(self, name: str) -> Any:
        async def unimplemented(request: Any, context: Any) -> None:
            await context.abort(grpc.StatusCode.UNIMPLEMENTED, name)

        return unimplemented


class Images(Servicer):
    def __init__(self, backend: Backend) -> None:
        self.backend = backend

    async def Get(self, request: Any, context: Any) -> Any:
        await self.backend.enter(context)
        if request.name != "img:1":
            await context.abort(grpc.StatusCode.NOT_FOUND, "no such image")
        target = descriptor_pb2.Descriptor(media_type="application/vnd.oci.image.index.v1+json")
        target.digest = "sha256:index"
        return images_pb2.GetImageResponse(image=images_pb2.Image(name=request.name, target=target))


class Content(Servicer):
    def __init__(self, backend: Backend) -> None:
        self.backend = backend

    async def Read(self, request: Any, context: Any) -> AsyncIterator[Any]:
        await self.backend.enter(context)
        for chunk in (b"abc", b"def"):
            yield content_pb2.ReadContentResponse(offset=0, data=chunk)


class Snapshots(Servicer):
    def __init__(self, backend: Backend) -> None:
        self.backend = backend

    async def Prepare(self, request: Any, context: Any) -> Any:
        await self.backend.enter(context)
        mount = mount_pb2.Mount(type="overlay", source="overlay", options=["lowerdir=/a"])
        return snapshots_pb2.PrepareSnapshotResponse(mounts=[mount])

    async def Remove(self, request: Any, context: Any) -> Any:
        await self.backend.enter(context)
        await context.abort(grpc.StatusCode.NOT_FOUND, "no such snapshot")


class Containers(Servicer):
    def __init__(self, backend: Backend) -> None:
        self.backend = backend

    async def Create(self, request: Any, context: Any) -> Any:
        await self.backend.enter(context)
        self.backend.created.append(request.container)
        return containers_pb2.CreateContainerResponse(container=request.container)

    async def Get(self, request: Any, context: Any) -> Any:
        await self.backend.enter(context)
        await context.abort(grpc.StatusCode.NOT_FOUND, "no such container")

    async def List(self, request: Any, context: Any) -> Any:
        await self.backend.enter(context)
        self.backend.list_filters.append(list(request.filters))
        found = containers_pb2.Container(
            id="c1", image="img:1", snapshotter="overlayfs", snapshot_key="c1", labels={"k": "v"}
        )
        return containers_pb2.ListContainersResponse(containers=[found])

    async def Delete(self, request: Any, context: Any) -> Any:
        await self.backend.enter(context)
        await context.abort(grpc.StatusCode.NOT_FOUND, "no such container")


class Tasks(Servicer):
    def __init__(self, backend: Backend) -> None:
        self.backend = backend

    async def Create(self, request: Any, context: Any) -> Any:
        await self.backend.enter(context)
        self.backend.created.append(request)
        return tasks_pb2.CreateTaskResponse(container_id=request.container_id, pid=4242)

    async def Get(self, request: Any, context: Any) -> Any:
        await self.backend.enter(context)
        if self.backend.task_state is None:
            await context.abort(grpc.StatusCode.NOT_FOUND, "no such task")
        process = task_pb2.Process(
            container_id=request.container_id, pid=7, status=self.backend.task_state, exit_status=3
        )
        return tasks_pb2.GetResponse(process=process)

    async def Kill(self, request: Any, context: Any) -> Any:
        await self.backend.enter(context)
        await context.abort(grpc.StatusCode.NOT_FOUND, "no such task")

    async def Delete(self, request: Any, context: Any) -> Any:
        await self.backend.enter(context)
        await context.abort(grpc.StatusCode.NOT_FOUND, "no such task")


@pytest.fixture
def socket_path() -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="cd") as tmp:
        yield Path(tmp) / "c.sock"


@pytest.fixture
def backend() -> Backend:
    return Backend()


@pytest.fixture
async def server(socket_path: Path, backend: Backend) -> AsyncIterator[None]:
    srv = grpc.aio.server()
    images_pb2_grpc.add_ImagesServicer_to_server(Images(backend), srv)
    content_pb2_grpc.add_ContentServicer_to_server(Content(backend), srv)
    snapshots_pb2_grpc.add_SnapshotsServicer_to_server(Snapshots(backend), srv)
    containers_pb2_grpc.add_ContainersServicer_to_server(Containers(backend), srv)
    tasks_pb2_grpc.add_TasksServicer_to_server(Tasks(backend), srv)
    srv.add_insecure_port(f"unix://{socket_path}")
    await srv.start()
    yield
    await srv.stop(None)


@pytest.fixture
async def client(server: None, socket_path: Path) -> AsyncIterator[ContainerdClient]:
    c = ContainerdClient(
        ContainerdClientConfig(
            address=str(socket_path), namespace="ns-test", snapshotter="overlayfs", call_timeout=2.0
        )
    )
    await c.connect()
    yield c
    await c.close()


class TestImages:
    async def test_target_is_returned(self, client: ContainerdClient) -> None:
        target = await client.get_image_target("img:1")

        assert target.digest == "sha256:index"
        assert target.media_type == "application/vnd.oci.image.index.v1+json"

    async def test_missing_image_is_a_typed_error(self, client: ContainerdClient) -> None:
        with pytest.raises(ContainerdImageNotFound, match="ns-test"):
            await client.get_image_target("absent:1")

    async def test_streamed_blob_is_joined(self, client: ContainerdClient) -> None:
        assert await client.read_blob("sha256:x") == b"abcdef"


class TestContainers:
    async def test_create_sends_runtime_spec_snapshot_and_labels(
        self, client: ContainerdClient, backend: Backend
    ) -> None:
        record = ContainerRecord(
            id="c1", image="img:1", snapshotter="overlayfs", snapshot_key="c1", labels={"a": "b"}
        )

        await client.create_container(record, "io.containerd.runc.v2", {"ociVersion": "1.1.0"})

        [sent] = backend.created
        assert sent.id == "c1"
        assert sent.runtime.name == "io.containerd.runc.v2"
        assert sent.snapshotter == "overlayfs" and sent.snapshot_key == "c1"
        assert dict(sent.labels) == {"a": "b"}
        assert sent.spec.type_url == SPEC_TYPE_URL
        assert json.loads(sent.spec.value) == {"ociVersion": "1.1.0"}

    async def test_list_sends_a_label_filter(
        self, client: ContainerdClient, backend: Backend
    ) -> None:
        records = await client.list_containers({
            "ai.backend.owner": "agent-1",
            "ai.backend.kernel-id": "",
        })

        assert backend.list_filters == [
            ['labels."ai.backend.owner"=="agent-1",labels."ai.backend.kernel-id"']
        ]
        assert [(r.id, r.snapshot_key, dict(r.labels)) for r in records] == [
            ("c1", "c1", {"k": "v"})
        ]

    async def test_filter_values_are_quoted(
        self, client: ContainerdClient, backend: Backend
    ) -> None:
        await client.list_containers({"k": 'a"b'})

        assert backend.list_filters == [['labels."k"=="a\\"b"']]

    async def test_missing_container_is_none(self, client: ContainerdClient) -> None:
        assert await client.get_container("absent") is None

    async def test_delete_of_a_missing_container_is_tolerated(
        self, client: ContainerdClient
    ) -> None:
        await client.delete_container("absent")


class TestSnapshots:
    async def test_prepare_returns_the_rootfs_mounts(self, client: ContainerdClient) -> None:
        mounts = await client.prepare_snapshot("c1", "sha256:parent")

        assert mounts == [MountSpec("overlay", "overlay", ("lowerdir=/a",))]

    async def test_remove_of_a_missing_snapshot_is_tolerated(
        self, client: ContainerdClient
    ) -> None:
        await client.remove_snapshot("absent")


class TestTasks:
    async def test_create_returns_the_pid_and_passes_rootfs_and_stdio(
        self, client: ContainerdClient, backend: Backend
    ) -> None:
        pid = await client.create_task(
            "c1", [MountSpec("overlay", "overlay", ("a",))], "file:///log", "file:///log"
        )

        assert pid == 4242
        [sent] = backend.created
        assert sent.container_id == "c1"
        assert [(m.type, list(m.options)) for m in sent.rootfs] == [("overlay", ["a"])]
        assert sent.stdout == "file:///log" and sent.stderr == "file:///log"

    @pytest.mark.parametrize(
        ("code", "state"),
        [
            (1, TaskState.CREATED),
            (2, TaskState.RUNNING),
            (3, TaskState.STOPPED),
            (4, TaskState.PAUSED),
        ],
    )
    async def test_task_state_is_mapped(
        self, client: ContainerdClient, backend: Backend, code: int, state: TaskState
    ) -> None:
        backend.task_state = code

        task = await client.get_task("c1")

        assert task is not None
        assert (task.pid, task.state, task.exit_status) == (7, state, 3)

    async def test_missing_task_is_none(self, client: ContainerdClient) -> None:
        assert await client.get_task("c1") is None

    async def test_kill_and_delete_of_a_missing_task_are_tolerated(
        self, client: ContainerdClient
    ) -> None:
        await client.kill_task("c1", 9, all_processes=True)
        await client.delete_task("c1")


class TestRequestBasics:
    async def test_every_call_carries_the_namespace_header(
        self, client: ContainerdClient, backend: Backend
    ) -> None:
        await client.get_image_target("img:1")
        await client.read_blob("sha256:x")
        await client.prepare_snapshot("c1", "p")
        await client.list_containers({})
        await client.get_task("c1")

        assert backend.namespaces == ["ns-test"] * 5

    async def test_server_error_is_wrapped(
        self, client: ContainerdClient, backend: Backend
    ) -> None:
        backend.fail_code = grpc.StatusCode.INTERNAL

        with pytest.raises(ContainerdOperationFailed, match="list_containers: INTERNAL"):
            await client.list_containers({})

    async def test_unavailable_is_its_own_error(
        self, client: ContainerdClient, backend: Backend
    ) -> None:
        backend.fail_code = grpc.StatusCode.UNAVAILABLE

        with pytest.raises(ContainerdUnavailableError):
            await client.list_containers({})

    async def test_slow_call_times_out_as_a_typed_error(
        self, client: ContainerdClient, backend: Backend
    ) -> None:
        backend.delay_sec = 5.0

        with pytest.raises(ContainerdOperationFailed, match="DEADLINE_EXCEEDED"):
            await client.list_containers({})

    async def test_slow_blob_read_times_out_as_a_typed_error(
        self, client: ContainerdClient, backend: Backend
    ) -> None:
        backend.delay_sec = 5.0

        with pytest.raises(ContainerdOperationFailed):
            await client.read_blob("sha256:x")


class TestConnection:
    async def test_unreachable_socket_fails_to_connect(self, socket_path: Path) -> None:
        client = ContainerdClient(
            ContainerdClientConfig(
                address=str(socket_path), namespace="ns", snapshotter="overlayfs", call_timeout=0.3
            )
        )

        with pytest.raises(ContainerdUnavailableError):
            await client.connect()

    async def test_calls_before_connect_are_refused(self, socket_path: Path) -> None:
        client = ContainerdClient(
            ContainerdClientConfig(
                address=str(socket_path), namespace="ns", snapshotter="overlayfs"
            )
        )

        with pytest.raises(ContainerdUnavailableError):
            await client.get_task("c1")

    async def test_close_is_idempotent(self, client: ContainerdClient) -> None:
        await client.close()
        await client.close()
