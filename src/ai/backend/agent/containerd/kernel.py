"""Containerd kernel + code runner (BEP-1055 / containerd agent backend).

Mirrors the Docker kernel contract but targets containerd's native task model.
Container-facing operations that require the containerd gRPC client are marked
``NotImplementedError`` (TODO: containerd) — this is a structural scaffold, not yet a
functional backend. Trivial/metadata methods return sensible defaults so the class is
concrete and selectable.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any, override

from ai.backend.agent.kernel import (
    AbstractCodeRunner,
    AbstractKernel,
    KernelRunnerNotInitializedError,
)
from ai.backend.agent.types import AgentEventData, KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.dto.agent.response import CodeCompletionResp
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import CommitStatus, KernelId, SessionId

_TODO = "containerd backend: not yet implemented (requires containerd gRPC client)"


class ContainerdKernel(AbstractKernel):
    def __init__(
        self,
        ownership_data: KernelOwnershipData,
        network_id: str,
        image: ImageRef,
        version: int,
        *,
        agent_config: Mapping[str, Any],
        resource_spec: Any,
        service_ports: Any,
        environ: Mapping[str, Any],
        data: dict[str, Any],
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
        return await ContainerdCodeRunner.new(
            self.kernel_id,
            self.session_id,
            event_producer,
            kernel_host=self.data["kernel_host"],
            repl_in_port=self.data["repl_in_port"],
            repl_out_port=self.data["repl_out_port"],
            exec_timeout=0,
            client_features=client_features,
        )

    def _require_runner(self) -> AbstractCodeRunner:
        if self.runner is None:
            raise KernelRunnerNotInitializedError("Kernel runner is not initialized")
        return self.runner

    @override
    async def check_status(self) -> dict[str, Any]:
        return await self._require_runner().feed_and_get_status()

    @override
    async def get_completions(self, text: str, opts: Mapping[str, Any]) -> CodeCompletionResp:
        result = await self._require_runner().feed_and_get_completion(text, opts)
        return CodeCompletionResp(result=result)

    @override
    async def get_logs(self) -> dict[str, Any]:
        # TODO: fetch task logs via the runtime client (nerdctl logs); needs runtime access.
        raise NotImplementedError(_TODO)

    @override
    async def interrupt_kernel(self) -> dict[str, Any]:
        await self._require_runner().feed_interrupt()
        return {"status": "finished"}

    @override
    async def start_service(self, service: str, opts: Mapping[str, Any]) -> dict[str, Any]:
        runner = self._require_runner()
        if self.data.get("block_service_ports", False):
            return {"status": "failed", "error": "operation blocked"}
        for sport in self.service_ports:
            if sport["name"] == service:
                break
        else:
            return {"status": "failed", "error": "invalid service name"}
        return await runner.feed_start_service({
            "name": service,
            "port": sport["container_ports"][0],
            "ports": sport["container_ports"],
            "protocol": sport["protocol"],
            "options": opts,
        })

    @override
    async def start_model_service(self, model_service: Mapping[str, Any]) -> dict[str, Any]:
        return await self._require_runner().feed_start_model_service(model_service)

    @override
    async def shutdown_service(self, service: str) -> None:
        await self._require_runner().feed_shutdown_service(service)

    @override
    async def check_duplicate_commit(self, kernel_id: KernelId, subdir: str) -> CommitStatus:
        raise NotImplementedError(_TODO)

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
        raise NotImplementedError(_TODO)

    @override
    async def get_service_apps(self) -> dict[str, Any]:
        return await self._require_runner().feed_service_apps()

    @override
    async def accept_file(self, container_path: os.PathLike[str] | str, filedata: bytes) -> None:
        raise NotImplementedError(_TODO)

    @override
    async def download_file(self, container_path: os.PathLike[str] | str) -> bytes:
        raise NotImplementedError(_TODO)

    @override
    async def download_single(self, container_path: os.PathLike[str] | str) -> bytes:
        raise NotImplementedError(_TODO)

    @override
    async def list_files(self, container_path: os.PathLike[str] | str) -> dict[str, Any]:
        raise NotImplementedError(_TODO)

    @override
    async def notify_event(self, evdata: AgentEventData) -> None:
        raise NotImplementedError(_TODO)


class ContainerdCodeRunner(AbstractCodeRunner):
    kernel_host: str
    repl_in_port: int
    repl_out_port: int

    def __init__(
        self,
        kernel_id: KernelId,
        session_id: SessionId,
        event_producer: EventProducer,
        *,
        kernel_host: str,
        repl_in_port: int,
        repl_out_port: int,
        exec_timeout: float = 0,
        client_features: frozenset[str] | None = None,
    ) -> None:
        super().__init__(
            kernel_id,
            session_id,
            event_producer,
            exec_timeout=exec_timeout,
            client_features=client_features,
        )
        self.kernel_host = kernel_host
        self.repl_in_port = repl_in_port
        self.repl_out_port = repl_out_port

    @override
    async def get_repl_in_addr(self) -> str:
        return f"tcp://{self.kernel_host}:{self.repl_in_port}"

    @override
    async def get_repl_out_addr(self) -> str:
        return f"tcp://{self.kernel_host}:{self.repl_out_port}"
