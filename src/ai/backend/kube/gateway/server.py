"""The kernel-level part of the Agent RPC contract, served for the kernels of one cluster.

The Manager calls the session gateway as it calls an Agent (`AgentClient`), with the same
CurveZMQ authentication: the gateway accepts only the manager public key.
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Awaitable, Callable
from typing import Any, Literal
from uuid import UUID

from callosum.lower.zeromq import ZeroMQAddress, ZeroMQRPCTransport
from callosum.ordering import AbstractAsyncScheduler, ExitOrderedAsyncScheduler
from callosum.rpc import Peer, RPCMessage

from ai.backend.common import msgpack
from ai.backend.common.auth import AgentAuthHandler, PublicKey, SecretKey
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import SessionId
from ai.backend.kube.errors import NodeHelperCommandError
from ai.backend.kube.gateway.images import GatewayImages
from ai.backend.kube.gateway.kernels import GatewayKernels
from ai.backend.logging.structured import StructuredLogger, with_log_context

log = StructuredLogger(logging.getLogger(__spec__.name))

RPCHandler = Callable[[RPCMessage], Awaitable[Any]]
# callosum's scheduler constructor is unannotated; calling it through this typed alias keeps
# the call checked without a type-ignore.
_new_scheduler: Callable[[], AbstractAsyncScheduler] = ExitOrderedAsyncScheduler


class GatewayRPCServer:
    _kernels: GatewayKernels
    _images: GatewayImages | None
    _gateway_id: str
    _peer: Peer
    _bind: str

    def __init__(
        self,
        kernels: GatewayKernels,
        *,
        images: GatewayImages | None = None,
        gateway_id: str,
        bind: str,
        manager_public_key: PublicKey,
        public_key: PublicKey,
        secret_key: SecretKey,
    ) -> None:
        self._kernels = kernels
        self._images = images
        self._gateway_id = gateway_id
        self._bind = bind
        self._peer = Peer(
            bind=ZeroMQAddress(f"tcp://{bind}"),
            transport=ZeroMQRPCTransport,
            authenticator=AgentAuthHandler("local", manager_public_key, public_key, secret_key),
            scheduler=_new_scheduler(),
            serializer=msgpack.packb,
            deserializer=msgpack.unpackb,
        )
        handlers: dict[str, Callable[..., Awaitable[Any]]] = {
            "ping": self.ping,
            "check_and_pull": self.check_and_pull,
            "check_running": self.check_running,
            "execute": self.execute,
            "interrupt_kernel": self.interrupt_kernel,
            "get_completions": self.get_completions,
            "trigger_batch_execution": self.trigger_batch_execution,
            "start_service": self.start_service,
            "shutdown_service": self.shutdown_service,
            "upload_file": self.upload_file,
            "download_file": self.download_file,
            "download_single": self.download_single,
            "list_files": self.list_files,
            "get_logs": self.get_logs,
            "commit": self.commit,
            "push_image": self.push_image,
        }
        for name, meth in handlers.items():
            self._peer.handle_function(name, _unpack(name, meth))

    async def __aenter__(self) -> GatewayRPCServer:
        await self._peer.__aenter__()
        log.info("session gateway rpc server started", rpc_addr=self._bind)
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self._peer.__aexit__(*exc_info)

    async def ping(self, msg: str, agent_id: str | None = None) -> str:
        return msg

    async def check_and_pull(
        self, image_configs: dict[str, Any], agent_id: str | None = None
    ) -> dict[str, str]:
        await self._kernels.images_ready(self._gateway_id, list(image_configs))
        return {}

    async def check_running(self, kernel_id: str, agent_id: str | None = None) -> bool:
        return self._kernels.is_running(kernel_id)

    async def execute(
        self,
        session_id: str,
        kernel_id: str,
        api_version: int,
        run_id: str,
        mode: Literal["query", "batch", "continue", "input"],
        code: str,
        opts: dict[str, Any],
        flush_timeout: float,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        return await self._kernels.execute(
            SessionId(UUID(session_id)),
            kernel_id,
            run_id,
            mode,
            code,
            opts=opts,
            api_version=api_version,
            flush_timeout=flush_timeout,
        )

    async def interrupt_kernel(self, kernel_id: str, agent_id: str | None = None) -> dict[str, Any]:
        return await self._kernels.interrupt(kernel_id)

    async def get_completions(
        self, kernel_id: str, text: str, opts: dict[str, Any], agent_id: str | None = None
    ) -> dict[str, Any]:
        return (await self._kernels.get_completions(kernel_id, text, opts)).as_dict()

    async def trigger_batch_execution(
        self,
        session_id: str,
        kernel_id: str,
        code: str,
        timeout_seconds: float | None,
        agent_id: str | None = None,
    ) -> None:
        self._kernels.start_batch(SessionId(UUID(session_id)), kernel_id, code, timeout_seconds)

    async def start_service(
        self, kernel_id: str, service: str, opts: dict[str, Any], agent_id: str | None = None
    ) -> dict[str, Any]:
        return await self._kernels.start_service(kernel_id, service, opts)

    async def shutdown_service(
        self, kernel_id: str, service: str, agent_id: str | None = None
    ) -> None:
        await self._kernels.shutdown_service(kernel_id, service)

    async def upload_file(
        self, kernel_id: str, filename: str, filedata: bytes, agent_id: str | None = None
    ) -> None:
        await self._kernels.upload_file(kernel_id, filename, filedata)

    async def download_file(
        self, kernel_id: str, filepath: str, agent_id: str | None = None
    ) -> bytes:
        return await self._kernels.download_file(kernel_id, filepath)

    async def download_single(
        self, kernel_id: str, filepath: str, agent_id: str | None = None
    ) -> bytes:
        return await self._kernels.download_single(kernel_id, filepath)

    async def list_files(
        self, kernel_id: str, path: str, agent_id: str | None = None
    ) -> dict[str, Any]:
        return await self._kernels.list_files(kernel_id, path)

    async def get_logs(self, kernel_id: str, agent_id: str | None = None) -> dict[str, Any]:
        return await self._kernels.get_logs(kernel_id)

    async def commit(
        self,
        kernel_id: str,
        subdir: str,
        *,
        canonical: str | None = None,
        filename: str | None = None,
        extra_labels: dict[str, str] | None = None,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        """Only a commit into an image (`canonical`); a commit into a file is the Agent's."""
        if self._images is None or canonical is None or filename is not None:
            raise NodeHelperCommandError("this cluster commits sessions into images only")
        task_id = self._images.commit(kernel_id, canonical, extra_labels or {})
        return {"bgtask_id": task_id, "kernel": kernel_id, "path": None}

    async def push_image(
        self,
        image_ref: ImageRef,
        registry_conf: dict[str, Any],
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        if self._images is None:
            raise NodeHelperCommandError("this cluster has no node helper")
        return {"bgtask_id": self._images.push(image_ref, registry_conf)}


def _unpack(name: str, meth: Callable[..., Awaitable[Any]]) -> RPCHandler:
    """Adapt a method to callosum's (request) → result handler, as the Agent RPC server does."""

    @functools.wraps(meth)
    async def _handler(request: RPCMessage) -> Any:
        body = request.body or {}
        args = body.get("args", ())
        kwargs = body.get("kwargs", {})
        with with_log_context(rpc_method=name):
            try:
                return await meth(*args, **kwargs)
            except Exception:
                log.exception("rpc handler failed")
                raise

    return _handler
