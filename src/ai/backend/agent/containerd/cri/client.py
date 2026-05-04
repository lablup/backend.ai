"""Async CRI gRPC client for the containerd backend.

This module wraps the auto-generated stubs in ``cri.generated`` with a
small high-level surface that the agent uses. Currently exposed:

- ``Version()`` — runtime health probe.
- PodSandbox lifecycle: ``RunPodSandbox`` / ``StopPodSandbox`` /
  ``RemovePodSandbox`` / ``PodSandboxStatus`` / ``ListPodSandbox``.
- Container lifecycle: ``CreateContainer`` / ``StartContainer`` /
  ``StopContainer`` / ``RemoveContainer`` / ``ListContainers`` /
  ``ContainerStatus``.
- Image management: ``PullImage`` / ``ImageStatus`` / ``ListImages`` /
  ``RemoveImage``.

Streaming RPCs (``Exec`` / ``Attach`` / ``ContainerStats``) and the
filesystem / runtime-config endpoints are not yet exposed; they land
when the agent layer needs them (code-runner integration, stats
collection).

Methods take and return raw proto objects rather than wrapping them in
domain dataclasses — the agent layer owns the translation between
kernel-domain concepts (``KernelCreationConfig``, scratch dirs, etc.)
and CRI proto, so this module stays a thin runtime-shaped surface.

Connection model
----------------
Containerd exposes its CRI socket as a Unix domain socket (default
``/run/containerd/containerd.sock``). gRPC's Python implementation
takes a target string of the form ``unix:///run/containerd/containerd.sock``
and the channel handles all framing — no extra adapter required.

The client deliberately avoids any synchronous ``grpc.insecure_channel``
calls; everything goes through ``grpc.aio`` so the agent's event loop
stays responsive even under bursts of concurrent kernel operations.
"""

from __future__ import annotations

import asyncio
import logging
from types import TracebackType
from typing import TYPE_CHECKING, Self, cast

import grpc
from grpc.aio import AioRpcError

from ai.backend.agent.errors.containerd import CriConnectionError, CriRpcError
from ai.backend.logging import BraceStyleAdapter

from .generated import api_pb2, api_pb2_grpc

if TYPE_CHECKING:
    # The *AsyncStub names exist only in the mypy-protobuf-generated
    # .pyi for type-checker consumption — the runtime .py emitted by
    # grpc_tools.protoc only defines the sync Stub classes. Importing
    # under TYPE_CHECKING keeps the names available for annotations and
    # cast() forward-refs without triggering an AttributeError at
    # runtime when the module is actually imported.
    from .generated.api_pb2_grpc import (
        ImageServiceAsyncStub,
        RuntimeServiceAsyncStub,
    )

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_CONTAINERD_SOCKET = "unix:///run/containerd/containerd.sock"

# Default upper bound for waiting on the gRPC channel to become ready.
# grpc.aio's channel_ready() retries internally with exponential backoff
# and never gives up on its own — without this guard, an unreachable
# socket (containerd not running, wrong path, missing permissions) hangs
# the caller indefinitely instead of producing an actionable error.
DEFAULT_CONNECT_TIMEOUT_SECS: float = 5.0

# Kubernetes Runtime API version requested in Version() calls. The
# string is opaque to the runtime but conventionally set to the CRI
# major version we vendored stubs for. See cri-api release-1.30
# api.proto for the canonical value.
RUNTIME_API_VERSION = "v1"


