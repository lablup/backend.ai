import os
from typing import Any, FrozenSet, Mapping, override

from ai.backend.agent.backends.code_runner import AbstractCodeRunner
from ai.backend.agent.backends.kernel import AbstractKernel
from ai.backend.agent.types import AgentEventData
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import CommitStatus


class DockerKernel(AbstractKernel):
    @override
    async def create_code_runner(
        self,
        event_producer: EventProducer,
        *,
        client_features: FrozenSet[str],
        api_version: int,
    ) -> AbstractCodeRunner:
        raise NotImplementedError

    @override
    async def check_status(self):
        raise NotImplementedError

    @override
    async def get_completions(self, text: str, opts: Mapping[str, Any]):
        raise NotImplementedError

    @override
    async def get_logs(self) -> dict[str, str]:
        raise NotImplementedError

    @override
    async def interrupt_kernel(self) -> None:
        raise NotImplementedError

    @override
    async def start_service(self, service: str, opts: Mapping[str, Any]) -> Mapping[str, Any]:
        raise NotImplementedError

    @override
    async def start_model_service(self, model_service: Mapping[str, Any]) -> Mapping[str, Any]:
        raise NotImplementedError

    @override
    async def shutdown_service(self, service: str) -> None:
        raise NotImplementedError

    @override
    async def check_duplicate_commit(self, subdir) -> CommitStatus:
        raise NotImplementedError

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
        raise NotImplementedError

    @override
    async def get_service_apps(self):
        raise NotImplementedError

    @override
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

    @override
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

    @override
    async def download_single(self, container_path: os.PathLike | str) -> bytes:
        """
        Download the designated path (a single file) as a tar archive.
        The path should be inside /home/work of the container.
        A relative path is interpreted as a subpath inside /home/work.
        The return value is the content of the file *extracted* from the downloaded archive.

        This API is intended to download a small file from the container filesystem.
        """
        raise NotImplementedError

    @override
    async def list_files(self, container_path: os.PathLike | str):
        """
        List the directory entries of the designated path.
        The path should be inside /home/work of the container.
        A relative path is interpreted as a subpath inside /home/work.
        """
        raise NotImplementedError

    @override
    async def notify_event(self, evdata: AgentEventData):
        raise NotImplementedError

    @override
    async def close(self) -> None:
        """
        Release internal resources used for interacting with the kernel.
        Note that this does NOT terminate the container.
        """
        pass
