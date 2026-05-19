"""Async client for containerd's native gRPC API.

The containerd-backend agent talks to the host's containerd over its
**native** gRPC API rather than the CRI API. Workloads are created in a
dedicated containerd metadata namespace (default ``backendai``) so that a
kubelet sharing the same containerd cannot see — and therefore cannot
garbage-collect — Backend.AI workloads: kubelet's CRI plugin only ever
enumerates the ``k8s.io`` namespace.

Every containerd API call is scoped by a ``containerd-namespace`` gRPC
metadata header; this client attaches it uniformly so callers never have
to think about it.

Currently exposed (grows as the agent layer needs more):

- ``version()`` — containerd health probe.
- ``ensure_namespace()`` / ``list_namespaces()`` — namespace bootstrap.
- ``pull_image()`` — image pull + unpack via the Transfer service.
- ``get_image()`` / ``list_images()`` — resolve / enumerate image records.
- ``get_image_oci_config()`` — read an image's OCI config (entrypoint, cmd, ...).
- ``prepare_image_rootfs()`` / ``prepare_snapshot()`` / ``remove_snapshot()``
  — prepare the container root filesystem from an image's layers.
- ``create_container()`` / ``delete_container()`` / ``list_containers()`` —
  the container metadata object (id, image, runtime, OCI spec, rootfs snapshot).
- ``create_task()`` / ``start_task()`` / ``get_task()`` / ``wait_task()`` /
  ``kill_task()`` / ``delete_task()`` — the running container process.

Everything goes through ``grpc.aio`` so the agent event loop stays
responsive.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from collections.abc import Mapping
from types import TracebackType
from typing import TYPE_CHECKING, Any, Self, TypeVar, cast

import grpc
from google.protobuf import any_pb2, empty_pb2
from google.protobuf.message import Message
from grpc.aio import AioRpcError

from ai.backend.agent.containerd.oci import OCI_SPEC_TYPE_URL
from ai.backend.agent.errors.containerd import (
    ContainerdConnectionError,
    ContainerdImageError,
    ContainerdRpcError,
)
from ai.backend.logging import BraceStyleAdapter

from .generated.containerd.services.containers.v1 import containers_pb2, containers_pb2_grpc
from .generated.containerd.services.content.v1 import content_pb2, content_pb2_grpc
from .generated.containerd.services.images.v1 import images_pb2, images_pb2_grpc
from .generated.containerd.services.namespaces.v1 import namespace_pb2, namespace_pb2_grpc
from .generated.containerd.services.snapshots.v1 import snapshots_pb2, snapshots_pb2_grpc
from .generated.containerd.services.tasks.v1 import tasks_pb2, tasks_pb2_grpc
from .generated.containerd.services.transfer.v1 import transfer_pb2, transfer_pb2_grpc
from .generated.containerd.services.version.v1 import version_pb2, version_pb2_grpc
from .generated.containerd.types import descriptor_pb2, mount_pb2, platform_pb2
from .generated.containerd.types.task import task_pb2
from .generated.containerd.types.transfer import imagestore_pb2, registry_pb2

if TYPE_CHECKING:
    # mypy-protobuf emits the *AsyncStub types for type-checking only
    # (decorated @type_check_only); importing them under TYPE_CHECKING
    # keeps the names available for annotations without a runtime import.
    from .generated.containerd.services.containers.v1.containers_pb2_grpc import (
        ContainersAsyncStub,
    )
    from .generated.containerd.services.content.v1.content_pb2_grpc import ContentAsyncStub
    from .generated.containerd.services.images.v1.images_pb2_grpc import ImagesAsyncStub
    from .generated.containerd.services.namespaces.v1.namespace_pb2_grpc import (
        NamespacesAsyncStub,
    )
    from .generated.containerd.services.snapshots.v1.snapshots_pb2_grpc import SnapshotsAsyncStub
    from .generated.containerd.services.tasks.v1.tasks_pb2_grpc import TasksAsyncStub
    from .generated.containerd.services.transfer.v1.transfer_pb2_grpc import TransferAsyncStub
    from .generated.containerd.services.version.v1.version_pb2_grpc import VersionAsyncStub

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_CONTAINERD_ADDRESS = "unix:///run/containerd/containerd.sock"

# Dedicated containerd metadata namespace for Backend.AI workloads. Kept
# distinct from kubelet's `k8s.io` so a co-located kubelet's CRI plugin
# never enumerates — and so never reaps — our containers.
DEFAULT_NAMESPACE = "backendai"

# containerd's default snapshotter; images are unpacked into it so a
# container's root filesystem can be prepared from the image layers.
DEFAULT_SNAPSHOTTER = "overlayfs"

# containerd runtime (shim) used to execute containers.
DEFAULT_RUNTIME = "io.containerd.runc.v2"

# Upper bound on waiting for the gRPC channel to become ready. grpc.aio
# retries forever otherwise, so an unreachable socket (containerd down,
# wrong path, missing permissions) would hang the caller with no
# actionable error.
DEFAULT_CONNECT_TIMEOUT_SECS: float = 5.0

# containerd scopes every request to a namespace carried in this gRPC
# metadata header. The Go client sets it from a context value; over raw
# gRPC it is an ordinary request header.
_NAMESPACE_HEADER = "containerd-namespace"

# `uname` machine name -> OCI/containerd architecture name.
_ARCH_ALIASES = {"x86_64": "amd64", "aarch64": "arm64"}

# Multi-platform image media types whose content is a list of per-platform
# manifests rather than a single manifest.
_INDEX_MEDIA_TYPES = frozenset({
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
})

_StubT = TypeVar("_StubT")


def _host_platform() -> platform_pb2.Platform:
    """Return the current host's containerd platform descriptor (linux)."""
    machine = os.uname().machine
    return platform_pb2.Platform(
        os="linux",
        architecture=_ARCH_ALIASES.get(machine, machine),
    )


