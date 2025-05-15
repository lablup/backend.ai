import os
from pathlib import Path
from typing import Any, FrozenSet, Mapping, override

from aiodocker import Docker
from aiotools import closing_async

from ai.backend.agent.backends.code_runner import AbstractCodeRunner
from ai.backend.agent.backends.kernel import AbstractKernel
from ai.backend.agent.types import AgentEventData
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import CommitStatus, KernelId


# With Runner Operation and With container operation
class DockerKernel(AbstractKernel):
    _local_config: Mapping[str, Any]
    _container_id: str

    def __init__(self, container_id: str) -> None:
        """
        Initialize the Docker kernel with the provided container ID.
        """
        self._container_id = container_id

    @override
    async def create_code_runner(
        self,
        event_producer: EventProducer,
        *,
        client_features: FrozenSet[str],
        api_version: int,
    ) -> AbstractCodeRunner:
        # TODO: Implement this method at KernelWrapper level (Runner)
        raise NotImplementedError

    @override
    async def get_completions(self, text: str, opts: Mapping[str, Any]) -> Mapping[str, Any]:
        # TODO: Implement this method at KernelWrapper level (Runner)
        raise NotImplementedError

    @override
    async def get_logs(self) -> Mapping[str, str]:
        async with closing_async(Docker()) as docker:
            container = await docker.containers.get(self._container_id)
            logs = await container.log(stdout=True, stderr=True, follow=False)
        return {"logs": "".join(logs)}

    @override
    async def interrupt_kernel(self) -> None:
        # TODO: Implement this method at KernelWrapper level (Runner)
        raise NotImplementedError

    @override
    async def start_service(self, service: str, opts: Mapping[str, Any]) -> Mapping[str, Any]:
        # TODO: Implement this method at KernelWrapper level (Runner)
        raise NotImplementedError

    @override
    async def start_model_service(self, model_service: Mapping[str, Any]) -> Mapping[str, Any]:
        # TODO: Implement this method at KernelWrapper level (Runner)
        raise NotImplementedError

    @override
    async def shutdown_service(self, service: str) -> None:
        # TODO: Implement this method at KernelWrapper level (Runner)
        raise NotImplementedError

    @override
    async def check_duplicate_commit(self, kernel_id: KernelId, subdir: str) -> CommitStatus:
        _, lock_path = self._get_commit_path(kernel_id, subdir)
        if lock_path.exists():
            return CommitStatus.ONGOING
        return CommitStatus.READY

    @override
    async def commit(
        self,
        kernel_id,
        subdir,
        *,
        canonical: str | None = None,
        filename: str | None = None,
        extra_labels: dict[str, str] = {},
    ):
        # TODO: Implement this method at KernelWrapper level (Image)
        raise NotImplementedError

    @override
    async def get_service_apps(self):
        # TODO: Implement this method at KernelWrapper level (Runner)
        raise NotImplementedError

    @override
    async def accept_file(self, container_path: os.PathLike | str, filedata) -> None:
        # TODO: Implement this method at KernelWrapper level (container)
        raise NotImplementedError

    @override
    async def download_file(self, container_path: os.PathLike | str) -> bytes:
        # TODO: Implement this method at KernelWrapper level (container)
        raise NotImplementedError

    @override
    async def download_single(self, container_path: os.PathLike | str) -> bytes:
        """
        Download the designated path (a single file) as a tar archive.
        The path should be inside /home/work of the container.
        A relative path is interpreted as a subpath inside /home/work.
        The return value is the content of the file *extracted* from the downloaded archive.

        This API is intended to download a small file from the container filesystem.
        """
        # TODO: Implement this method at KernelWrapper level (container)
        raise NotImplementedError

    @override
    async def list_files(self, container_path: os.PathLike | str):
        """
        List the directory entries of the designated path.
        The path should be inside /home/work of the container.
        A relative path is interpreted as a subpath inside /home/work.
        """
        # TODO: Implement this method at KernelWrapper level (container)
        raise NotImplementedError

    @override
    async def notify_event(self, evdata: AgentEventData):
        # TODO: Implement this method at KernelWrapper level (Runner)
        raise NotImplementedError

    @override
    async def close(self) -> None:
        """
        Release internal resources used for interacting with the kernel.
        Note that this does NOT terminate the container.
        """
        pass

    def _get_commit_path(self, kernel_id: KernelId, subdir: str) -> tuple[Path, Path]:
        base_commit_path: Path = self._local_config["agent"]["image-commit-path"]
        commit_path = base_commit_path / subdir
        lock_path = commit_path / "lock" / str(kernel_id)
        return commit_path, lock_path
