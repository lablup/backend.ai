"""Native containerd gRPC ``ContainerdRuntimeClient`` (BEP-1055).

Talks to the containerd daemon directly over its gRPC API (unix socket) — the sole
runtime client, with no ``nerdctl``/``ctr`` CLI dependency (and none of the CLI-imposed
limits such as nerdctl's 4 KiB ``nerdctl/mounts`` label). Implements the
``ContainerdRuntimeClient`` ABC, so the orchestrator and network layers are unchanged.

Covers the full ContainerdRuntimeClient surface over the containerd gRPC API alone (no
ctr/nerdctl), verified against live containerd v2.2.1: the connection, container/task
lifecycle (create via a hand-built OCI spec + snapshot, start/kill/remove), introspection,
image ops (exists/list/remove/entrypoint over the Images+Content services), and pull/push
over the Transfer service (an OCIRegistry <-> ImageStore transfer that also unpacks into
the snapshotter).
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, override

import grpc
from google.protobuf import any_pb2

from ai.backend.agent.containerd.runtime import ContainerdRuntimeClient, TaskHandle
from ai.backend.agent.containerd.runtime_spec import build_oci_runtime_spec
from ai.backend.common.arch import CURRENT_ARCH
from ai.backend.logging import BraceStyleAdapter

from ._grpcapi.api.services.containers.v1 import containers_pb2, containers_pb2_grpc
from ._grpcapi.api.services.content.v1 import content_pb2, content_pb2_grpc
from ._grpcapi.api.services.images.v1 import images_pb2, images_pb2_grpc
from ._grpcapi.api.services.snapshots.v1 import snapshots_pb2, snapshots_pb2_grpc
from ._grpcapi.api.services.tasks.v1 import tasks_pb2, tasks_pb2_grpc
from ._grpcapi.api.services.transfer.v1 import transfer_pb2, transfer_pb2_grpc
from ._grpcapi.api.types import mount_pb2
from ._grpcapi.api.types.transfer import imagestore_pb2, registry_pb2

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_ADDRESS = "unix:///run/containerd/containerd.sock"
# containerd multiplexes all objects by namespace; every RPC must carry it as metadata.
_NAMESPACE_HEADER = "containerd-namespace"
_RUNC_RUNTIME = "io.containerd.runc.v2"
_SNAPSHOTTER = "overlayfs"
_SPEC_TYPE_URL = "types.containerd.io/opencontainers/runtime-spec/1/Spec"
_INDEX_MEDIA_TYPES = frozenset({
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
})
# GOARCH names for platform matching in a multi-arch image index.
_GOARCH = {"aarch64": "arm64", "x86_64": "amd64"}

# containerd task status enum (api/types/task/task.proto) -> our string status.
_TASK_STATUS = {0: "unknown", 1: "created", 2: "running", 3: "stopped", 4: "paused", 5: "pausing"}


def _containerd_any(msg: Any) -> any_pb2.Any:
    """Wrap a message in an Any the way containerd's typeurl expects: the bare proto full
    name as the URL, NOT protobuf's ``type.googleapis.com/`` prefix (which the daemon's
    transfer plugin does not match on)."""
    return any_pb2.Any(type_url=msg.DESCRIPTOR.full_name, value=msg.SerializeToString())


def _chain_id(diff_ids: Sequence[str]) -> str:
    """OCI identity chain ID of an rootfs (diff_ids) — the snapshot key parent."""
    if not diff_ids:
        return ""
    chain = diff_ids[0]
    for diff_id in diff_ids[1:]:
        chain = "sha256:" + hashlib.sha256(f"{chain} {diff_id}".encode()).hexdigest()
    return chain


class ContainerdGrpcRuntimeClient(ContainerdRuntimeClient):
    _address: str
    _namespace: str
    _channel: grpc.aio.Channel | None
    _containers: containers_pb2_grpc.ContainersStub | None
    _tasks: tasks_pb2_grpc.TasksStub | None
    _images: images_pb2_grpc.ImagesStub | None
    _content: content_pb2_grpc.ContentStub | None
    _snapshots: snapshots_pb2_grpc.SnapshotsStub | None
    _transfer: transfer_pb2_grpc.TransferStub | None
    _rootfs: dict[str, list[mount_pb2.Mount]]

    def __init__(self, *, address: str = DEFAULT_ADDRESS, namespace: str = "backend-ai") -> None:
        self._address = address
        self._namespace = namespace
        self._channel = None
        self._containers = None
        self._tasks = None
        self._images = None
        self._content = None
        self._snapshots = None
        self._transfer = None
        self._rootfs: dict[str, list[mount_pb2.Mount]] = {}

    @override
    async def open(self) -> None:
        """Establish the gRPC channel and service stubs (idempotent)."""
        if self._channel is not None:
            return
        self._channel = grpc.aio.insecure_channel(self._address)
        self._containers = containers_pb2_grpc.ContainersStub(self._channel)
        self._tasks = tasks_pb2_grpc.TasksStub(self._channel)
        self._images = images_pb2_grpc.ImagesStub(self._channel)
        self._content = content_pb2_grpc.ContentStub(self._channel)
        self._snapshots = snapshots_pb2_grpc.SnapshotsStub(self._channel)
        self._transfer = transfer_pb2_grpc.TransferStub(self._channel)

    @override
    async def close(self) -> None:
        if self._channel is not None:
            await self._channel.close()
            self._channel = None
            self._containers = self._tasks = None
            self._images = self._content = self._snapshots = self._transfer = None

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

    def _images_stub(self) -> images_pb2_grpc.ImagesStub:
        if self._images is None:
            raise RuntimeError("ContainerdGrpcRuntimeClient is not open (call open() first)")
        return self._images

    def _content_stub(self) -> content_pb2_grpc.ContentStub:
        if self._content is None:
            raise RuntimeError("ContainerdGrpcRuntimeClient is not open (call open() first)")
        return self._content

    def _snapshots_stub(self) -> snapshots_pb2_grpc.SnapshotsStub:
        if self._snapshots is None:
            raise RuntimeError("ContainerdGrpcRuntimeClient is not open (call open() first)")
        return self._snapshots

    def _transfer_stub(self) -> transfer_pb2_grpc.TransferStub:
        if self._transfer is None:
            raise RuntimeError("ContainerdGrpcRuntimeClient is not open (call open() first)")
        return self._transfer

    # --- image content helpers (read the manifest chain to resolve the rootfs) ---

    def _resolve_volume_source(self, source: str) -> str:
        """Map a nerdctl named-volume source to its on-disk data dir (absolute paths pass
        through)."""
        if source.startswith("/"):
            return source
        hits = list(Path("/var/lib/nerdctl").glob(f"*/volumes/{self._namespace}/{source}/_data"))
        return str(hits[0]) if hits else source

    async def _read_content(self, digest: str) -> bytes:
        buf = bytearray()
        async for resp in self._content_stub().Read(
            content_pb2.ReadContentRequest(digest=digest), metadata=self._md
        ):
            buf.extend(resp.data)
        return bytes(buf)

    async def _resolve_image(self, image_ref: str) -> tuple[str, dict[str, Any]]:
        """Resolve an image to (rootfs chain_id, image config) for the current platform,
        following a multi-arch index down to this arch's manifest when present."""
        image = (
            await self._images_stub().Get(
                images_pb2.GetImageRequest(name=image_ref), metadata=self._md
            )
        ).image
        target = image.target
        if target.media_type in _INDEX_MEDIA_TYPES:
            index = json.loads(await self._read_content(target.digest))
            want = _GOARCH.get(CURRENT_ARCH, CURRENT_ARCH)
            manifest_digest = next(
                (
                    m["digest"]
                    for m in index["manifests"]
                    if m.get("platform", {}).get("architecture") == want
                    and m.get("platform", {}).get("os") == "linux"
                ),
                None,
            )
            if manifest_digest is None:
                raise RuntimeError(f"no linux/{want} manifest in index for {image_ref}")
            manifest = json.loads(await self._read_content(manifest_digest))
        else:
            manifest = json.loads(await self._read_content(target.digest))
        config = json.loads(await self._read_content(manifest["config"]["digest"]))
        return _chain_id(config["rootfs"]["diff_ids"]), config

    # --- container/task lifecycle (Phase 2) ---

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
        chain_id, image_config = await self._resolve_image(image_ref)
        # A mount source that is not an absolute path is a nerdctl *named volume* (e.g. the
        # krunner volume); nerdctl resolves it, but runc needs the real path. Resolve it to
        # the volume's data dir so the OCI runtime spec carries a valid bind source.
        oci_spec = {
            **oci_spec,
            "mounts": [
                {**m, "source": self._resolve_volume_source(str(m["source"]))}
                for m in oci_spec.get("mounts", [])
            ],
        }
        # Active snapshot for the writable rootfs, layered on the image's chain.
        prepared = await self._snapshots_stub().Prepare(
            snapshots_pb2.PrepareSnapshotRequest(
                snapshotter=_SNAPSHOTTER, key=container_id, parent=chain_id
            ),
            metadata=self._md,
        )
        self._rootfs[container_id] = list(prepared.mounts)
        # Merge the image's env (PATH, ...) *under* the kernel's env, and honor its WorkingDir.
        cfg = image_config.get("config") or {}
        env: dict[str, str] = {}
        for entry in cfg.get("Env") or []:
            key, _, value = str(entry).partition("=")
            env[key] = value
        env.update(oci_spec.get("env") or {})
        runtime_spec = build_oci_runtime_spec(
            {**oci_spec, "env": env},
            command=command,
            rootfs_path="rootfs",
            cwd=cfg.get("WorkingDir") or "/",
            hostname=container_id[:12],
        )
        spec_any = any_pb2.Any(type_url=_SPEC_TYPE_URL, value=json.dumps(runtime_spec).encode())
        container = containers_pb2.Container(
            id=container_id,
            image=image_ref,
            runtime=containers_pb2.Container.Runtime(name=_RUNC_RUNTIME),
            spec=spec_any,
            snapshotter=_SNAPSHOTTER,
            snapshot_key=container_id,
            labels=dict(oci_spec.get("labels") or {}),
        )
        await self._containers_stub().Create(
            containers_pb2.CreateContainerRequest(container=container), metadata=self._md
        )

    @override
    async def start_container(self, container_id: str) -> TaskHandle:
        resp = await self._tasks_stub().Create(
            tasks_pb2.CreateTaskRequest(
                container_id=container_id, rootfs=self._rootfs.get(container_id, [])
            ),
            metadata=self._md,
        )
        await self._tasks_stub().Start(
            tasks_pb2.StartRequest(container_id=container_id), metadata=self._md
        )
        return TaskHandle(container_id=container_id, pid=resp.pid)

    @override
    async def kill_container(self, container_id: str, *, signal: int) -> None:
        try:
            await self._tasks_stub().Kill(
                tasks_pb2.KillRequest(container_id=container_id, signal=signal, all=True),
                metadata=self._md,
            )
        except grpc.aio.AioRpcError as e:
            if e.code() is not grpc.StatusCode.NOT_FOUND:
                raise

    @override
    async def remove_container(self, container_id: str) -> None:
        # task -> container -> snapshot; each best-effort (already-gone is fine).
        for coro in (
            self._tasks_stub().Delete(
                tasks_pb2.DeleteTaskRequest(container_id=container_id), metadata=self._md
            ),
            self._containers_stub().Delete(
                containers_pb2.DeleteContainerRequest(id=container_id), metadata=self._md
            ),
            self._snapshots_stub().Remove(
                snapshots_pb2.RemoveSnapshotRequest(snapshotter=_SNAPSHOTTER, key=container_id),
                metadata=self._md,
            ),
        ):
            try:
                await coro
            except grpc.aio.AioRpcError as e:
                if e.code() is not grpc.StatusCode.NOT_FOUND:
                    raise
        self._rootfs.pop(container_id, None)

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

    # --- image service ---

    @override
    async def image_exists(self, image_ref: str) -> bool:
        try:
            await self._images_stub().Get(
                images_pb2.GetImageRequest(name=image_ref), metadata=self._md
            )
        except grpc.aio.AioRpcError as e:
            if e.code() is grpc.StatusCode.NOT_FOUND:
                return False
            raise
        return True

    @override
    async def list_images(self) -> Sequence[str]:
        resp = await self._images_stub().List(images_pb2.ListImagesRequest(), metadata=self._md)
        return [img.name for img in resp.images]

    @override
    async def remove_image(self, image_ref: str) -> None:
        try:
            await self._images_stub().Delete(
                images_pb2.DeleteImageRequest(name=image_ref), metadata=self._md
            )
        except grpc.aio.AioRpcError as e:
            if e.code() is not grpc.StatusCode.NOT_FOUND:
                raise

    @override
    async def image_entrypoint(self, image_ref: str) -> list[str] | None:
        try:
            _chain, config = await self._resolve_image(image_ref)
        except grpc.aio.AioRpcError as e:
            if e.code() is grpc.StatusCode.NOT_FOUND:
                return None
            raise
        cfg = config.get("config") or {}
        entry = cfg.get("Entrypoint") or cfg.get("Cmd")
        return [str(x) for x in entry] if entry else None

    @override
    async def pull_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None:
        # Pull server-side via the Transfer service: an OCIRegistry source streamed into an
        # ImageStore destination (which also unpacks into the snapshotter). Pure containerd
        # API — no ctr/nerdctl.
        resolver = registry_pb2.RegistryResolver()
        if auth and (user := auth.get("username")) and (pw := auth.get("password")):
            token = base64.b64encode(f"{user}:{pw}".encode()).decode()
            resolver.headers["Authorization"] = f"Basic {token}"
        source = _containerd_any(registry_pb2.OCIRegistry(reference=image_ref, resolver=resolver))
        destination = _containerd_any(
            imagestore_pb2.ImageStore(
                name=image_ref,
                unpacks=[imagestore_pb2.UnpackConfiguration(snapshotter=_SNAPSHOTTER)],
            )
        )
        await self._transfer_stub().Transfer(
            transfer_pb2.TransferRequest(source=source, destination=destination),
            metadata=self._md,
        )

    @override
    async def push_image(self, image_ref: str) -> None:
        # Reverse of pull: an ImageStore source pushed to an OCIRegistry destination.
        source = _containerd_any(imagestore_pb2.ImageStore(name=image_ref))
        destination = _containerd_any(registry_pb2.OCIRegistry(reference=image_ref))
        await self._transfer_stub().Transfer(
            transfer_pb2.TransferRequest(source=source, destination=destination),
            metadata=self._md,
        )
