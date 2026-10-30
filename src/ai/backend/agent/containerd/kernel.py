from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any, override

from ai.backend.agent.errors.containerd import KernelVerbNotSupported
from ai.backend.agent.kernel import AbstractCodeRunner, AbstractKernel
from ai.backend.agent.types import AgentEventData
from ai.backend.common.dto.agent.response import CodeCompletionResp
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import CommitStatus, KernelId


class ContainerdKernel(AbstractKernel):
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
        raise KernelVerbNotSupported("check_status")

    @override
    async def get_completions(self, text: str, opts: Mapping[str, Any]) -> CodeCompletionResp:
        raise KernelVerbNotSupported("get_completions")

    @override
    async def get_logs(self) -> dict[str, Any]:
        raise KernelVerbNotSupported("get_logs")

    @override
    async def interrupt_kernel(self) -> dict[str, Any]:
        raise KernelVerbNotSupported("interrupt_kernel")

    @override
    async def start_service(self, service: str, opts: Mapping[str, Any]) -> dict[str, Any]:
        raise KernelVerbNotSupported("start_service")

    @override
    async def start_model_service(self, model_service: Mapping[str, Any]) -> dict[str, Any]:
        raise KernelVerbNotSupported("start_model_service")

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

    @override
    async def get_service_apps(self) -> dict[str, Any]:
        raise KernelVerbNotSupported("get_service_apps")

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
