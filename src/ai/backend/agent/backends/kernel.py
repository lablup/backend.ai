import asyncio
import enum
import logging
import os
from abc import ABC, abstractmethod
from decimal import Decimal
from pathlib import Path
from typing import Any, FrozenSet, Mapping, Optional, Sequence

import zmq

from ai.backend.agent.agent import KernelObjectType
from ai.backend.agent.backends.code_runner import AbstractCodeRunner, NextResult
from ai.backend.agent.resources import AbstractComputePlugin, KernelResourceSpec, Mount
from ai.backend.agent.types import AgentEventData, MountInfo
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.kernel import KernelLifecycleEventReason
from ai.backend.common.types import (
    ClusterInfo,
    CommitStatus,
    DeviceId,
    KernelId,
    MountPermission,
    MountTypes,
    SlotName,
)
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AbstractKernel(ABC):
    @abstractmethod
    async def create_code_runner(
        self,
        event_producer: EventProducer,
        *,
        client_features: FrozenSet[str],
        api_version: int,
    ) -> AbstractCodeRunner:
        raise NotImplementedError

    @abstractmethod
    async def get_completions(self, text: str, opts: Mapping[str, Any]):
        raise NotImplementedError

    @abstractmethod
    async def get_logs(self) -> Mapping[str, str]:
        raise NotImplementedError

    @abstractmethod
    async def interrupt_kernel(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def start_service(self, service: str, opts: Mapping[str, Any]) -> Mapping[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def start_model_service(self, model_service: Mapping[str, Any]) -> Mapping[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def shutdown_service(self, service: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def check_duplicate_commit(self, kernel_id: KernelId, subdir: str) -> CommitStatus:
        raise NotImplementedError

    @abstractmethod
    async def commit(
        self,
        kernel_id,
        subdir,
        *,
        canonical: str | None = None,
        filename: str | None = None,
        extra_labels: dict[str, str] = {},
    ):
        raise NotImplementedError

    @abstractmethod
    async def get_service_apps(self):
        raise NotImplementedError

    @abstractmethod
    async def accept_file(self, container_path: os.PathLike | str, filedata) -> None:
        """
        Put the uploaded file to the designated container path.
        The path should be inside /home/work of the container.
        A relative path is interpreted as a subpath inside /home/work.

        WARNING: Since the implementations may use the scratch directory mounted as the home
        directory inside the container, the file may not be visible inside the container if the
        designated home-relative path overlaps with a vfolder mount.
        """
        raise NotImplementedError

    @abstractmethod
    async def download_file(self, container_path: os.PathLike | str) -> bytes:
        """
        Download the designated path (a single file or an entire directory) as a tar archive.
        The path should be inside /home/work of the container.
        A relative path is interpreted as a subpath inside /home/work.
        The return value is the raw byte stream of the archive itself, and it is the caller's
        responsibility to extract the tar archive.

        This API is intended to download a small set of files from the container filesystem.
        """
        raise NotImplementedError

    @abstractmethod
    async def download_single(self, container_path: os.PathLike | str) -> bytes:
        """
        Download the designated path (a single file) as a tar archive.
        The path should be inside /home/work of the container.
        A relative path is interpreted as a subpath inside /home/work.
        The return value is the content of the file *extracted* from the downloaded archive.

        This API is intended to download a small file from the container filesystem.
        """
        raise NotImplementedError

    @abstractmethod
    async def list_files(self, container_path: os.PathLike | str):
        """
        List the directory entries of the designated path.
        The path should be inside /home/work of the container.
        A relative path is interpreted as a subpath inside /home/work.
        """
        raise NotImplementedError

    @abstractmethod
    async def notify_event(self, evdata: AgentEventData):
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """
        Release internal resources used for interacting with the kernel.
        Note that this does NOT terminate the container.
        """
        pass


class ExecutionMode(enum.StrEnum):
    """
    Execution mode for the kernel.
    """

    BATCH = "batch"
    QUERY = "query"
    INPUT = "input"
    CONTINUE = "continue"


class KernelWrapper:
    _id: KernelId
    _kernel: AbstractKernel
    _code_runner: AbstractCodeRunner
    _tasks: set[asyncio.Task[None]] = set()

    def __init__(self, id: KernelId, kernel: AbstractKernel, runner: AbstractCodeRunner):
        self._id = id
        self._kernel = kernel
        self._code_runner = runner
        self._tasks = set()

    @property
    def id(self) -> KernelId:
        return self._id

    async def ping(self):
        return await self._code_runner.ping()

    def kernel(self) -> AbstractKernel:
        return self._kernel

    async def check_status(self) -> Optional[Mapping[str, float]]:
        return await self._code_runner.feed_and_get_status()

    async def execute(
        self,
        run_id: Optional[str],
        mode: ExecutionMode,
        text: str,
        *,
        opts: Mapping[str, Any],
        api_version: int,
        flush_timeout: float,
    ) -> NextResult:
        myself = asyncio.current_task()
        if myself is None:
            raise RuntimeError("Cannot execute outside of an asyncio task")
        self._tasks.add(myself)
        try:
            await self._code_runner.attach_output_queue(run_id)
            try:
                match mode:
                    case ExecutionMode.BATCH:
                        await self._code_runner.feed_batch(opts)
                    case ExecutionMode.QUERY:
                        await self._code_runner.feed_code(text)
                    case ExecutionMode.INPUT:
                        await self._code_runner.feed_input(text)
                    case ExecutionMode.CONTINUE:
                        pass
            except zmq.ZMQError:
                # cancel the operation by myself
                # since the peer is gone.
                raise asyncio.CancelledError
            return await self._code_runner.get_next_result(
                api_ver=api_version,
                flush_timeout=flush_timeout,
            )
        except asyncio.CancelledError:
            await self._code_runner.close()
            raise
        finally:
            self._tasks.remove(myself)

    async def close(self, reason: KernelLifecycleEventReason) -> None:
        """
        Destroy the kernel and release all resources.
        """
        await self._kernel.close()
        await self._code_runner.close()
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


class AbstractKernelCreationContext(ABC):
    @abstractmethod
    async def prepare_resource_spec(
        self,
    ) -> tuple[KernelResourceSpec, Optional[Mapping[str, Any]]]:
        raise NotImplementedError

    @abstractmethod
    async def prepare_scratch(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_intrinsic_mounts(self) -> Sequence[Mount]:
        raise NotImplementedError

    @property
    @abstractmethod
    def repl_ports(self) -> Sequence[int]:
        """
        Return the list of intrinsic REPL ports to exclude from public mapping.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def protected_services(self) -> Sequence[str]:
        """
        Return the list of protected (intrinsic) service names to exclude from public mapping.
        """
        raise NotImplementedError

    @abstractmethod
    async def apply_network(self, cluster_info: ClusterInfo) -> None:
        """
        Apply the given cluster network information to the deployment.
        """
        raise NotImplementedError

    @abstractmethod
    async def prepare_ssh(self, cluster_info: ClusterInfo) -> None:
        """
        Prepare container to accept SSH connection.
        Install the ssh keypair inside the kernel from cluster_info.
        """
        raise NotImplementedError

    @abstractmethod
    async def process_mounts(self, mounts: Sequence[Mount]):
        raise NotImplementedError

    @abstractmethod
    async def apply_accelerator_allocation(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def generate_accelerator_mounts(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> list[MountInfo]:
        raise NotImplementedError

    @abstractmethod
    def resolve_krunner_filepath(self, filename) -> Path:
        """
        Return matching krunner path object for given filename.
        """
        raise NotImplementedError

    @abstractmethod
    def get_runner_mount(
        self,
        type: MountTypes,
        src: str | Path,
        target: str | Path,
        perm: MountPermission = MountPermission.READ_ONLY,
        opts: Optional[Mapping[str, Any]] = None,
    ):
        """
        Return mount object to mount target krunner file/folder/volume.
        """
        raise NotImplementedError

    @abstractmethod
    async def prepare_container(
        self,
        resource_spec: KernelResourceSpec,
        environ: Mapping[str, str],
        service_ports,
        cluster_info: ClusterInfo,
    ) -> KernelObjectType:
        raise NotImplementedError

    @abstractmethod
    async def start_container(
        self,
        kernel_obj: AbstractKernel,
        cmdargs: list[str],
        resource_opts,
        preopen_ports,
        cluster_info: ClusterInfo,
    ) -> Mapping[str, Any]:
        raise NotImplementedError
