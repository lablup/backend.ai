import asyncio
from typing import Any, Dict, FrozenSet, Mapping, Sequence

from ai.backend.common.docker import ImageRef
from ai.backend.common.types import AgentId, CommitStatus, KernelId, SessionId

from ..kernel import AbstractCodeRunner, AbstractKernel
from ..resources import KernelResourceSpec


class DummyKernel(AbstractKernel):
    dummy_config: Mapping[str, Any]

    def __init__(
        self,
        kernel_id: KernelId,
        session_id: SessionId,
        agent_id: AgentId,
        image: ImageRef,
        version: int,
        *,
        agent_config: Mapping[str, Any],
        resource_spec: KernelResourceSpec,
        service_ports: Any,  # TODO: type-annotation
        environ: Mapping[str, Any],
        data: Dict[str, Any],
        dummy_config: Mapping[str, Any],
    ) -> None:
        super().__init__(
            kernel_id,
            session_id,
            agent_id,
            image,
            version,
            agent_config=agent_config,
            resource_spec=resource_spec,
            service_ports=service_ports,
            data=data,
            environ=environ,
        )
        self.is_commiting = False
        self.dummy_config = dummy_config
        self.dummy_kernel_cfg = self.dummy_config["kernel"]

    async def close(self) -> None:
        pass

    async def create_code_runner(
        self,
        *,
        client_features: FrozenSet[str],
        api_version: int,
    ) -> "AbstractCodeRunner":
        return await DummyCodeRunner.new(
            self.kernel_id,
            kernel_host=self.data["kernel_host"],
            repl_in_port=self.data["repl_in_port"],
            repl_out_port=self.data["repl_out_port"],
            exec_timeout=0,
            client_features=client_features,
        )

    async def check_status(self):
        await asyncio.sleep(self.dummy_kernel_cfg["delay"]["check-status"])
        return {}

    async def get_completions(self, text, opts):
        await asyncio.sleep(self.dummy_kernel_cfg["delay"]["get-completions"])
        return {"status": "finished", "completions": []}

    async def get_logs(self):
        await asyncio.sleep(self.dummy_kernel_cfg["delay"]["get-logs"])
        return {"logs": "my logs"}

    async def interrupt_kernel(self):
        await asyncio.sleep(self.dummy_kernel_cfg["delay"]["interrupt-kernel"])

    async def start_service(self, service, opts):
        await asyncio.sleep(self.dummy_kernel_cfg["delay"]["start-service"])

    async def start_model_service(self, model_service: Mapping[str, Any]):
        await asyncio.sleep(self.dummy_kernel_cfg["delay"]["start-model-service"])
        return {}

    async def shutdown_service(self, service):
        await asyncio.sleep(self.dummy_kernel_cfg["delay"]["shutdown-service"])

    async def check_duplicate_commit(self, kernel_id, subdir) -> CommitStatus:
        if self.is_commiting:
            return CommitStatus.ONGOING
        return CommitStatus.READY

    async def commit(self, kernel_id, subdir, filename):
        self.is_commiting = True
        await asyncio.sleep(self.dummy_kernel_cfg["delay"]["commit"])
        self.is_commiting = False

    async def get_service_apps(self):
        await asyncio.sleep(self.dummy_kernel_cfg["delay"]["get-service-apps"])
        return {
            "status": "done",
            "data": [],
        }

    async def accept_file(self, filename, filedata):
        await asyncio.sleep(self.dummy_kernel_cfg["delay"]["accept-file"])

    async def download_file(self, filepath):
        await asyncio.sleep(self.dummy_kernel_cfg["delay"]["download-file"])
        return b""

    async def download_single(self, filepath):
        await asyncio.sleep(self.dummy_kernel_cfg["delay"]["download-single"])
        return b""

    async def list_files(self, path: str):
        await asyncio.sleep(self.dummy_kernel_cfg["delay"]["list-files"])
        return {"files": "", "errors": "", "abspath": ""}


class DummyCodeRunner(AbstractCodeRunner):
    kernel_host: str
    repl_in_port: int
    repl_out_port: int

    def __init__(
        self,
        kernel_id,
        *,
        kernel_host,
        repl_in_port,
        repl_out_port,
        exec_timeout=0,
        client_features=None,
    ) -> None:
        super().__init__(kernel_id, exec_timeout=exec_timeout, client_features=client_features)
        self.kernel_host = kernel_host
        self.repl_in_port = repl_in_port
        self.repl_out_port = repl_out_port

    async def get_repl_in_addr(self) -> str:
        return f"tcp://{self.kernel_host}:{self.repl_in_port}"

    async def get_repl_out_addr(self) -> str:
        return f"tcp://{self.kernel_host}:{self.repl_out_port}"


async def prepare_krunner_env(local_config: Mapping[str, Any]) -> Mapping[str, Sequence[str]]:
    return {}
