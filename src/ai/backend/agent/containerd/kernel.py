from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import ssl
from collections.abc import Mapping
from typing import Any, Final, override

from tenacity import TryAgain

from ai.backend.agent.containerd.profile.base import LaunchPlan, TlsConnectReadiness
from ai.backend.agent.errors.containerd import (
    ContainerdOperationFailed,
    KernelVerbNotSupported,
    ReadinessTimeout,
)
from ai.backend.agent.kernel import AbstractCodeRunner, AbstractKernel
from ai.backend.agent.resources import KernelResourceSpec
from ai.backend.agent.types import AgentEventData, KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.dto.agent.response import CodeCompletionResp
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import CommitStatus, KernelId
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

REPL_IN_PORT: Final = 2000
_PROBE_TIMEOUT_SEC: Final = 2.0
_TLS_CONNECT_TIMEOUT_SEC: Final = 5.0
# PROVISIONAL: the window and interval of one check_status call; a call can last up to
# window + connect timeout + interval, so init-timeout-sec must exceed that (20 s).
_TLS_PROBE_WINDOW_SEC: Final = 10.0
_TLS_RETRY_INTERVAL_SEC: Final = 1.0


class ContainerdKernel(AbstractKernel):
    launch_plan: LaunchPlan
    _readiness_deadline: float | None

    def __init__(
        self,
        ownership_data: KernelOwnershipData,
        network_id: str,
        image: ImageRef,
        version: int,
        *,
        agent_config: Mapping[str, Any],
        resource_spec: KernelResourceSpec,
        service_ports: Any,  # TODO: type-annotation
        environ: Mapping[str, Any],
        data: dict[str, Any],
        launch_plan: LaunchPlan,
    ) -> None:
        super().__init__(
            ownership_data,
            network_id,
            image,
            version,
            agent_config=agent_config,
            resource_spec=resource_spec,
            service_ports=service_ports,
            data=data,
            environ=environ,
        )
        self.launch_plan = launch_plan
        self._readiness_deadline = None

    @override
    async def init(self, event_producer: EventProducer) -> None:
        # The containerd agent creates no code runner.
        self.runner = None

    @override
    async def close(self) -> None:
        pass

    @override
    async def create_code_runner(
        self,
        event_producer: EventProducer,
        *,
        client_features: frozenset[str],
        api_version: int,
    ) -> AbstractCodeRunner:
        raise KernelVerbNotSupported("create_code_runner")

    # FIXME(containerd-mvp): probe only; no kernel status without a code runner.
    # KernelRunnerReadiness: a TCP connect to the REPL port; TlsConnectReadiness: a TLS handshake
    # through DNAT. TryAgain makes the create_kernel readiness loop retry.
    @override
    async def check_status(self) -> dict[str, Any] | None:
        readiness = self.launch_plan.readiness
        if isinstance(readiness, TlsConnectReadiness):
            return await self._check_tls_status(readiness)
        kernel_ip = self.data.get("kernel_ip")
        if not kernel_ip:
            raise ContainerdOperationFailed("the kernel data has no kernel IP")
        try:
            async with asyncio.timeout(_PROBE_TIMEOUT_SEC):
                _, writer = await asyncio.open_connection(kernel_ip, REPL_IN_PORT)
        except (OSError, TimeoutError) as e:
            raise TryAgain from e
        writer.close()
        with contextlib.suppress(OSError):
            await writer.wait_closed()
        return {}

    def _tls_target(self, readiness: TlsConnectReadiness) -> tuple[str, int]:
        # PROVISIONAL: probe the DNAT path (published host + host port), not the kernel IP.
        host = self.data.get("published_host")
        if not host:
            raise ContainerdOperationFailed("the kernel data has no published host")
        for port in self.service_ports:
            if port["name"] == readiness.port_name:
                host_port = port["host_ports"][0] if port["host_ports"] else None
                if host_port is None:
                    break
                return str(host), int(host_port)
        raise ContainerdOperationFailed(
            f"the kernel has no published service port {readiness.port_name!r}"
        )

    async def _check_tls_status(self, readiness: TlsConnectReadiness) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        host, port = self._tls_target(readiness)
        if self._readiness_deadline is None:
            self._readiness_deadline = loop.time() + readiness.timeout_s
        deadline = self._readiness_deadline
        if loop.time() >= deadline:
            raise ReadinessTimeout(f"no TLS handshake on {host}:{port} in {readiness.timeout_s} s")
        window_end = loop.time() + _TLS_PROBE_WINDOW_SEC
        # Readiness proves the handshake only; the TD cert is self-signed (ADR 0049)
        # and appraised by `cc verify` (ADR 0067).
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        while True:
            try:
                async with asyncio.timeout(_TLS_CONNECT_TIMEOUT_SEC):
                    _, writer = await asyncio.open_connection(host, port, ssl=context)
            except (OSError, ssl.SSLError, asyncio.IncompleteReadError, TimeoutError) as e:
                log.debug(
                    "tls handshake failed",
                    kernel_id=str(self.kernel_id),
                    port=port,
                    error=repr(e),
                )
                now = loop.time()
                if now >= deadline:
                    raise ReadinessTimeout(
                        f"no TLS handshake on {host}:{port} in {readiness.timeout_s} s"
                    ) from e
                if now >= window_end:
                    raise TryAgain from e
                await asyncio.sleep(min(_TLS_RETRY_INTERVAL_SEC, deadline - now))
                continue
            writer.close()
            with contextlib.suppress(OSError, ssl.SSLError):
                await writer.wait_closed()
            return {}

    @override
    async def get_completions(self, text: str, opts: Mapping[str, Any]) -> CodeCompletionResp:
        raise KernelVerbNotSupported("get_completions")

    @override
    async def get_logs(self) -> dict[str, Any]:
        raise KernelVerbNotSupported("get_logs")

    @override
    async def interrupt_kernel(self) -> dict[str, Any]:
        raise KernelVerbNotSupported("interrupt_kernel")

    # FIXME(containerd-mvp): no service is started; the manager proceeds to the app-proxy token
    @override
    async def start_service(self, service: str, opts: Mapping[str, Any]) -> dict[str, Any]:
        return {"status": "started"}

    # FIXME(containerd-mvp): no model service is started by the agent
    @override
    async def start_model_service(self, model_service: Mapping[str, Any]) -> dict[str, Any]:
        return {"status": "started"}

    @override
    async def shutdown_service(self, service: str) -> None:
        raise KernelVerbNotSupported("shutdown_service")

    @override
    async def check_duplicate_commit(self, kernel_id: KernelId, subdir: str) -> CommitStatus:
        raise KernelVerbNotSupported("check_duplicate_commit")

    @override
    async def commit(
        self,
        kernel_id: KernelId,
        subdir: str,
        *,
        canonical: str | None = None,
        filename: str | None = None,
        extra_labels: dict[str, str] | None = None,
    ) -> None:
        raise KernelVerbNotSupported("commit")

    # FIXME(containerd-mvp): no service apps are reported
    @override
    async def get_service_apps(self) -> dict[str, Any]:
        return {"status": "ok", "data": []}

    @override
    async def accept_file(self, container_path: os.PathLike[str] | str, filedata: bytes) -> None:
        raise KernelVerbNotSupported("accept_file")

    @override
    async def download_file(self, container_path: os.PathLike[str] | str) -> bytes:
        raise KernelVerbNotSupported("download_file")

    @override
    async def download_single(self, container_path: os.PathLike[str] | str) -> bytes:
        raise KernelVerbNotSupported("download_single")

    @override
    async def list_files(self, container_path: os.PathLike[str] | str) -> dict[str, Any]:
        raise KernelVerbNotSupported("list_files")

    @override
    async def notify_event(self, evdata: AgentEventData) -> None:
        raise KernelVerbNotSupported("notify_event")
