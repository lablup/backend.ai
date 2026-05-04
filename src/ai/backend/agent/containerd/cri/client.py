"""Async CRI gRPC client for the containerd backend.

This module wraps the auto-generated stubs in ``cri.generated`` with a
small high-level surface that the agent uses. Only the bare minimum
needed to validate end-to-end gRPC plumbing (``Version()``) is exposed
in this commit; image, sandbox, and container operations land in
follow-ups.

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

from ai.backend.agent.errors.containerd import CriConnectionError
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

    def _require_runtime_stub(self) -> api_pb2_grpc.RuntimeServiceAsyncStub:
        if self._runtime_stub is None:
            raise CriConnectionError(
                "CRI client is not connected; call connect() or use it as an async context manager."
            )
        return self._runtime_stub