class CriClient:
    """High-level async CRI client for the host's containerd.

    Use as an async context manager so the gRPC channel is closed
    cleanly even on cancellation:

        async with CriClient() as cri:
            version = await cri.version()
    """

    _target: str
    _connect_timeout_secs: float
    _channel: grpc.aio.Channel | None
    # Annotations are deferred (`from __future__ import annotations`),
    # so referencing the TYPE_CHECKING-only names here is safe at runtime.
    _runtime_stub: RuntimeServiceAsyncStub | None
    _image_stub: ImageServiceAsyncStub | None

    def __init__(
        self,
        target: str = DEFAULT_CONTAINERD_SOCKET,
        *,
        connect_timeout_secs: float = DEFAULT_CONNECT_TIMEOUT_SECS,
    ) -> None:
        self._target = target
        self._connect_timeout_secs = connect_timeout_secs
        self._channel = None
        self._runtime_stub = None
        self._image_stub = None

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
        """Open the gRPC channel to containerd's CRI endpoint.

        ``grpc.aio.insecure_channel`` returns immediately and lazy-
        connects on the first RPC; ``channel_ready()`` actively probes
        until the channel is usable. We wrap that probe in a timeout
        because grpc.aio retries forever otherwise — an unreachable
        socket (containerd not running, wrong path, missing permissions)
        would hang the caller indefinitely with no log line to diagnose.
        """
        if self._channel is not None:
            return
        log.debug("Opening CRI channel to {}", self._target)
        channel = grpc.aio.insecure_channel(self._target)
        try:
            await asyncio.wait_for(channel.channel_ready(), timeout=self._connect_timeout_secs)
        except TimeoutError as exc:
            await channel.close()
            raise CriConnectionError(
                f"Timed out after {self._connect_timeout_secs:.1f}s waiting for containerd "
                f"CRI at {self._target}. Check that containerd is running and the socket "
                f"path / permissions are correct (try `crictl --runtime-endpoint {self._target} "
                "version`)."
            ) from exc
        except AioRpcError as exc:
            await channel.close()
            raise CriConnectionError(
                f"Could not connect to containerd CRI at {self._target}: {exc.details()}"
            ) from exc
        self._channel = channel
        # mypy-protobuf emits *AsyncStub names ONLY in the .pyi for
        # type checking — they don't exist at runtime, only the sync
        # Stub class is generated by grpc_tools.protoc. The sync class
        # works transparently against an aio channel (its method
        # callables become awaitable when the channel is aio), so we
        # instantiate the real sync class and cast to the aio-typed
        # alias via a forward-reference string so the type name is
        # never evaluated at runtime.
        self._runtime_stub = cast(
            "RuntimeServiceAsyncStub",
            api_pb2_grpc.RuntimeServiceStub(channel),
        )
        self._image_stub = cast(
            "ImageServiceAsyncStub",
            api_pb2_grpc.ImageServiceStub(channel),
        )

    async def close(self) -> None:
        if self._channel is None:
            return
        await self._channel.close()
        self._channel = None
        self._runtime_stub = None
        self._image_stub = None

    async def version(self) -> api_pb2.VersionResponse:
        """Return the runtime's version info — used as a health probe."""
        stub = self._require_runtime_stub()
        request = api_pb2.VersionRequest(version=RUNTIME_API_VERSION)
        try:
            # grpc.aio's UnaryUnaryMultiCallable.__call__ stub is loosely
            # typed (returns Any when awaited); annotate locally so the
            # public signature stays precise.
            response: api_pb2.VersionResponse = await stub.Version(request)
        except AioRpcError as exc:
            raise CriConnectionError(
                f"CRI Version() call against {self._target} failed: {exc.details()}"
            ) from exc
        return response

    # ------------------------------------------------------------------ #
    # PodSandbox lifecycle
    # ------------------------------------------------------------------ #
    #
    # Every CRI workload is anchored to a "pod sandbox" — a pause-image
    # container that owns the network (and optionally IPC/PID) namespace
    # the actual workload containers join. CNI ADD fires once at sandbox
    # creation, not per workload container; everything we care about for
    # the cilium-mode V1 PoC (eBPF datapath attach, IP assignment,
    # reserved:init identity, IP release on DEL) happens at this layer.
    #
    # Methods take and return raw proto objects so the caller controls the
    # full PodSandboxConfig surface (metadata, namespace_options, labels,
    # annotations, dns_config, …). High-level builders that translate from
    # KernelCreationConfig into a PodSandboxConfig live in the agent layer
    # once we wire ContainerdAgent — keeping them out of this module
    # avoids leaking kernel-domain concepts into the CRI wrapper.

    async def run_pod_sandbox(
        self,
        config: api_pb2.PodSandboxConfig,
        runtime_handler: str = "",
    ) -> str:
        """Create + start a pod sandbox; return the sandbox ID."""
        stub = self._require_runtime_stub()
        request = api_pb2.RunPodSandboxRequest(
            config=config,
            runtime_handler=runtime_handler,
        )
        try:
            response: api_pb2.RunPodSandboxResponse = await stub.RunPodSandbox(request)
        except AioRpcError as exc:
            raise CriRpcError(
                f"CRI RunPodSandbox failed for sandbox '{config.metadata.name}' "
                f"in synthetic namespace '{config.metadata.namespace}': {exc.details()}"
            ) from exc
        return response.pod_sandbox_id

    async def stop_pod_sandbox(self, sandbox_id: str) -> None:
        """Stop a pod sandbox (triggers CNI DEL — IP returns to the pool)."""
        stub = self._require_runtime_stub()
        request = api_pb2.StopPodSandboxRequest(pod_sandbox_id=sandbox_id)
        try:
            await stub.StopPodSandbox(request)
        except AioRpcError as exc:
            raise CriRpcError(
                f"CRI StopPodSandbox failed for sandbox {sandbox_id}: {exc.details()}"
            ) from exc

    async def remove_pod_sandbox(self, sandbox_id: str) -> None:
        """Remove a stopped pod sandbox (frees the pause container + netns)."""
        stub = self._require_runtime_stub()
        request = api_pb2.RemovePodSandboxRequest(pod_sandbox_id=sandbox_id)
        try:
            await stub.RemovePodSandbox(request)
        except AioRpcError as exc:
            raise CriRpcError(
                f"CRI RemovePodSandbox failed for sandbox {sandbox_id}: {exc.details()}"
            ) from exc

    async def pod_sandbox_status(
        self,
        sandbox_id: str,
        *,
        verbose: bool = False,
    ) -> api_pb2.PodSandboxStatusResponse:
        """Return the sandbox's runtime state, including network info."""
        stub = self._require_runtime_stub()
        request = api_pb2.PodSandboxStatusRequest(
            pod_sandbox_id=sandbox_id,
            verbose=verbose,
        )
        try:
            response: api_pb2.PodSandboxStatusResponse = await stub.PodSandboxStatus(request)
        except AioRpcError as exc:
            raise CriRpcError(
                f"CRI PodSandboxStatus failed for sandbox {sandbox_id}: {exc.details()}"
            ) from exc
        return response

    async def list_pod_sandbox(
        self,
        *,
        sandbox_filter: api_pb2.PodSandboxFilter | None = None,
    ) -> list[api_pb2.PodSandbox]:
        """List sandboxes matching the optional filter (used for reconciliation)."""
        stub = self._require_runtime_stub()
        request = api_pb2.ListPodSandboxRequest(filter=sandbox_filter)
        try:
            response: api_pb2.ListPodSandboxResponse = await stub.ListPodSandbox(request)
        except AioRpcError as exc:
            raise CriRpcError(f"CRI ListPodSandbox failed: {exc.details()}") from exc
        return list(response.items)

    # ------------------------------------------------------------------ #
    # Container lifecycle
    # ------------------------------------------------------------------ #
    #
    # Once a sandbox exists (with its netns + CNI-assigned interface),
    # workload containers are created inside it. They join the sandbox's
    # network namespace, so all containers in a sandbox share the IP that
    # CNI assigned at RunPodSandbox time. For Backend.AI's "1 kernel = 1
    # workload container in its own sandbox" model, this is a 1:1 wrapping
    # — no sidecar pattern.
    #
    # CreateContainer must be passed the same PodSandboxConfig that was
    # used for RunPodSandbox (the proto demands it for cross-validation,
    # even though the runtime already has the sandbox state).

    async def create_container(
        self,
        *,
        sandbox_id: str,
        config: api_pb2.ContainerConfig,
        sandbox_config: api_pb2.PodSandboxConfig,
    ) -> str:
        """Create a workload container inside an existing sandbox; return container ID."""
        stub = self._require_runtime_stub()
        request = api_pb2.CreateContainerRequest(
            pod_sandbox_id=sandbox_id,
            config=config,
            sandbox_config=sandbox_config,
        )
        try:
            response: api_pb2.CreateContainerResponse = await stub.CreateContainer(request)
        except AioRpcError as exc:
            raise CriRpcError(
                f"CRI CreateContainer failed in sandbox {sandbox_id} "
                f"for container '{config.metadata.name}': {exc.details()}"
            ) from exc
        return response.container_id

    async def start_container(self, container_id: str) -> None:
        """Start a previously created container."""
        stub = self._require_runtime_stub()
        request = api_pb2.StartContainerRequest(container_id=container_id)
        try:
            await stub.StartContainer(request)
        except AioRpcError as exc:
            raise CriRpcError(
                f"CRI StartContainer failed for container {container_id}: {exc.details()}"
            ) from exc

    async def stop_container(self, container_id: str, *, grace_period_secs: int = 0) -> None:
        """Stop a running container.

        ``grace_period_secs`` maps to CRI's ``StopContainerRequest.timeout``
        — the grace period before forced termination (SIGTERM → wait →
        SIGKILL). Default 0 mirrors CRI's "kill immediately" behaviour;
        callers wanting a graceful shutdown should pass an explicit
        non-zero value. Renamed from the proto's ``timeout`` so it cannot
        be confused with an asyncio call timeout.
        """
        stub = self._require_runtime_stub()
        request = api_pb2.StopContainerRequest(container_id=container_id, timeout=grace_period_secs)
        try:
            await stub.StopContainer(request)
        except AioRpcError as exc:
            raise CriRpcError(
                f"CRI StopContainer failed for container {container_id}: {exc.details()}"
            ) from exc

    async def remove_container(self, container_id: str) -> None:
        """Remove a stopped container (frees rootfs + container metadata)."""
        stub = self._require_runtime_stub()
        request = api_pb2.RemoveContainerRequest(container_id=container_id)
        try:
            await stub.RemoveContainer(request)
        except AioRpcError as exc:
            raise CriRpcError(
                f"CRI RemoveContainer failed for container {container_id}: {exc.details()}"
            ) from exc

    async def list_containers(
        self,
        *,
        container_filter: api_pb2.ContainerFilter | None = None,
    ) -> list[api_pb2.Container]:
        """List containers matching the optional filter."""
        stub = self._require_runtime_stub()
        request = api_pb2.ListContainersRequest(filter=container_filter)
        try:
            response: api_pb2.ListContainersResponse = await stub.ListContainers(request)
        except AioRpcError as exc:
            raise CriRpcError(f"CRI ListContainers failed: {exc.details()}") from exc
        return list(response.containers)

    async def container_status(
        self,
        container_id: str,
        *,
        verbose: bool = False,
    ) -> api_pb2.ContainerStatusResponse:
        """Return the container's runtime state."""
        stub = self._require_runtime_stub()
        request = api_pb2.ContainerStatusRequest(
            container_id=container_id,
            verbose=verbose,
        )
        try:
            response: api_pb2.ContainerStatusResponse = await stub.ContainerStatus(request)
        except AioRpcError as exc:
            raise CriRpcError(
                f"CRI ContainerStatus failed for container {container_id}: {exc.details()}"
            ) from exc
        return response

    # ------------------------------------------------------------------ #
    # Image management
    # ------------------------------------------------------------------ #
    #
    # CRI separates image management onto its own service (ImageService)
    # because it has different concurrency / progress-reporting characteristics
    # than the runtime service (image pulls can take minutes; runtime ops
    # are typically sub-second).
    #
    # PullImage is intentionally exposed as a single awaitable rather than a
    # streaming progress channel — CRI's PullImage is a unary RPC that
    # blocks until the pull finishes (or fails). For long pulls the agent
    # already wraps these calls in BackgroundTask handlers; per-byte
    # progress is not exposed by CRI.

    async def pull_image(
        self,
        image: api_pb2.ImageSpec,
        *,
        auth: api_pb2.AuthConfig | None = None,
        sandbox_config: api_pb2.PodSandboxConfig | None = None,
    ) -> str:
        """Pull an image; return the runtime's image reference (id or digest)."""
        stub = self._require_image_stub()
        request = api_pb2.PullImageRequest(
            image=image,
            auth=auth,
            sandbox_config=sandbox_config,
        )
        try:
            response: api_pb2.PullImageResponse = await stub.PullImage(request)
        except AioRpcError as exc:
            raise CriRpcError(
                f"CRI PullImage failed for image '{image.image}': {exc.details()}"
            ) from exc
        return response.image_ref

    async def image_status(
        self,
        image: api_pb2.ImageSpec,
        *,
        verbose: bool = False,
    ) -> api_pb2.ImageStatusResponse:
        """Return image metadata; ``image.image`` may be missing if not present."""
        stub = self._require_image_stub()
        request = api_pb2.ImageStatusRequest(image=image, verbose=verbose)
        try:
            response: api_pb2.ImageStatusResponse = await stub.ImageStatus(request)
        except AioRpcError as exc:
            raise CriRpcError(
                f"CRI ImageStatus failed for image '{image.image}': {exc.details()}"
            ) from exc
        return response

    async def list_images(
        self,
        *,
        image_filter: api_pb2.ImageFilter | None = None,
    ) -> list[api_pb2.Image]:
        """List images known to the runtime."""
        stub = self._require_image_stub()
        request = api_pb2.ListImagesRequest(filter=image_filter)
        try:
            response: api_pb2.ListImagesResponse = await stub.ListImages(request)
        except AioRpcError as exc:
            raise CriRpcError(f"CRI ListImages failed: {exc.details()}") from exc
        return list(response.images)

    async def remove_image(self, image: api_pb2.ImageSpec) -> None:
        """Remove an image from the runtime's image store."""
        stub = self._require_image_stub()
        request = api_pb2.RemoveImageRequest(image=image)
        try:
            await stub.RemoveImage(request)
        except AioRpcError as exc:
            raise CriRpcError(
                f"CRI RemoveImage failed for image '{image.image}': {exc.details()}"
            ) from exc

    def _require_runtime_stub(self) -> RuntimeServiceAsyncStub:
        if self._runtime_stub is None:
            raise CriConnectionError(
                "CRI client is not connected; call connect() or use it as an async context manager."
            )
        return self._runtime_stub

    def _require_image_stub(self) -> ImageServiceAsyncStub:
        if self._image_stub is None:
            raise CriConnectionError(
                "CRI client is not connected; call connect() or use it as an async context manager."
            )
        return self._image_stub
