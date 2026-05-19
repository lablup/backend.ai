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

Snapshots, containers and tasks land in later increments. Everything goes
through ``grpc.aio`` so the agent event loop stays responsive.
"""

from __future__ import annotations

import asyncio
import logging
import os
from types import TracebackType
from typing import TYPE_CHECKING, Self, TypeVar, cast

import grpc
from google.protobuf import any_pb2, empty_pb2
from google.protobuf.message import Message
from grpc.aio import AioRpcError

from ai.backend.agent.errors.containerd import (
    ContainerdConnectionError,
    ContainerdRpcError,
)
from ai.backend.logging import BraceStyleAdapter

from .generated.containerd.services.namespaces.v1 import namespace_pb2, namespace_pb2_grpc
from .generated.containerd.services.transfer.v1 import transfer_pb2, transfer_pb2_grpc
from .generated.containerd.services.version.v1 import version_pb2, version_pb2_grpc
from .generated.containerd.types import platform_pb2
from .generated.containerd.types.transfer import imagestore_pb2, registry_pb2

if TYPE_CHECKING:
    # mypy-protobuf emits the *AsyncStub types for type-checking only
    # (decorated @type_check_only); importing them under TYPE_CHECKING
    # keeps the names available for annotations without a runtime import.
    from .generated.containerd.services.namespaces.v1.namespace_pb2_grpc import (
        NamespacesAsyncStub,
    )
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

    async def close(self) -> None:
        if self._channel is None:
            return
        await self._channel.close()
        self._channel = None
        self._version = None
        self._namespaces = None
        self._transfer = None

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

    def _require(self, stub: _StubT | None) -> _StubT:
        if stub is None:
            raise ContainerdConnectionError(
                "containerd client is not connected; call connect() or use it "
                "as an async context manager."
            )
        return stub
