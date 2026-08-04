import os
from collections.abc import Mapping
from typing import Any, override

from ai.backend.agent.kernel import AbstractCodeRunner, AbstractKernel
from ai.backend.agent.resources import KernelResourceSpec
from ai.backend.agent.types import AgentEventData, KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.dto.agent.response import CodeCompletionResp
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.kernel_runner import RunnerVerb
from ai.backend.common.types import CommitStatus, KernelId

from .errors import (
    ChannelTerminatedVerbRefused,
    HostFileTransferRefused,
    HostLogReadRefused,
    SessionCommitRefused,
)


def _off_the_agent(verb: RunnerVerb) -> ChannelTerminatedVerbRefused:
    return ChannelTerminatedVerbRefused(
        extra_msg=f"{verb.value} is spoken over the guest-terminated channel, not by the agent"
    )


class CocoKernel(AbstractKernel):
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
            environ=environ,
            data=data,
        )

    @property
    @override
    def channel_terminated(self) -> bool:
        return True

    @override
    async def close(self) -> None:
        pass

    @override
    async def create_code_runner(
        self, event_producer: EventProducer, *, client_features: frozenset[str], api_version: int
    ) -> AbstractCodeRunner:
        raise ChannelTerminatedVerbRefused(
            extra_msg="the agent host holds no session channel key and cannot dial the runner"
        )

    @override
    async def check_status(self) -> dict[str, Any] | None:
        raise _off_the_agent(RunnerVerb.STATUS)

    @override
    async def get_completions(self, text: str, opts: Mapping[str, Any]) -> CodeCompletionResp:
        raise _off_the_agent(RunnerVerb.COMPLETE)

    @override
    async def interrupt_kernel(self) -> dict[str, Any]:
        raise _off_the_agent(RunnerVerb.INTERRUPT)

    @override
    async def start_service(self, service: str, opts: Mapping[str, Any]) -> dict[str, Any]:
        raise _off_the_agent(RunnerVerb.START_SERVICE)

    @override
    async def start_model_service(self, model_service: Mapping[str, Any]) -> dict[str, Any]:
        raise _off_the_agent(RunnerVerb.START_MODEL_SERVICE)

    @override
    async def shutdown_service(self, service: str) -> None:
        raise _off_the_agent(RunnerVerb.SHUTDOWN_SERVICE)

    @override
    async def get_service_apps(self) -> dict[str, Any]:
        raise _off_the_agent(RunnerVerb.GET_APPS)

    @override
    async def notify_event(self, evdata: AgentEventData) -> None:
        raise _off_the_agent(RunnerVerb.EVENT)

    @override
    async def get_logs(self) -> dict[str, Any]:
        raise HostLogReadRefused(extra_msg=str(self.kernel_id))

    @override
    async def check_duplicate_commit(self, kernel_id: KernelId, subdir: str) -> CommitStatus:
        raise SessionCommitRefused(extra_msg=str(kernel_id))

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
        raise SessionCommitRefused(extra_msg=str(kernel_id))

    @override
    async def accept_file(self, container_path: os.PathLike[str] | str, filedata: bytes) -> None:
        raise HostFileTransferRefused(extra_msg=str(container_path))

    @override
    async def download_file(self, container_path: os.PathLike[str] | str) -> bytes:
        raise HostFileTransferRefused(extra_msg=str(container_path))

    @override
    async def download_single(self, container_path: os.PathLike[str] | str) -> bytes:
        raise HostFileTransferRefused(extra_msg=str(container_path))

    @override
    async def list_files(self, container_path: os.PathLike[str] | str) -> dict[str, Any]:
        raise HostFileTransferRefused(extra_msg=str(container_path))
