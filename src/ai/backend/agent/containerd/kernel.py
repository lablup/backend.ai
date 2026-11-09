from __future__ import annotations

import asyncio
import logging
import os
import ssl
from collections.abc import Mapping
from typing import Any, Final, override

from tenacity import TryAgain

from ai.backend.agent.containerd.profile.base import LaunchPlan, TlsConnectReadiness
from ai.backend.agent.containerd.rpc.client import ContainerdAPI
from ai.backend.agent.containerd.rpc.types import TaskState
from ai.backend.agent.errors.containerd import (
    ContainerdOperationFailed,
    KernelTaskExited,
    KernelVerbNotSupported,
    ReadinessTimeout,
)
from ai.backend.agent.kernel import AbstractCodeRunner, AbstractKernel
from ai.backend.agent.resources import KernelResourceSpec
from ai.backend.agent.types import AgentEventData, KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.dto.agent.response import CodeCompletionResp
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import CommitStatus, KernelId
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

_TLS_CONNECT_TIMEOUT_SEC: Final = 5.0
# One check_status call probes for up to this window, then raises TryAgain to the create_kernel loop.
_TLS_PROBE_WINDOW_SEC: Final = 10.0
_TLS_RETRY_INTERVAL_SEC: Final = 1.0


class ContainerdKernel(AbstractKernel):
    launch_plan: LaunchPlan | None
    _client: ContainerdAPI
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
        service_ports: Any,
        data: dict[Any, Any],
        environ: Mapping[str, Any],
        client: ContainerdAPI,
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
        # Set by start_container, where the profile plans the launch.
        self.launch_plan = None
        self._client = client
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

    @override
    async def check_status(self) -> dict[str, Any] | None:
        # FIXME(containerd-mvp): no code runner; without a readiness the started task counts as ready
        readiness = self.launch_plan.readiness if self.launch_plan else None
        if readiness is None:
            return {}
        return await self._check_tls_status(readiness)

    def _tls_target(self, readiness: TlsConnectReadiness) -> tuple[str, int]:
        # The DNAT path (published host and host port), not the kernel IP.
        host = self.data.get("published_host")
        if not host:
            raise ContainerdOperationFailed("the kernel data has no published host")
        for port in self.service_ports:
            if port["name"] != readiness.port_name:
                continue
            host_port = next((p for p in port["host_ports"] if p is not None), None)
            if host_port is not None:
                return str(host), host_port
        raise ContainerdOperationFailed(
            f"the kernel has no published service port {readiness.port_name!r}"
        )

    async def _raise_if_task_exited(self) -> None:
        # A task that exited can never answer the handshake: end the wait before its timeout.
        container_id = self.data.get("container_id")
        if not container_id:
            return
        try:
            task = await self._client.get_task(container_id)
        except BackendAIError as e:
            log.debug("kernel task lookup failed", kernel_id=str(self.kernel_id), error=repr(e))
            return
        if task is None:
            raise KernelTaskExited(f"the kernel task is gone (container {container_id})")
        if task.state is TaskState.STOPPED:
            raise KernelTaskExited(
                f"the kernel task exited with status {task.exit_status} (container {container_id})"
            )

    async def _check_tls_status(self, readiness: TlsConnectReadiness) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        host, port = self._tls_target(readiness)
        if self._readiness_deadline is None:
            self._readiness_deadline = loop.time() + readiness.timeout_s
        deadline = self._readiness_deadline
        timeout_message = f"no TLS handshake on {host}:{port} in {readiness.timeout_s} s"
        if loop.time() >= deadline:
            raise ReadinessTimeout(timeout_message)
        window_end = loop.time() + _TLS_PROBE_WINDOW_SEC
        # Readiness proves the handshake only; the TD cert is self-signed and appraised elsewhere.
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        while True:
            try:
                left = min(deadline, window_end) - loop.time()
                async with asyncio.timeout(min(_TLS_CONNECT_TIMEOUT_SEC, max(left, 0.01))):
                    _, writer = await asyncio.open_connection(host, port, ssl=context)
            except (OSError, TimeoutError) as e:
                log.debug(
                    "tls handshake failed",
                    kernel_id=str(self.kernel_id),
                    port=port,
                    error=repr(e),
                )
                await self._raise_if_task_exited()
                now = loop.time()
                if now >= deadline:
                    raise ReadinessTimeout(timeout_message) from e
                if now >= window_end:
                    raise TryAgain from e
                await asyncio.sleep(min(_TLS_RETRY_INTERVAL_SEC, deadline - now))
                continue
            # The probe sends no data; abort skips the unbounded close_notify exchange.
            writer.transport.abort()
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