def _containerd_any(message: Message) -> any_pb2.Any:
    """Pack a proto message into an ``Any`` using containerd's type-URL rule.

    containerd's ``typeurl`` registry keys objects by the *bare* protobuf
    message full name (``typeurl.TypeURL`` returns
    ``Descriptor().FullName()`` with no prefix). The standard
    ``Any.Pack()`` prefixes the URL with ``type.googleapis.com/``, which
    misses containerd's lookup — the Transfer service then reports
    "method Transfer not implemented for <type> to <type>" because it
    could not resolve the rich Go type behind the bare proto message.
    """
    return any_pb2.Any(
        type_url=message.DESCRIPTOR.full_name,
        value=message.SerializeToString(),
    )


def _chain_id(diff_ids: list[str]) -> str:
    """Compute an OCI rootfs chain ID from a list of layer diff IDs.

    ``chainID([]) = ""``; ``chainID([d]) = d``;
    ``chainID([d1..dn]) = sha256(chainID([d1..dn-1]) + " " + dn)``.
    This is the snapshot key under which containerd commits the unpacked
    image rootfs.
    """
    if not diff_ids:
        return ""
    chain = diff_ids[0]
    for diff_id in diff_ids[1:]:
        digest = hashlib.sha256(f"{chain} {diff_id}".encode()).hexdigest()
        chain = f"sha256:{digest}"
    return chain


