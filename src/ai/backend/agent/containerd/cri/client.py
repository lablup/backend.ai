"""Async CRI gRPC client for the containerd backend.

This module wraps the auto-generated stubs in ``cri.generated`` with a
small high-level surface that the agent uses. Currently exposed:
``Version()`` plus the PodSandbox lifecycle (``RunPodSandbox`` /
``StopPodSandbox`` / ``RemovePodSandbox`` / ``PodSandboxStatus`` /
``ListPodSandbox``). Container and image operations land in follow-up
commits.

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

import logging
from types import TracebackType
from typing import Self

import grpc
from grpc.aio import AioRpcError

from ai.backend.agent.errors.containerd import CriConnectionError, CriRpcError
from ai.backend.logging import BraceStyleAdapter

from .generated import api_pb2, api_pb2_grpc

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_CONTAINERD_SOCKET = "unix:///run/containerd/containerd.sock"

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
    _channel: grpc.aio.Channel | None
    _runtime_stub: api_pb2_grpc.RuntimeServiceAsyncStub | None
    _image_stub: api_pb2_grpc.ImageServiceAsyncStub | None

    def __init__(self, target: str = DEFAULT_CONTAINERD_SOCKET) -> None:
        self._target = target
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
        connects on the first RPC; we still call ``channel_ready()``
        here so a misconfigured socket path / permission issue surfaces
        at agent startup rather than at first kernel creation.
        """
        if self._channel is not None:
            return
        log.debug("Opening CRI channel to {}", self._target)
        channel = grpc.aio.insecure_channel(self._target)
        try:
            await channel.channel_ready()
        except AioRpcError as exc:
            await channel.close()
            raise CriConnectionError(
                f"Could not connect to containerd CRI at {self._target}: {exc.details()}"
            ) from exc
        self._channel = channel
        # mypy-protobuf generates *AsyncStub aliases (subclassing the sync
        # Stub) that carry the awaitable signatures we need under grpc.aio,
        # but only the sync class actually exists at runtime. The two are
        # interchangeable at runtime — the channel decides whether the
        # returned callables are awaitable.
        self._runtime_stub = api_pb2_grpc.RuntimeServiceAsyncStub(channel)
        self._image_stub = api_pb2_grpc.ImageServiceAsyncStub(channel)

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

    def _require_runtime_stub(self) -> api_pb2_grpc.RuntimeServiceAsyncStub:
        if self._runtime_stub is None:
            raise CriConnectionError(
                "CRI client is not connected; call connect() or use it as an async context manager."
            )
        return self._runtime_stub
