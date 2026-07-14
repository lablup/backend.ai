"""Native containerd gRPC OCI runtime (BEP-1062).

Talks to the containerd daemon directly over its gRPC API (unix socket) — the sole
runtime client, with no ``nerdctl``/``ctr`` CLI dependency (and none of the CLI-imposed
limits such as nerdctl's 4 KiB ``nerdctl/mounts`` label). Implements the
``OciRuntime`` interface, so the orchestrator and network layers are unchanged.

Covers the full OciRuntime surface over the containerd gRPC API alone (no
ctr/nerdctl), verified against live containerd v2.2.1: the connection, container/task
lifecycle (create via a hand-built OCI spec + snapshot, start/kill/remove), introspection,
image ops (exists/list/remove/entrypoint over the Images+Content services), and pull/push
over the Transfer service (an OCIRegistry <-> ImageStore transfer that also unpacks into
the snapshotter).
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
import gzip
import hashlib
import io
import json
import logging
import signal
import tarfile
import tempfile
from collections.abc import AsyncIterator, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast, override
from uuid import uuid4

import grpc
from google.protobuf import any_pb2, field_mask_pb2

from ai.backend.agent.containerd._grpcapi.api.events import task_pb2 as task_events_pb2
from ai.backend.agent.containerd._grpcapi.api.services.containers.v1 import (
    containers_pb2,
    containers_pb2_grpc,
)
from ai.backend.agent.containerd._grpcapi.api.services.content.v1 import (
    content_pb2,
    content_pb2_grpc,
)
from ai.backend.agent.containerd._grpcapi.api.services.diff.v1 import diff_pb2, diff_pb2_grpc
from ai.backend.agent.containerd._grpcapi.api.services.events.v1 import (
    events_pb2,
    events_pb2_grpc,
)
from ai.backend.agent.containerd._grpcapi.api.services.images.v1 import images_pb2, images_pb2_grpc
from ai.backend.agent.containerd._grpcapi.api.services.snapshots.v1 import (
    snapshots_pb2,
    snapshots_pb2_grpc,
)
from ai.backend.agent.containerd._grpcapi.api.services.tasks.v1 import tasks_pb2, tasks_pb2_grpc
from ai.backend.agent.containerd._grpcapi.api.services.transfer.v1 import (
    transfer_pb2,
    transfer_pb2_grpc,
)
from ai.backend.agent.containerd._grpcapi.api.types import descriptor_pb2, mount_pb2, platform_pb2
from ai.backend.agent.containerd._grpcapi.api.types.transfer import imagestore_pb2, registry_pb2
from ai.backend.agent.containerd.logs import logger_uri, unlink_log_files
from ai.backend.agent.containerd.runtime.interface import (
    ContainerInfo,
    ExecResult,
    ImageInfo,
    OciRuntime,
    TaskEvent,
    TaskHandle,
)
from ai.backend.agent.containerd.runtime.spec import build_oci_runtime_spec
from ai.backend.agent.errors.kernel import ContainerExecTimeout
from ai.backend.common.arch import CURRENT_ARCH
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_ADDRESS = "unix:///run/containerd/containerd.sock"
# Host dir where each task's captured stdout+stderr is written (read back by get_logs).
CONTAINER_LOG_ROOT = Path("/var/lib/backend.ai/containerd-logs")


def container_log_path(container_id: str) -> Path:
    return CONTAINER_LOG_ROOT / f"{container_id}.log"


# containerd multiplexes all objects by namespace; every RPC must carry it as metadata.
_NAMESPACE_HEADER = "containerd-namespace"
_RUNC_RUNTIME = "io.containerd.runc.v2"
_SNAPSHOTTER = "overlayfs"
_SPEC_TYPE_URL = "types.containerd.io/opencontainers/runtime-spec/1/Spec"
_PROCESS_TYPE_URL = "types.containerd.io/opencontainers/runtime-spec/1/Process"
_LAYER_MEDIA_TYPE = "application/vnd.oci.image.layer.v1.tar"  # uncompressed -> digest == diff_id
_CONFIG_MEDIA_TYPE = "application/vnd.oci.image.config.v1+json"
_MANIFEST_MEDIA_TYPE = "application/vnd.oci.image.manifest.v1+json"
_INDEX_MEDIA_TYPES = frozenset({
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
})
# A commit produces an OCI manifest even when the base image is a Docker one (as most registry
# images still are), keeping the base's layer descriptors exactly as they are — a mix the registries
# accept and containerd's own tooling (nerdctl commit) produces too. It is not a free choice: the
# differ refuses to write a Docker-media-type layer at all ("unsupported diff media type ...
# tar.gzip: not implemented", verified against containerd 2.2.1), so the new layer must be OCI, and
# an OCI layer under a Docker manifest is the combination nothing accepts.
_OCI_LAYER_GZIP_MEDIA_TYPE = "application/vnd.oci.image.layer.v1.tar+gzip"

# containerd's garbage collector reaches content ONLY through these labels. A manifest that does not
# name its config and layers is a manifest whose config and layers are unreferenced — the next GC
# pass deletes them and leaves the image an empty shell. containerd itself writes them on every pull
# (`ctr content ls` shows them on any pulled manifest); a blob we write ourselves is no different.
_GC_ROOT_LABEL = "containerd.io/gc.root"
_GC_REF_CONFIG_LABEL = "containerd.io/gc.ref.content.config"
_GC_REF_LAYER_LABEL = "containerd.io/gc.ref.content.l.{index}"
# The differ records the layer's *uncompressed* digest here — the diff_id the image config needs,
# which for a compressed layer is not the blob's own digest.
_UNCOMPRESSED_LABEL = "containerd.io/uncompressed"
# GOARCH names for platform matching in a multi-arch image index.
_GOARCH = {"aarch64": "arm64", "x86_64": "amd64"}

# containerd task status enum (api/types/task/task.proto) -> our string status.
_TASK_STATUS = {0: "unknown", 1: "created", 2: "running", 3: "stopped", 4: "paused", 5: "pausing"}

# Docker sets StopSignal=SIGINT for kernels; the kernel runner traps it to shut down cleanly.
_STOP_SIGNAL = signal.SIGINT
_KILL_SIGNAL = signal.SIGKILL


# Default deadline for the lifecycle RPCs that a destroy/clean handler waits on. Nothing in this
# client passed a timeout, so a wedged daemon (an overlayfs/snapshotter stall is the usual cause)
# blocked those handlers forever — remove_container's own 10s poll does not help, since it is the
# RPCs *inside* it that hang. Generous, because these are local-socket calls to a busy daemon, not
# network round trips; it is a backstop against an indefinite hang, not a latency budget. Streaming
# and legitimately long-running calls (content Read/Write, event Subscribe, transfer pull/push, exec
# Wait) are left unbounded.
_LIFECYCLE_CALL_TIMEOUT = 120.0


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


class ContainerdGrpcRuntime(OciRuntime):
    _address: str
    _namespace: str
    _channel: grpc.aio.Channel | None
    _containers: containers_pb2_grpc.ContainersStub | None
    _tasks: tasks_pb2_grpc.TasksStub | None
    _images: images_pb2_grpc.ImagesStub | None
    _content: content_pb2_grpc.ContentStub | None
    _snapshots: snapshots_pb2_grpc.SnapshotsStub | None
    _transfer: transfer_pb2_grpc.TransferStub | None
    _diff: diff_pb2_grpc.DiffStub | None
    _events: events_pb2_grpc.EventsStub | None
    _rootfs: dict[str, list[mount_pb2.Mount]]
    # containerd's `certs.d` directory. The transfer service reads a registry's hosts.toml only
    # when the CLIENT names this directory, so an agent that leaves it unset cannot reach a private
    # CA / self-signed / plain-HTTP registry however the host is configured. See registry_hosts_dir
    # in the agent config.
    _registry_hosts_dir: str | None
    # (logger launcher, log root, total byte budget) — set once the agent has written the launcher.
    # None means no `binary://` logging: the shim appends to a plain file that nobody rotates.
    _log_config: tuple[Path, Path, int] | None

    def __init__(
        self,
        *,
        address: str = DEFAULT_ADDRESS,
        namespace: str = "backend-ai",
        registry_hosts_dir: str | None = None,
    ) -> None:
        self._address = address
        self._namespace = namespace
        self._registry_hosts_dir = registry_hosts_dir
        self._channel = None
        self._containers = None
        self._tasks = None
        self._images = None
        self._content = None
        self._snapshots = None
        self._transfer = None
        self._diff = None
        self._events = None
        self._rootfs: dict[str, list[mount_pb2.Mount]] = {}
        self._log_config = None

    @override
    def configure_logging(self, launcher: Path, log_root: Path, max_total_bytes: int) -> None:
        """Log new containers through our own writer (see containerd/log_writer.py)."""
        self._log_config = (launcher, log_root, max_total_bytes)

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
        self._diff = diff_pb2_grpc.DiffStub(self._channel)
        self._events = events_pb2_grpc.EventsStub(self._channel)

    @override
    async def close(self) -> None:
        if self._channel is not None:
            await self._channel.close()
            self._channel = None
            self._containers = self._tasks = None
            self._images = self._content = self._snapshots = None
            self._transfer = self._diff = self._events = None

    @property
    def _md(self) -> list[tuple[str, str]]:
        return [(_NAMESPACE_HEADER, self._namespace)]

    def _containers_stub(self) -> containers_pb2_grpc.ContainersStub:
        if self._containers is None:
            raise RuntimeError("ContainerdGrpcRuntime is not open (call open() first)")
        return self._containers

    def _tasks_stub(self) -> tasks_pb2_grpc.TasksStub:
        if self._tasks is None:
            raise RuntimeError("ContainerdGrpcRuntime is not open (call open() first)")
        return self._tasks

    def _images_stub(self) -> images_pb2_grpc.ImagesStub:
        if self._images is None:
            raise RuntimeError("ContainerdGrpcRuntime is not open (call open() first)")
        return self._images

    def _content_stub(self) -> content_pb2_grpc.ContentStub:
        if self._content is None:
            raise RuntimeError("ContainerdGrpcRuntime is not open (call open() first)")
        return self._content

    def _snapshots_stub(self) -> snapshots_pb2_grpc.SnapshotsStub:
        if self._snapshots is None:
            raise RuntimeError("ContainerdGrpcRuntime is not open (call open() first)")
        return self._snapshots

    def _transfer_stub(self) -> transfer_pb2_grpc.TransferStub:
        if self._transfer is None:
            raise RuntimeError("ContainerdGrpcRuntime is not open (call open() first)")
        return self._transfer

    def _diff_stub(self) -> diff_pb2_grpc.DiffStub:
        if self._diff is None:
            raise RuntimeError("ContainerdGrpcRuntime is not open (call open() first)")
        return self._diff

    def _events_stub(self) -> events_pb2_grpc.EventsStub:
        if self._events is None:
            raise RuntimeError("ContainerdGrpcRuntime is not open (call open() first)")
        return self._events

    @override
    async def subscribe_task_events(self) -> AsyncIterator[TaskEvent]:
        # Subscribe to the runtime's whole event stream and surface the task lifecycle ones.
        # The event's container_id IS our container id (== kernel id), so no name lookup.
        async for env in self._events_stub().Subscribe(
            events_pb2.SubscribeRequest(), metadata=self._md
        ):
            topic = env.topic
            if topic == "/tasks/exit":
                ev = task_events_pb2.TaskExit()
                ev.ParseFromString(env.event.value)
                # /tasks/exit also fires when an `exec`-ed process (health probe, in-container
                # tool, etc.) exits; its ``id`` is the exec id. Only the main task's exit
                # (id == container_id) means the kernel itself died — ignore exec exits, else a
                # transient `exec` would tear the kernel down.
                if ev.id == ev.container_id:
                    yield TaskEvent("exit", ev.container_id, ev.exit_status)
            elif topic == "/tasks/oom":
                ev_oom = task_events_pb2.TaskOOM()
                ev_oom.ParseFromString(env.event.value)
                yield TaskEvent("oom", ev_oom.container_id)
            elif topic == "/tasks/start":
                ev_start = task_events_pb2.TaskStart()
                ev_start.ParseFromString(env.event.value)
                yield TaskEvent("start", ev_start.container_id)

    async def _write_content(
        self, data: bytes, media_type: str, *, labels: Mapping[str, str] | None = None
    ) -> dict[str, Any]:
        """Write a blob to the content store and return its OCI descriptor dict."""
        digest = "sha256:" + hashlib.sha256(data).hexdigest()
        ref = f"commit-{digest[7:19]}"

        async def _requests() -> Any:
            yield content_pb2.WriteContentRequest(
                action=content_pb2.WriteAction.WRITE,
                ref=ref,
                total=len(data),
                expected=digest,
                offset=0,
                data=data,
            )
            yield content_pb2.WriteContentRequest(
                action=content_pb2.WriteAction.COMMIT,
                ref=ref,
                total=len(data),
                expected=digest,
                offset=len(data),
                labels=dict(labels or {}),
            )

        async for _resp in self._content_stub().Write(_requests(), metadata=self._md):
            pass
        return {"mediaType": media_type, "digest": digest, "size": len(data)}

    async def _uncompressed_digest(self, digest: str) -> str:
        """The diff_id of a compressed layer blob: the digest of its *uncompressed* tar, which the
        differ writes as a label on the blob it produced."""
        info = (
            await self._content_stub().Info(
                content_pb2.InfoRequest(digest=digest), metadata=self._md
            )
        ).info
        uncompressed = info.labels.get(_UNCOMPRESSED_LABEL)
        if not uncompressed:
            raise RuntimeError(
                f"containerd did not record an uncompressed digest for the committed layer {digest};"
                " the image it produced would not unpack"
            )
        return str(uncompressed)

    async def _drop_gc_root(self, digest: str) -> None:
        """Release the temporary GC root held on a blob while the image that will reference it did
        not exist yet. The mask names the one label, so the differ's ``uncompressed`` label — which
        is how containerd maps a diff_id back to this blob when it unpacks the image — survives."""
        await self._content_stub().Update(
            content_pb2.UpdateRequest(
                info=content_pb2.Info(digest=digest, labels={_GC_ROOT_LABEL: ""}),
                update_mask=field_mask_pb2.FieldMask(paths=[f"labels.{_GC_ROOT_LABEL}"]),
            ),
            metadata=self._md,
        )

    async def _delete_content(self, digest: str) -> None:
        """Delete a blob from the content store. Used to clean up the layer/config a failed commit
        wrote — once its GC root is dropped it would be collectable anyway, but leaving a several-
        gigabyte layer to sit until the next GC pass is worth avoiding."""
        with contextlib.suppress(grpc.aio.AioRpcError):
            await self._content_stub().Delete(
                content_pb2.DeleteContentRequest(digest=digest), metadata=self._md
            )

    @contextlib.asynccontextmanager
    async def _paused(self, container_id: str) -> AsyncIterator[None]:
        """Freeze the container's processes for the duration of the diff, the way `docker commit`
        does by default: a rootfs read while it is being written yields a layer of half-written
        files, and the user is not told which.

        A container with no running task (already exited) needs no pausing, and a runtime that
        refuses to pause must not cost the user their commit — it costs them only the guarantee.
        """
        try:
            await self._tasks_stub().Pause(
                tasks_pb2.PauseTaskRequest(container_id=container_id), metadata=self._md
            )
        except grpc.aio.AioRpcError as e:
            log.warning(
                "could not pause {} for the commit ({}); its rootfs is being read while it runs",
                container_id,
                e.code().name,
            )
            yield
            return
        try:
            yield
        finally:
            with contextlib.suppress(grpc.aio.AioRpcError):
                await self._tasks_stub().Resume(
                    tasks_pb2.ResumeTaskRequest(container_id=container_id), metadata=self._md
                )

    @override
    async def commit_container(
        self,
        container_id: str,
        *,
        base_image_ref: str,
        target_ref: str,
        labels: Mapping[str, str] | None = None,
    ) -> None:
        base_manifest = await self._resolve_manifest(base_image_ref)
        base_config = json.loads(await self._read_content(base_manifest["config"]["digest"]))
        base_layers = list(base_manifest.get("layers") or [])
        base_diff_ids = list(base_config["rootfs"]["diff_ids"])
        now = datetime.now(UTC).isoformat()

        # 1. Diff the container's rootfs against the base image's, so the layer holds what the user
        #    CHANGED and the image shares every layer below it with the base. A diff against nothing
        #    (left=[]) would flatten the whole rootfs into one layer that no other image shares:
        #    gigabytes duplicated in the content store, a push that uploads the entire OS, and a
        #    pull that can reuse none of what the puller already has.
        active = (
            await self._snapshots_stub().Mounts(
                snapshots_pb2.MountsRequest(snapshotter=_SNAPSHOTTER, key=container_id),
                metadata=self._md,
            )
        ).mounts
        view_key = f"backendai-commit-{container_id}"
        base_view = (
            await self._snapshots_stub().View(
                snapshots_pb2.ViewSnapshotRequest(
                    snapshotter=_SNAPSHOTTER,
                    key=view_key,
                    parent=_chain_id(base_diff_ids),
                ),
                metadata=self._md,
            )
        ).mounts
        try:
            async with self._paused(container_id):
                layer = (
                    await self._diff_stub().Diff(
                        diff_pb2.DiffRequest(
                            left=list(base_view),
                            right=list(active),
                            media_type=_OCI_LAYER_GZIP_MEDIA_TYPE,
                            ref=f"commit-{container_id}",
                            # The image that will reference this blob does not exist yet, so until
                            # it does the blob is unreferenced — and containerd's GC deletes what
                            # nothing references. Hold it as a root, and let go below.
                            labels={_GC_ROOT_LABEL: now},
                        ),
                        metadata=self._md,
                    )
                ).diff
        finally:
            with contextlib.suppress(grpc.aio.AioRpcError):
                await self._snapshots_stub().Remove(
                    snapshots_pb2.RemoveSnapshotRequest(snapshotter=_SNAPSHOTTER, key=view_key),
                    metadata=self._md,
                )

        # From here the diff layer is a rooted blob in the content store. Every step that follows
        # can fail — reading the diff_id back, writing the config/manifest, Images.Create — and a
        # GC root is never collected, even after the image is deleted, so a failure that left these
        # roots set would pin the layer (gigabytes) and the config forever. Roll them back on any
        # exception; on success the image roots them and the temporary roots are dropped at the end.
        rooted: list[str] = [layer.digest]
        try:
            await self._finish_commit(
                container_id, target_ref, now, labels, base_config, base_diff_ids, base_layers,
                layer, rooted,
            )  # fmt: skip
        except BaseException:
            for digest in rooted:
                with contextlib.suppress(grpc.aio.AioRpcError):
                    await self._drop_gc_root(digest)
                await self._delete_content(digest)
            raise

    async def _finish_commit(
        self,
        container_id: str,
        target_ref: str,
        now: str,
        labels: Mapping[str, str] | None,
        base_config: dict[str, Any],
        base_diff_ids: list[str],
        base_layers: list[dict[str, Any]],
        layer: Any,
        rooted: list[str],
    ) -> None:
        # 2. New config: the base's, plus this layer's diff_id and a history entry.
        #
        #    The diff_id is the layer's UNCOMPRESSED digest, which for a gzipped layer is NOT the
        #    blob's digest. The differ records it as a *content label*, and leaves the descriptor it
        #    returns with empty annotations — so it has to be read back from the content store.
        #    Taking the blob's own digest instead produces an image containerd accepts, stores, and
        #    then refuses to unpack ("wrong diff id calculated on extraction"): complete on disk,
        #    unusable in fact.
        diff_id = await self._uncompressed_digest(layer.digest)
        config = json.loads(json.dumps(base_config))  # deep copy: we edit nested members
        config["rootfs"] = {"type": "layers", "diff_ids": [*base_diff_ids, diff_id]}
        cfg = dict(config.get("config") or {})
        cfg["Labels"] = {**(cfg.get("Labels") or {}), **(labels or {})}
        config["config"] = cfg
        config["created"] = now
        config["history"] = [
            *(config.get("history") or []),
            {"created": now, "created_by": f"backend.ai commit {container_id}"},
        ]
        config_desc = await self._write_content(
            json.dumps(config).encode(), _CONFIG_MEDIA_TYPE, labels={_GC_ROOT_LABEL: now}
        )
        rooted.append(config_desc["digest"])

        # 3. New manifest: the base's layers plus ours. Its GC labels are what keep the config and
        #    every layer reachable once the image is the only thing rooting them.
        layers: list[dict[str, Any]] = [
            *base_layers,
            {
                "mediaType": _OCI_LAYER_GZIP_MEDIA_TYPE,
                "digest": layer.digest,
                "size": layer.size,
            },
        ]
        manifest = {
            "schemaVersion": 2,
            "mediaType": _MANIFEST_MEDIA_TYPE,
            "config": config_desc,
            "layers": layers,
        }
        gc_refs = {_GC_REF_CONFIG_LABEL: config_desc["digest"], _GC_ROOT_LABEL: now}
        for index, desc in enumerate(layers):
            gc_refs[_GC_REF_LAYER_LABEL.format(index=index)] = str(desc["digest"])
        manifest_desc = await self._write_content(
            json.dumps(manifest).encode(), _MANIFEST_MEDIA_TYPE, labels=gc_refs
        )
        rooted.append(manifest_desc["digest"])

        # 4. Register the image pointing at the manifest.
        target = descriptor_pb2.Descriptor(
            media_type=_MANIFEST_MEDIA_TYPE,
            digest=manifest_desc["digest"],
            size=manifest_desc["size"],
        )
        image = images_pb2.Image(name=target_ref, target=target)
        try:
            await self._images_stub().Create(
                images_pb2.CreateImageRequest(image=image), metadata=self._md
            )
        except grpc.aio.AioRpcError as e:
            if e.code() is not grpc.StatusCode.ALREADY_EXISTS:
                raise
            await self._images_stub().Update(
                images_pb2.UpdateImageRequest(image=image), metadata=self._md
            )

        # 5. The image now roots the manifest, and the manifest references the config and the layer,
        #    so the temporary roots can go. Leaving them would pin every commit's blobs forever —
        #    a GC root is never collected, even after the image is deleted.
        for digest in (manifest_desc["digest"], config_desc["digest"], layer.digest):
            with contextlib.suppress(grpc.aio.AioRpcError):
                await self._drop_gc_root(digest)

    # --- image content helpers (read the manifest chain to resolve the rootfs) ---

    async def _read_content_chunks(self, digest: str) -> AsyncIterator[bytes]:
        """Stream a blob from the content store, one gRPC chunk at a time."""
        async for resp in self._content_stub().Read(
            content_pb2.ReadContentRequest(digest=digest), metadata=self._md
        ):
            yield resp.data

    async def _read_content(self, digest: str) -> bytes:
        buf = bytearray()
        async for chunk in self._read_content_chunks(digest):
            buf.extend(chunk)
        return bytes(buf)

    async def _spool_content(self, digest: str, dest: Path) -> int:
        """Stream a blob from the content store to a file, a chunk at a time, and return its size.

        `_read_content` holds the whole blob in memory; a rootfs layer is gigabytes, so export used
        to need the entire image resident in the agent's RSS at once (OOM-killing it on a large
        image). Spooling each blob to disk keeps the footprint to one gRPC chunk."""
        size = 0
        f = await asyncio.to_thread(dest.open, "wb")
        try:
            async for chunk in self._read_content_chunks(digest):
                await asyncio.to_thread(f.write, chunk)
                size += len(chunk)
        finally:
            await asyncio.to_thread(f.close)
        return size

    @override
    async def export_image(self, image_ref: str, dest_path: Path) -> None:
        """Write a gzipped OCI-layout archive of ``image_ref`` to ``dest_path``.

        This is the containerd counterpart of Docker's ``GET /images/<id>/get``, which is what the
        Docker backend streams into the session-export file. containerd's own export lives behind
        the Transfer service's streaming API, which needs the `streaming` gRPC service we do not
        generate stubs for — so we assemble the archive from the content store instead, which we
        can already read. The result is a standard OCI image layout (oci-layout + index.json +
        blobs/), the interchange format `docker load` and `ctr images import` both accept.
        """
        manifest = await self._resolve_manifest(image_ref)
        manifest_bytes = json.dumps(manifest, separators=(",", ":")).encode()
        manifest_digest = "sha256:" + hashlib.sha256(manifest_bytes).hexdigest()

        index = {
            "schemaVersion": 2,
            "mediaType": "application/vnd.oci.image.index.v1+json",
            "manifests": [
                {
                    "mediaType": manifest.get("mediaType", _MANIFEST_MEDIA_TYPE),
                    "digest": manifest_digest,
                    "size": len(manifest_bytes),
                    "annotations": {"org.opencontainers.image.ref.name": image_ref},
                }
            ],
        }
        # The layer blobs are spooled to a temp dir first, one chunk at a time, so the whole
        # (multi-gigabyte) image never sits in the agent's memory. Only the small metadata blobs
        # (manifest, config, oci-layout, index.json) are held as bytes. The tar streams from disk.
        await asyncio.to_thread(dest_path.parent.mkdir, parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=dest_path.parent) as spool_dir:
            spool = Path(spool_dir)
            inline: list[tuple[str, bytes]] = [
                (manifest_digest, manifest_bytes),
                (manifest["config"]["digest"], await self._read_content(manifest["config"]["digest"])),
            ]  # fmt: skip
            layer_files: list[tuple[str, Path, int]] = []
            for i, desc in enumerate(manifest.get("layers", [])):
                blob = spool / f"layer-{i}"
                size = await self._spool_content(desc["digest"], blob)
                layer_files.append((desc["digest"], blob, size))

            def _write() -> None:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                with gzip.open(dest_path, "wb") as gz, tarfile.open(fileobj=gz, mode="w|") as tar:

                    def add_bytes(name: str, payload: bytes) -> None:
                        info = tarfile.TarInfo(name)
                        info.size = len(payload)
                        tar.addfile(info, io.BytesIO(payload))

                    def blob_name(digest: str) -> str:
                        algo, _, hexdigest = digest.partition(":")
                        return f"blobs/{algo}/{hexdigest}"

                    add_bytes("oci-layout", json.dumps({"imageLayoutVersion": "1.0.0"}).encode())
                    add_bytes("index.json", json.dumps(index).encode())
                    for digest, payload in inline:
                        add_bytes(blob_name(digest), payload)
                    for digest, path, size in layer_files:
                        info = tarfile.TarInfo(blob_name(digest))
                        info.size = size
                        with path.open("rb") as bf:
                            tar.addfile(info, bf)  # streamed, not read into memory

            await asyncio.to_thread(_write)

    async def _resolve_manifest(self, image_ref: str) -> dict[str, Any]:
        """The image's manifest for THIS platform, following a multi-arch index when present."""
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
            return cast(dict[str, Any], json.loads(await self._read_content(manifest_digest)))
        return cast(dict[str, Any], json.loads(await self._read_content(target.digest)))

    @override
    async def image_config_digest(self, image_ref: str) -> str | None:
        """The digest of the image's *config* blob — the identity Docker reports as ``Id``.

        This, not the manifest digest, is what the manager stores and hands back as ``image_id``.
        Comparing the manifest digest against it never matches, so AutoPullBehavior.DIGEST would
        re-pull the image on every single kernel creation.
        """
        try:
            manifest = await self._resolve_manifest(image_ref)
        except grpc.aio.AioRpcError as e:
            if e.code() is grpc.StatusCode.NOT_FOUND:
                return None
            raise
        return str(manifest["config"]["digest"])

    async def _resolve_image(self, image_ref: str) -> tuple[str, dict[str, Any]]:
        """Resolve an image to (rootfs chain_id, image config) for the current platform."""
        manifest = await self._resolve_manifest(image_ref)
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
        # Every mount source must be an absolute host path — runc binds it directly. (There
        # are no named volumes: krunner is extracted to a host dir, cf. containerd/krunner.py.)
        for mount in oci_spec.get("mounts", []):
            if not str(mount["source"]).startswith("/"):
                raise ValueError(f"mount source must be an absolute path, got {mount['source']!r}")
        # Active snapshot for the writable rootfs, layered on the image's chain.
        prepared = await self._snapshots_stub().Prepare(
            snapshots_pb2.PrepareSnapshotRequest(
                snapshotter=_SNAPSHOTTER, key=container_id, parent=chain_id
            ),
            metadata=self._md,
        )
        self._rootfs[container_id] = list(prepared.mounts)
        # The snapshot is now the container's, keyed on its id. If anything below fails — a bad
        # spec, Containers.Create — that snapshot and the _rootfs entry survive, and a retry of the
        # same kernel id then fails at Prepare with ALREADY_EXISTS forever. Undo the snapshot on any
        # failure so the id is reusable.
        try:
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
                # The caller pins both (Docker sets WorkingDir=/home/work and
                # Hostname=cluster_hostname); fall back to the image / a container-id prefix only
                # when it did not.
                cwd=oci_spec.get("cwd") or cfg.get("WorkingDir") or "/",
                hostname=oci_spec.get("hostname") or container_id[:12],
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
        except BaseException:
            self._rootfs.pop(container_id, None)
            with contextlib.suppress(grpc.aio.AioRpcError):
                await self._snapshots_stub().Remove(
                    snapshots_pb2.RemoveSnapshotRequest(snapshotter=_SNAPSHOTTER, key=container_id),
                    metadata=self._md,
                )
            raise

    @override
    async def create_task(self, container_id: str, *, use_logger: bool = True) -> TaskHandle:
        # Tasks.Create leaves the task in the 'created' state: the init process (and its netns)
        # exist and its PID is returned, but the user command is not exec'd until start_task.
        # The network layer attaches CNI into /proc/<pid>/ns/net in this window.
        #
        # `log_uri` is a `binary://` URI: containerd starts that program and pipes the container's
        # stdout/stderr into it, so we own the write end and can rotate the log the way dockerd's
        # driver does. Without one, the shim appends to a plain file forever and nobody rotates it —
        # which is the fallback used for short-lived internal containers (the image-distro probe),
        # where a few lines of output are read once and the container is thrown away.
        if use_logger and self._log_config is not None:
            launcher, log_root, max_bytes = self._log_config
            stdio = logger_uri(launcher, log_root, max_bytes)
        else:
            log_path = container_log_path(container_id)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.touch(exist_ok=True)
            stdio = str(log_path)
        resp = await self._tasks_stub().Create(
            tasks_pb2.CreateTaskRequest(
                container_id=container_id,
                rootfs=self._rootfs.get(container_id, []),
                stdout=stdio,
                stderr=stdio,
            ),
            metadata=self._md,
        )
        return TaskHandle(container_id=container_id, pid=resp.pid)

    @override
    async def start_task(self, container_id: str) -> None:
        # Tasks.Start execs the user command in the already-created task, whose network the
        # caller has attached in the meantime.
        await self._tasks_stub().Start(
            tasks_pb2.StartRequest(container_id=container_id), metadata=self._md
        )

    @override
    async def kill_container(
        self, container_id: str, *, signal: int, all_processes: bool = True
    ) -> None:
        """Signal the container. ``all_processes`` broadcasts to every process in it; clear it to
        signal only the init process (PID 1), which is what a graceful stop wants."""
        try:
            await self._tasks_stub().Kill(
                tasks_pb2.KillRequest(container_id=container_id, signal=signal, all=all_processes),
                metadata=self._md,
                timeout=_LIFECYCLE_CALL_TIMEOUT,
            )
        except grpc.aio.AioRpcError as e:
            if e.code() is not grpc.StatusCode.NOT_FOUND:
                raise

    @override
    async def stop_container(self, container_id: str, *, grace_period: float) -> None:
        # Graceful stop, then SIGKILL — matching Docker's container.stop(). kill_container
        # swallows NOT_FOUND, so a task that is already gone is a no-op. The poll interval
        # mirrors remove_container's (~10 ticks/s).
        #
        # Two details of Docker's contract, both of which we used to get wrong:
        #  - the signal is SIGINT (Docker's StopSignal for kernels), not SIGTERM. The kernel
        #    runner happens to trap both, so this is parity rather than a fix in itself.
        #  - it goes to the INIT PROCESS ONLY. Broadcasting it to every process in the container
        #    (all=True) tears the user's workload down underneath the runner instead of letting
        #    the runner shut its children down in order — the whole point of a grace period.
        await self.kill_container(container_id, signal=_STOP_SIGNAL, all_processes=False)
        deadline_ticks = max(1, int(grace_period / 0.1))
        for _ in range(deadline_ticks):
            status = await self.container_status(container_id)
            if status in (None, "stopped", "created", "unknown"):
                return
            await asyncio.sleep(0.1)
        await self.kill_container(container_id, signal=_KILL_SIGNAL)

    @override
    async def remove_container(self, container_id: str) -> None:
        # containerd rejects deleting a still-running task ("cannot delete a running process"),
        # so SIGKILL the task and wait for it to actually exit before deletion. (Also required
        # for HOSTFILE scratch: the loop mount can only be unmounted once the container's
        # bind-mount of it is gone.)
        await self.kill_container(container_id, signal=_KILL_SIGNAL)
        exited = False
        for _ in range(100):  # up to ~10s
            status = await self.container_status(container_id)
            if status in (None, "stopped", "created", "unknown"):
                exited = True
                break
            await asyncio.sleep(0.1)
        # task -> container -> snapshot. Each is a no-op if already gone (NOT_FOUND). But the task
        # delete can also fail FAILED_PRECONDITION when the task refused to die (a process wedged in
        # D-state on a hung NFS vfolder outlives even SIGKILL): treat that like already-gone and go
        # on, or the container record, its snapshot, the _rootfs entry and the logs would all be
        # left behind — a leak on every stuck kernel — and the caller would see the whole clean
        # fail. (containerd's DeleteTaskRequest here carries no force flag, so the shim's own task
        # record may linger until the process finally dies; the container-level records still go.)
        try:
            await self._tasks_stub().Delete(
                tasks_pb2.DeleteTaskRequest(container_id=container_id),
                metadata=self._md,
                timeout=_LIFECYCLE_CALL_TIMEOUT,
            )
        except grpc.aio.AioRpcError as e:
            if e.code() not in (
                grpc.StatusCode.NOT_FOUND,
                grpc.StatusCode.FAILED_PRECONDITION,
            ):
                raise
            if not exited:
                log.warning(
                    "remove_container(c:{}): task did not exit; deleting its records anyway",
                    container_id,
                )
        for coro in (
            self._containers_stub().Delete(
                containers_pb2.DeleteContainerRequest(id=container_id),
                metadata=self._md,
                timeout=_LIFECYCLE_CALL_TIMEOUT,
            ),
            self._snapshots_stub().Remove(
                snapshots_pb2.RemoveSnapshotRequest(snapshotter=_SNAPSHOTTER, key=container_id),
                metadata=self._md,
                timeout=_LIFECYCLE_CALL_TIMEOUT,
            ),
        ):
            try:
                await coro
            except grpc.aio.AioRpcError as e:
                if e.code() is not grpc.StatusCode.NOT_FOUND:
                    raise
        self._rootfs.pop(container_id, None)
        # The rotated files are as much this kernel's log as the active one.
        unlink_log_files(container_log_path(container_id))

    # --- container/task introspection (Phase 1) ---

    @override
    async def list_containers(self) -> Sequence[str]:
        resp: containers_pb2.ListContainersResponse = await self._containers_stub().List(
            containers_pb2.ListContainersRequest(), metadata=self._md
        )
        return [c.id for c in resp.containers]

    @override
    async def list_container_infos(self) -> Sequence[ContainerInfo]:
        resp: containers_pb2.ListContainersResponse = await self._containers_stub().List(
            containers_pb2.ListContainersRequest(), metadata=self._md
        )
        infos: list[ContainerInfo] = []
        for c in resp.containers:
            infos.append(
                ContainerInfo(
                    id=c.id,
                    image=c.image,
                    labels=dict(c.labels),
                    # No task => the container exists but has never run: it is mid-creation
                    # (Containers.Create has returned, Tasks.Create has not). Report "created",
                    # not "stopped" — the latter reads as dead and gets the kernel cleaned up
                    # underneath us. A task that has exited reports "stopped" on its own, and
                    # remove_container() deletes task and container together, so a task-less
                    # container is never a leftover of a completed run.
                    status=await self.container_status(c.id) or "created",
                )
            )
        return infos

    @override
    async def container_status(self, container_id: str) -> str | None:
        try:
            resp: tasks_pb2.GetResponse = await self._tasks_stub().Get(
                tasks_pb2.GetRequest(container_id=container_id),
                metadata=self._md,
                timeout=_LIFECYCLE_CALL_TIMEOUT,
            )
        except grpc.aio.AioRpcError as e:
            if e.code() is grpc.StatusCode.NOT_FOUND:
                return None
            raise
        return _TASK_STATUS.get(resp.process.status, "unknown")

    @override
    async def exec_in_container(
        self,
        container_id: str,
        args: Sequence[str],
        *,
        uid: int | None = None,
        gid: int | None = None,
        cwd: str | None = None,
        timeout_sec: float = 30.0,
    ) -> ExecResult:
        # Reuse the container's own process spec (env, capabilities, rlimits) and override only
        # what this call needs; building a Process from scratch would drop the environment the
        # kernel runner depends on (PATH to /opt/backend.ai/bin, etc).
        base = await self._container_process_spec(container_id)
        process = {
            **base,
            "args": list(args),
            "terminal": False,
        }
        if uid is not None or gid is not None:
            user = dict(base.get("user") or {})
            if uid is not None:
                user["uid"] = uid
            if gid is not None:
                user["gid"] = gid
            process["user"] = user
        if cwd is not None:
            process["cwd"] = cwd

        exec_id = f"bai-exec-{uuid4().hex}"
        # The shim writes the streams to plain host paths (same as create_task). Keep them
        # separate and read them back as raw bytes: download_file carries a tar through stdout.
        out_path = CONTAINER_LOG_ROOT / f"{exec_id}.out"
        err_path = CONTAINER_LOG_ROOT / f"{exec_id}.err"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.touch()
        err_path.touch()
        try:
            await self._tasks_stub().Exec(
                tasks_pb2.ExecProcessRequest(
                    container_id=container_id,
                    exec_id=exec_id,
                    terminal=False,
                    stdout=str(out_path),
                    stderr=str(err_path),
                    spec=any_pb2.Any(
                        type_url=_PROCESS_TYPE_URL, value=json.dumps(process).encode()
                    ),
                ),
                metadata=self._md,
            )
            await self._tasks_stub().Start(
                tasks_pb2.StartRequest(container_id=container_id, exec_id=exec_id),
                metadata=self._md,
            )
            try:
                resp: tasks_pb2.WaitResponse = await asyncio.wait_for(
                    self._tasks_stub().Wait(
                        tasks_pb2.WaitRequest(container_id=container_id, exec_id=exec_id),
                        metadata=self._md,
                    ),
                    timeout_sec,
                )
                return ExecResult(
                    exit_code=resp.exit_status,
                    stdout=out_path.read_bytes(),
                    stderr=err_path.read_bytes(),
                )
            except TimeoutError as e:
                # Do not leave the command running: it holds the exec process (and our stdio
                # paths) open for as long as it likes.
                with contextlib.suppress(grpc.aio.AioRpcError):
                    await self._tasks_stub().Kill(
                        tasks_pb2.KillRequest(container_id=container_id, exec_id=exec_id, signal=9),
                        metadata=self._md,
                    )
                raise ContainerExecTimeout(
                    f"exec in {container_id[:12]} timed out after {timeout_sec}s: {list(args)!r}"
                ) from e
        finally:
            with contextlib.suppress(grpc.aio.AioRpcError):
                await self._tasks_stub().DeleteProcess(
                    tasks_pb2.DeleteProcessRequest(container_id=container_id, exec_id=exec_id),
                    metadata=self._md,
                )
            out_path.unlink(missing_ok=True)
            err_path.unlink(missing_ok=True)

    async def _container_process_spec(self, container_id: str) -> dict[str, Any]:
        """The `process` block of the container's stored OCI runtime spec."""
        resp: containers_pb2.GetContainerResponse = await self._containers_stub().Get(
            containers_pb2.GetContainerRequest(id=container_id), metadata=self._md
        )
        spec = json.loads(resp.container.spec.value)
        return cast(dict[str, Any], spec.get("process") or {})

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
    async def image_digest(self, image_ref: str) -> str | None:
        try:
            resp = await self._images_stub().Get(
                images_pb2.GetImageRequest(name=image_ref), metadata=self._md
            )
        except grpc.aio.AioRpcError as e:
            if e.code() is grpc.StatusCode.NOT_FOUND:
                return None
            raise
        return str(resp.image.target.digest)

    @override
    async def list_images(self) -> Sequence[str]:
        resp = await self._images_stub().List(images_pb2.ListImagesRequest(), metadata=self._md)
        return [img.name for img in resp.images]

    @override
    async def list_image_infos(self) -> Sequence[ImageInfo]:
        resp = await self._images_stub().List(images_pb2.ListImagesRequest(), metadata=self._md)
        infos: list[ImageInfo] = []
        for img in resp.images:
            try:
                _chain, config = await self._resolve_image(img.name)
            except (grpc.aio.AioRpcError, KeyError, ValueError):
                continue  # unreadable/foreign image — skip, don't fail the whole scan
            cfg = config.get("config") or {}
            infos.append(
                ImageInfo(
                    name=img.name,
                    digest=img.target.digest,
                    architecture=str(config.get("architecture") or ""),
                    labels={str(k): str(v) for k, v in (cfg.get("Labels") or {}).items()},
                )
            )
        return infos

    @override
    async def remove_image(self, image_ref: str, *, sync: bool = False) -> None:
        try:
            await self._images_stub().Delete(
                images_pb2.DeleteImageRequest(name=image_ref, sync=sync), metadata=self._md
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

    def _oci_registry(self, image_ref: str, auth: Mapping[str, str] | None) -> Any:
        """An OCIRegistry ref: basic-auth header when credentials are given, plus the host config
        directory that describes registries which are not plain public HTTPS.

        Docker gets the latter for free — dockerd applies its own daemon.json/certs.d — but
        containerd's transfer service consults hosts.toml only when we name the directory. Leaving
        it unset means "every registry is public HTTPS with a well-known CA", which is why a
        self-signed or HTTP registry failed with `server gave HTTP response to HTTPS client` even
        on a host that had it correctly configured for ctr/nerdctl.
        """
        resolver = registry_pb2.RegistryResolver()
        if auth and (user := auth.get("username")) and (pw := auth.get("password")):
            token = base64.b64encode(f"{user}:{pw}".encode()).decode()
            resolver.headers["Authorization"] = f"Basic {token}"
        if self._registry_hosts_dir:
            resolver.host_dir = self._registry_hosts_dir
        return _containerd_any(registry_pb2.OCIRegistry(reference=image_ref, resolver=resolver))

    @override
    async def pull_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None:
        # Pull server-side via the Transfer service: an OCIRegistry source streamed into an
        # ImageStore destination (which also unpacks into the snapshotter). Pure containerd
        # API — no ctr/nerdctl.
        source = self._oci_registry(image_ref, auth)
        # Pull THIS node's platform only. An empty platforms list means "all platforms" to the
        # transfer service, so a multi-arch image (Backend.AI publishes amd64 + arm64) would fetch
        # and store every architecture's layers — roughly 2x pull time and disk on every agent.
        # Docker pulls the host platform; so do we. (The unpack platform is advisory: containerd
        # picks the unpack config from its own server-side list. It is passed for correctness, but
        # what actually bounds the fetch is ImageStore.platforms.)
        platform = platform_pb2.Platform(
            os="linux", architecture=_GOARCH.get(CURRENT_ARCH, CURRENT_ARCH)
        )
        destination = _containerd_any(
            imagestore_pb2.ImageStore(
                name=image_ref,
                platforms=[platform],
                unpacks=[
                    imagestore_pb2.UnpackConfiguration(snapshotter=_SNAPSHOTTER, platform=platform)
                ],
            )
        )
        await self._transfer_stub().Transfer(
            transfer_pb2.TransferRequest(source=source, destination=destination),
            metadata=self._md,
        )

    @override
    async def push_image(self, image_ref: str, *, auth: Mapping[str, str] | None = None) -> None:
        # Reverse of pull: an ImageStore source pushed to an OCIRegistry destination.
        source = _containerd_any(imagestore_pb2.ImageStore(name=image_ref))
        destination = self._oci_registry(image_ref, auth)
        await self._transfer_stub().Transfer(
            transfer_pb2.TransferRequest(source=source, destination=destination),
            metadata=self._md,
        )