class ContainerdClient:
    """High-level async client for the host's containerd native API.

    Use as an async context manager so the gRPC channel is always closed,
    even on cancellation::

        async with ContainerdClient() as cd:
            print(await cd.version())
    """

    _address: str
    _namespace: str
    _connect_timeout_secs: float
    _channel: grpc.aio.Channel | None
    # Annotations are deferred, so the TYPE_CHECKING-only *AsyncStub names
    # are safe to reference here. The generated sync Stub classes are
    # instantiated against an aio channel (their call methods become
    # awaitable) and cast to the aio-typed alias in connect().
    _version: VersionAsyncStub | None
    _namespaces: NamespacesAsyncStub | None
    _transfer: TransferAsyncStub | None
    _images: ImagesAsyncStub | None
    _content: ContentAsyncStub | None
    _snapshots: SnapshotsAsyncStub | None
    _containers: ContainersAsyncStub | None
    _tasks: TasksAsyncStub | None

    def __init__(
        self,
        address: str = DEFAULT_CONTAINERD_ADDRESS,
        *,
        namespace: str = DEFAULT_NAMESPACE,
        connect_timeout_secs: float = DEFAULT_CONNECT_TIMEOUT_SECS,
    ) -> None:
        self._address = address
        self._namespace = namespace
        self._connect_timeout_secs = connect_timeout_secs
        self._channel = None
        self._version = None
        self._namespaces = None
        self._transfer = None
        self._images = None
        self._content = None
        self._snapshots = None
        self._containers = None
        self._tasks = None

    @property
    def namespace(self) -> str:
        """The containerd metadata namespace this client operates in."""
        return self._namespace

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def connect(self) -> None:
        """Open the gRPC channel to containerd and wait until it is ready.

        The ``channel_ready()`` probe is wrapped in a timeout because
        grpc.aio retries forever otherwise — an unreachable socket would
        hang the caller indefinitely with no log line to diagnose.
        """
        if self._channel is not None:
            return
        log.debug("Opening containerd channel to {}", self._address)
        channel = grpc.aio.insecure_channel(self._address)
        try:
            await asyncio.wait_for(channel.channel_ready(), timeout=self._connect_timeout_secs)
        except TimeoutError as exc:
            await channel.close()
            raise ContainerdConnectionError(
                f"Timed out after {self._connect_timeout_secs:.1f}s waiting for containerd "
                f"at {self._address}. Check that containerd is running and the socket "
                f"path / permissions are correct."
            ) from exc
        except AioRpcError as exc:
            await channel.close()
            raise ContainerdConnectionError(
                f"Could not connect to containerd at {self._address}: {exc.details()}"
            ) from exc
        self._channel = channel
        # The generated sync `*Stub` classes work transparently over an aio
        # channel — their call methods return awaitables — but mypy types
        # the constructor as the sync stub, so cast to the aio-typed alias
        # (a forward-ref string; the names are TYPE_CHECKING-only).
        self._version = cast("VersionAsyncStub", version_pb2_grpc.VersionStub(channel))
        self._namespaces = cast("NamespacesAsyncStub", namespace_pb2_grpc.NamespacesStub(channel))
        self._transfer = cast("TransferAsyncStub", transfer_pb2_grpc.TransferStub(channel))
        self._images = cast("ImagesAsyncStub", images_pb2_grpc.ImagesStub(channel))
        self._content = cast("ContentAsyncStub", content_pb2_grpc.ContentStub(channel))
        self._snapshots = cast("SnapshotsAsyncStub", snapshots_pb2_grpc.SnapshotsStub(channel))
        self._containers = cast("ContainersAsyncStub", containers_pb2_grpc.ContainersStub(channel))
        self._tasks = cast("TasksAsyncStub", tasks_pb2_grpc.TasksStub(channel))

    async def close(self) -> None:
        if self._channel is None:
            return
        await self._channel.close()
        self._channel = None
        self._version = None
        self._namespaces = None
        self._transfer = None
        self._images = None
        self._content = None
        self._snapshots = None
        self._containers = None
        self._tasks = None

    @property
    def _metadata(self) -> tuple[tuple[str, str], ...]:
        """gRPC metadata scoping every call to this client's namespace."""
        return ((_NAMESPACE_HEADER, self._namespace),)

    async def version(self) -> version_pb2.VersionResponse:
        """Return containerd's version info — used as a health probe."""
        stub = self._require(self._version)
        try:
            response: version_pb2.VersionResponse = await stub.Version(
                empty_pb2.Empty(), metadata=self._metadata
            )
        except AioRpcError as exc:
            raise ContainerdConnectionError(
                f"containerd Version() call against {self._address} failed: {exc.details()}"
            ) from exc
        return response

    async def list_namespaces(self) -> list[namespace_pb2.Namespace]:
        """List the containerd metadata namespaces known to the daemon."""
        stub = self._require(self._namespaces)
        try:
            response: namespace_pb2.ListNamespacesResponse = await stub.List(
                namespace_pb2.ListNamespacesRequest(), metadata=self._metadata
            )
        except AioRpcError as exc:
            raise ContainerdRpcError(f"containerd ListNamespaces failed: {exc.details()}") from exc
        return list(response.namespaces)

    async def ensure_namespace(self) -> None:
        """Create this client's containerd namespace if it does not exist.

        containerd has no idempotent create, so an ``ALREADY_EXISTS`` status
        is treated as success.
        """
        stub = self._require(self._namespaces)
        request = namespace_pb2.CreateNamespaceRequest(
            namespace=namespace_pb2.Namespace(name=self._namespace),
        )
        try:
            await stub.Create(request, metadata=self._metadata)
        except AioRpcError as exc:
            if exc.code() is grpc.StatusCode.ALREADY_EXISTS:
                return
            raise ContainerdRpcError(
                f"containerd CreateNamespace '{self._namespace}' failed: {exc.details()}"
            ) from exc

    async def pull_image(
        self,
        ref: str,
        *,
        platform: platform_pb2.Platform | None = None,
        snapshotter: str = DEFAULT_SNAPSHOTTER,
    ) -> str:
        """Pull an image into this namespace and unpack it for the platform.

        Uses containerd's Transfer service, which performs the full pull +
        unpack server-side (registry fetch, content store, snapshot
        unpack) — the client only describes the source (an OCI registry
        reference) and the destination (the image store, with an unpack
        configuration). The call blocks until the pull completes; per-byte
        progress streaming is not exposed yet.

        ``ref`` is a registry reference such as
        ``docker.io/library/busybox:latest``. Returns ``ref`` unchanged.
        """
        stub = self._require(self._transfer)
        target_platform = platform if platform is not None else _host_platform()
        source = _containerd_any(registry_pb2.OCIRegistry(reference=ref))
        destination = _containerd_any(
            imagestore_pb2.ImageStore(
                name=ref,
                platforms=[target_platform],
                unpacks=[
                    imagestore_pb2.UnpackConfiguration(
                        platform=target_platform,
                        snapshotter=snapshotter,
                    ),
                ],
            )
        )
        request = transfer_pb2.TransferRequest(source=source, destination=destination)
        try:
            await stub.Transfer(request, metadata=self._metadata)
        except AioRpcError as exc:
            raise ContainerdRpcError(
                f"containerd Transfer (pull '{ref}') failed: {exc.details()}"
            ) from exc
        return ref

    async def get_image(self, ref: str) -> images_pb2.Image:
        """Return the image record (name -> content descriptor) for ``ref``.

        Raises ``ContainerdImageError`` if the image is unknown to containerd
        in this namespace; callers can catch that distinctly from a
        generic ``ContainerdRpcError``.
        """
        stub = self._require(self._images)
        try:
            response: images_pb2.GetImageResponse = await stub.Get(
                images_pb2.GetImageRequest(name=ref), metadata=self._metadata
            )
        except AioRpcError as exc:
            if exc.code() is grpc.StatusCode.NOT_FOUND:
                raise ContainerdImageError(
                    f"containerd has no image '{ref}' in namespace '{self._namespace}'"
                ) from exc
            raise ContainerdRpcError(
                f"containerd GetImage '{ref}' failed: {exc.details()}"
            ) from exc
        return response.image

    async def list_images(self) -> list[images_pb2.Image]:
        """List every image record in this namespace."""
        stub = self._require(self._images)
        try:
            response: images_pb2.ListImagesResponse = await stub.List(
                images_pb2.ListImagesRequest(), metadata=self._metadata
            )
        except AioRpcError as exc:
            raise ContainerdRpcError(f"containerd ListImages failed: {exc.details()}") from exc
        return list(response.images)

    async def get_image_oci_config(self, ref: str) -> dict[str, Any]:
        """Return an image's OCI image config document.

        The returned mapping is the JSON config blob the image manifest
        points at — its ``config`` holds the container ``Entrypoint`` /
        ``Cmd`` / ``Env`` / ``Labels``, and ``rootfs`` the layer diff IDs.
        """
        image = await self.get_image(ref)
        return await self._read_image_config(image.target)

    async def prepare_image_rootfs(
        self,
        image_ref: str,
        snapshot_key: str,
        *,
        snapshotter: str = DEFAULT_SNAPSHOTTER,
    ) -> list[mount_pb2.Mount]:
        """Prepare a writable container root filesystem from an image.

        Resolves the image's rootfs chain ID (the key of the committed
        snapshot containerd produced when unpacking the image) and prepares
        a new active snapshot on top of it. Returns the mounts that make up
        the container root filesystem — these are handed to ``Tasks.Create``.
        """
        image = await self.get_image(image_ref)
        chain_id = await self._resolve_chain_id(image.target)
        return await self.prepare_snapshot(snapshot_key, chain_id, snapshotter=snapshotter)

    async def prepare_snapshot(
        self,
        key: str,
        parent: str,
        *,
        snapshotter: str = DEFAULT_SNAPSHOTTER,
    ) -> list[mount_pb2.Mount]:
        """Prepare an active snapshot ``key`` on top of ``parent``; return mounts."""
        stub = self._require(self._snapshots)
        request = snapshots_pb2.PrepareSnapshotRequest(
            snapshotter=snapshotter,
            key=key,
            parent=parent,
        )
        try:
            response: snapshots_pb2.PrepareSnapshotResponse = await stub.Prepare(
                request, metadata=self._metadata
            )
        except AioRpcError as exc:
            raise ContainerdRpcError(
                f"containerd PrepareSnapshot '{key}' failed: {exc.details()}"
            ) from exc
        return list(response.mounts)

    async def remove_snapshot(self, key: str, *, snapshotter: str = DEFAULT_SNAPSHOTTER) -> None:
        """Remove a snapshot by key."""
        stub = self._require(self._snapshots)
        request = snapshots_pb2.RemoveSnapshotRequest(snapshotter=snapshotter, key=key)
        try:
            await stub.Remove(request, metadata=self._metadata)
        except AioRpcError as exc:
            raise ContainerdRpcError(
                f"containerd RemoveSnapshot '{key}' failed: {exc.details()}"
            ) from exc

    async def _read_content(self, digest: str) -> bytes:
        """Read a content-store blob in full by digest."""
        stub = self._require(self._content)
        request = content_pb2.ReadContentRequest(digest=digest)
        chunks: list[bytes] = []
        try:
            async for response in stub.Read(request, metadata=self._metadata):
                chunks.append(response.data)
        except AioRpcError as exc:
            raise ContainerdRpcError(
                f"containerd ReadContent '{digest}' failed: {exc.details()}"
            ) from exc
        return b"".join(chunks)

    async def _read_image_config(self, target: descriptor_pb2.Descriptor) -> dict[str, Any]:
        """Walk an image's content (index -> manifest -> config) and return
        the parsed OCI image config document for the host platform."""
        document: Any = json.loads(await self._read_content(target.digest))
        if target.media_type in _INDEX_MEDIA_TYPES:
            host = _host_platform()
            manifest_digest: str | None = None
            for entry in document.get("manifests", []):
                entry_platform = entry.get("platform") or {}
                if (
                    entry_platform.get("os") == host.os
                    and entry_platform.get("architecture") == host.architecture
                ):
                    manifest_digest = entry.get("digest")
                    break
            if not manifest_digest:
                raise ContainerdRpcError(
                    f"image index {target.digest} has no manifest for {host.os}/{host.architecture}"
                )
            document = json.loads(await self._read_content(manifest_digest))
        config = document.get("config")
        if not isinstance(config, dict) or not config.get("digest"):
            raise ContainerdRpcError(f"image manifest {target.digest} has no config descriptor")
        image_config: Any = json.loads(await self._read_content(config["digest"]))
        if not isinstance(image_config, dict):
            raise ContainerdRpcError(f"image config for {target.digest} is not a JSON object")
        return image_config

    async def _resolve_chain_id(self, target: descriptor_pb2.Descriptor) -> str:
        """Return the rootfs chain ID (snapshot key) for an image's host-platform layers."""
        image_config = await self._read_image_config(target)
        diff_ids = image_config.get("rootfs", {}).get("diff_ids", [])
        return _chain_id([str(diff_id) for diff_id in diff_ids])

    async def create_container(
        self,
        container_id: str,
        *,
        image: str,
        spec: dict[str, Any],
        snapshot_key: str,
        runtime: str = DEFAULT_RUNTIME,
        snapshotter: str = DEFAULT_SNAPSHOTTER,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        """Create the container metadata object in containerd's store.

        This records the container (its image, runtime, OCI spec and rootfs
        snapshot) but does not start anything — a task must be created from
        it to run the process. ``spec`` is the OCI runtime spec dict (see
        ``oci.build_oci_spec``); containerd stores it as a typeurl-tagged
        JSON blob, not a protobuf message.
        """
        stub = self._require(self._containers)
        container = containers_pb2.Container(
            id=container_id,
            image=image,
            runtime=containers_pb2.Container.Runtime(name=runtime),
            spec=any_pb2.Any(
                type_url=OCI_SPEC_TYPE_URL,
                value=json.dumps(spec).encode(),
            ),
            snapshotter=snapshotter,
            snapshot_key=snapshot_key,
            labels=dict(labels or {}),
        )
        request = containers_pb2.CreateContainerRequest(container=container)
        try:
            await stub.Create(request, metadata=self._metadata)
        except AioRpcError as exc:
            raise ContainerdRpcError(
                f"containerd CreateContainer '{container_id}' failed: {exc.details()}"
            ) from exc

    async def delete_container(self, container_id: str) -> None:
        """Delete a container metadata object (its task must already be gone)."""
        stub = self._require(self._containers)
        request = containers_pb2.DeleteContainerRequest(id=container_id)
        try:
            await stub.Delete(request, metadata=self._metadata)
        except AioRpcError as exc:
            raise ContainerdRpcError(
                f"containerd DeleteContainer '{container_id}' failed: {exc.details()}"
            ) from exc

    async def list_containers(self) -> list[containers_pb2.Container]:
        """List every container metadata object in this namespace."""
        stub = self._require(self._containers)
        try:
            response: containers_pb2.ListContainersResponse = await stub.List(
                containers_pb2.ListContainersRequest(), metadata=self._metadata
            )
        except AioRpcError as exc:
            raise ContainerdRpcError(f"containerd ListContainers failed: {exc.details()}") from exc
        return list(response.containers)

    async def create_task(
        self,
        container_id: str,
        *,
        rootfs: list[mount_pb2.Mount],
    ) -> int:
        """Create a task (the runc process) for an existing container.

        ``rootfs`` is the list of mounts from the container's prepared
        snapshot; the runc shim performs these mounts before exec'ing the
        container process. The task is created but not started — call
        ``start_task``. stdio is left empty (the process gets no attached
        streams), which suits non-interactive workloads. Returns the pid.
        """
        stub = self._require(self._tasks)
        request = tasks_pb2.CreateTaskRequest(container_id=container_id, rootfs=rootfs)
        try:
            response: tasks_pb2.CreateTaskResponse = await stub.Create(
                request, metadata=self._metadata
            )
        except AioRpcError as exc:
            raise ContainerdRpcError(
                f"containerd CreateTask '{container_id}' failed: {exc.details()}"
            ) from exc
        return response.pid

    async def start_task(self, container_id: str) -> int:
        """Start a previously created task; return the process pid."""
        stub = self._require(self._tasks)
        request = tasks_pb2.StartRequest(container_id=container_id)
        try:
            response: tasks_pb2.StartResponse = await stub.Start(request, metadata=self._metadata)
        except AioRpcError as exc:
            raise ContainerdRpcError(
                f"containerd StartTask '{container_id}' failed: {exc.details()}"
            ) from exc
        return response.pid

    async def get_task(self, container_id: str) -> task_pb2.Process:
        """Return a task's current process state (status, pid, ...)."""
        stub = self._require(self._tasks)
        request = tasks_pb2.GetRequest(container_id=container_id)
        try:
            response: tasks_pb2.GetResponse = await stub.Get(request, metadata=self._metadata)
        except AioRpcError as exc:
            raise ContainerdRpcError(
                f"containerd GetTask '{container_id}' failed: {exc.details()}"
            ) from exc
        return cast(task_pb2.Process, response.process)

    async def wait_task(self, container_id: str) -> int:
        """Block until a task exits; return its exit status."""
        stub = self._require(self._tasks)
        request = tasks_pb2.WaitRequest(container_id=container_id)
        try:
            response: tasks_pb2.WaitResponse = await stub.Wait(request, metadata=self._metadata)
        except AioRpcError as exc:
            raise ContainerdRpcError(
                f"containerd WaitTask '{container_id}' failed: {exc.details()}"
            ) from exc
        return response.exit_status

    async def kill_task(self, container_id: str, *, signal_number: int = 9) -> None:
        """Send a signal to a task's processes (default 9 = SIGKILL)."""
        stub = self._require(self._tasks)
        request = tasks_pb2.KillRequest(
            container_id=container_id,
            signal=signal_number,
            all=True,
        )
        try:
            await stub.Kill(request, metadata=self._metadata)
        except AioRpcError as exc:
            raise ContainerdRpcError(
                f"containerd KillTask '{container_id}' failed: {exc.details()}"
            ) from exc

    async def delete_task(self, container_id: str) -> tasks_pb2.DeleteResponse:
        """Delete a stopped task and its on-disk state; return exit info."""
        stub = self._require(self._tasks)
        request = tasks_pb2.DeleteTaskRequest(container_id=container_id)
        try:
            response: tasks_pb2.DeleteResponse = await stub.Delete(request, metadata=self._metadata)
        except AioRpcError as exc:
            raise ContainerdRpcError(
                f"containerd DeleteTask '{container_id}' failed: {exc.details()}"
            ) from exc
        return response

    def _require(self, stub: _StubT | None) -> _StubT:
        if stub is None:
            raise ContainerdConnectionError(
                "containerd client is not connected; call connect() or use it "
                "as an async context manager."
            )
        return stub
