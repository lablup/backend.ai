from __future__ import annotations

import asyncio
import contextlib
import os
from collections.abc import Mapping
from typing import Any, Final, override

from tenacity import TryAgain

from ai.backend.agent.containerd.profile.base import LaunchPlan
from ai.backend.agent.errors.containerd import ContainerdOperationFailed, KernelVerbNotSupported
from ai.backend.agent.kernel import AbstractCodeRunner, AbstractKernel
from ai.backend.agent.resources import KernelResourceSpec
from ai.backend.agent.types import AgentEventData, KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.dto.agent.response import CodeCompletionResp
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import CommitStatus, KernelId

_PROBE_HOST: Final = "127.0.0.1"
_PROBE_TIMEOUT_SEC: Final = 2.0


class ContainerdKernel(AbstractKernel):
    launch_plan: LaunchPlan

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
    # The runc readiness probe: the kernel runner listens on its REPL port once it is up.
    # TryAgain makes the create_kernel readiness loop retry.
    @override
    async def check_status(self) -> dict[str, Any] | None:
        ports = self.data.get("intrinsic_ports")
        if not ports:
            raise ContainerdOperationFailed("the kernel data has no REPL ports")
        try:
            async with asyncio.timeout(_PROBE_TIMEOUT_SEC):
                _, writer = await asyncio.open_connection(_PROBE_HOST, int(ports["replin"]))
        except (OSError, TimeoutError) as e:
            raise TryAgain from e
        writer.close()
        with contextlib.suppress(OSError):
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
