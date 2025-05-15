import asyncio
import os
from typing import Any, FrozenSet, Mapping, override

from ai.backend.agent.backends.code_runner import AbstractCodeRunner, NopCodeRunner
from ai.backend.agent.backends.kernel import AbstractKernel
from ai.backend.agent.types import AgentEventData
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import CommitStatus, KernelId


class DummyKernel(AbstractKernel):
    _is_commiting: bool
    _dummy_kernel_cfg: Mapping[str, Any]

    def __init__(self, dummy_config: Mapping[str, Any]) -> None:
        self._is_commiting = False
        self._dummy_kernel_cfg = dummy_config["kernel"]

    @override
    async def create_code_runner(
        self,
        event_producer: EventProducer,
        *,
        client_features: FrozenSet[str],
        api_version: int,
    ) -> AbstractCodeRunner:
        return NopCodeRunner()

    @override
    async def get_completions(self, text: str, opts: Mapping[str, Any]):
        delay = self._dummy_kernel_cfg["delay"]["get-completions"]
        await asyncio.sleep(delay)
        return {"status": "finished", "completions": []}

    @override
    async def get_logs(self) -> Mapping[str, str]:
        delay = self._dummy_kernel_cfg["delay"]["get-logs"]
        await asyncio.sleep(delay)
        return {"logs": "my logs"}

    @override
    async def interrupt_kernel(self) -> None:
        delay = self._dummy_kernel_cfg["delay"]["interrupt-kernel"]
        await asyncio.sleep(delay)

    @override
    async def start_service(self, service: str, opts: Mapping[str, Any]) -> Mapping[str, Any]:
        delay = self._dummy_kernel_cfg["delay"]["start-service"]
        await asyncio.sleep(delay)
        return {}

    @override
    async def start_model_service(self, model_service: Mapping[str, Any]) -> Mapping[str, Any]:
        delay = self._dummy_kernel_cfg["delay"]["start-model-service"]
        await asyncio.sleep(delay)
        return {}

    @override
    async def shutdown_service(self, service: str) -> None:
        delay = self._dummy_kernel_cfg["delay"]["shutdown-service"]
        await asyncio.sleep(delay)

    @override
    async def check_duplicate_commit(self, kernel_id: KernelId, subdir: str) -> CommitStatus:
        if self._is_commiting:
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
        self._is_commiting = True
        delay = self._dummy_kernel_cfg["delay"]["commit"]
        await asyncio.sleep(delay)
        self._is_commiting = False

    @override
    async def get_service_apps(self):
        delay = self._dummy_kernel_cfg["delay"]["get-service-apps"]
        await asyncio.sleep(delay)
        return {
            "status": "done",
            "data": [],
        }

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
        delay = self._dummy_kernel_cfg["delay"]["accept-file"]
        await asyncio.sleep(delay)

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
        delay = self._dummy_kernel_cfg["delay"]["download-file"]
        await asyncio.sleep(delay)
        return b""

    @override
    async def download_single(self, container_path: os.PathLike | str) -> bytes:
        """
        Download the designated path (a single file) as a tar archive.
        The path should be inside /home/work of the container.
        A relative path is interpreted as a subpath inside /home/work.
        The return value is the content of the file *extracted* from the downloaded archive.

        This API is intended to download a small file from the container filesystem.
        """
        delay = self._dummy_kernel_cfg["delay"]["download-single"]
        await asyncio.sleep(delay)
        return b""

    @override
    async def list_files(self, container_path: os.PathLike | str) -> dict[str, str]:
        """
        List the directory entries of the designated path.
        The path should be inside /home/work of the container.
        A relative path is interpreted as a subpath inside /home/work.
        """
        delay = self._dummy_kernel_cfg["delay"]["list-files"]
        await asyncio.sleep(delay)
        return {"files": "", "errors": "", "abspath": ""}

    @override
    async def notify_event(self, evdata: AgentEventData) -> None:
        pass

    @override
    async def close(self) -> None:
        """
        Release internal resources used for interacting with the kernel.
        Note that this does NOT terminate the container.
        """
        pass
