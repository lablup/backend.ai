import asyncio
from dataclasses import dataclass
import enum
import logging
import os
from abc import ABC, abstractmethod
from decimal import Decimal
from pathlib import Path
from typing import Any, FrozenSet, Literal, Mapping, Optional, Sequence

import zmq

from ai.backend.agent.agent import KernelObjectType
from ai.backend.agent.kernel import AbstractCodeRunner, NextResult
from ai.backend.agent.resources import AbstractComputePlugin, KernelResourceSpec, Mount
from ai.backend.agent.types import AgentEventData, KernelOwnershipData, MountInfo
from ai.backend.common.docker import ImageRef
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import (
    ClusterInfo,
    ClusterSSHPortMapping,
    CommitStatus,
    ContainerId,
    DeviceId,
    KernelCreationConfig,
    KernelId,
    MountPermission,
    MountTypes,
    SlotName,
)
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

@dataclass
class StartServiceResult:
    ...


@dataclass
class StartModelServiceResult:
    ...

       
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
    async def check_status(self):
        raise NotImplementedError

    @abstractmethod
    async def get_completions(self, text: str, opts: Mapping[str, Any]):
        raise NotImplementedError

    @abstractmethod
    async def get_logs(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def interrupt_kernel(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def start_service(self, service: str, opts: Mapping[str, Any]) -> StartServiceResult:
        raise NotImplementedError

    @abstractmethod
    async def start_model_service(self, model_service: Mapping[str, Any]) -> StartModelServiceResult:
        raise NotImplementedError

    @abstractmethod
    async def shutdown_service(self, service: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def check_duplicate_commit(self, subdir) -> CommitStatus:
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
    _kernel: AbstractKernel
    _runner: AbstractCodeRunner
    _tasks: set[asyncio.Task[None]] = set()

    def __init__(self, kernel: AbstractKernel, runner: AbstractCodeRunner):
        self._kernel = kernel
        self._runner = runner
        self._tasks = set()

    
    async def ping(self):
        return await self._runner.ping()
    
    def kernel(self) -> AbstractKernel:
        return self._kernel

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
            await self._runner.attach_output_queue(run_id)
            try:
                match mode:
                    case ExecutionMode.BATCH:
                        await self._runner.feed_batch(opts)
                    case ExecutionMode.QUERY:
                        await self._runner.feed_code(text)
                    case ExecutionMode.INPUT:
                        await self._runner.feed_input(text)
                    case ExecutionMode.CONTINUE:
                        pass
            except zmq.ZMQError:
                # cancel the operation by myself
                # since the peer is gone.
                raise asyncio.CancelledError
            return await self._runner.get_next_result(
                api_ver=api_version,
                flush_timeout=flush_timeout,
            )
        except asyncio.CancelledError:
            await self._runner.close()
            raise
        finally:
            self._tasks.remove(myself)

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


class AbstractKernelFactory(ABC):
    @abstractmethod
    async def init_kernel_context(
        self,
        ownership_data: KernelOwnershipData,
        kernel_image: ImageRef,
        kernel_config: KernelCreationConfig,
        *,
        restarting: bool = False,
        cluster_ssh_port_mapping: Optional[ClusterSSHPortMapping] = None,
    ) -> AbstractKernelCreationContext:
        raise NotImplementedError

    @abstractmethod
    async def destroy_kernel(
        self,
        kernel_id: KernelId,
        container_id: Optional[ContainerId],
    ) -> None:
        """
        Initiate destruction of the kernel.

        Things to do:
        * Send SIGTERM to the kernel's main process.
        * Send SIGKILL if it's not terminated within a few seconds.
        """

    @abstractmethod
    async def clean_kernel(
        self,
        kernel_id: KernelId,
        container_id: Optional[ContainerId],
        restarting: bool,
    ) -> None:
        """
        Clean up kernel-related book-keepers when the underlying
        implementation detects an event that the kernel has terminated.

        Things to do:
        * Call :meth:`self.collect_logs()` to store the container's console outputs.
        * Delete the underlying kernel resource (e.g., container)
        * Release host-specific resources used for the kernel (e.g., scratch spaces)

        This method is intended to be called asynchronously by the implementation-specific
        event monitoring routine.

        The ``container_id`` may be ``None`` if the container has already gone away.
        In such cases, skip container-specific cleanups.
        """
