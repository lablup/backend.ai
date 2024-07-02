from __future__ import annotations

import asyncio
import os
from collections import OrderedDict
from typing import Any, Dict, FrozenSet, Mapping, Sequence, override

from ai.backend.common.docker import ImageRef
from ai.backend.common.events import EventProducer
from ai.backend.common.types import AgentId, CommitStatus, KernelId, SessionId

from ..kernel import AbstractCodeRunner, AbstractKernel, NextResult, ResultRecord
from ..resources import KernelResourceSpec
from ..types import AgentEventData


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
        event_producer: EventProducer,
        *,
        client_features: FrozenSet[str],
        api_version: int,
    ) -> "AbstractCodeRunner":
        if self.dummy_kernel_cfg["use-fake-code-runner"]:
            return await DummyFakeCodeRunner.new(
                self.kernel_id,
                self.session_id,
                event_producer,
                kernel_host=self.data["kernel_host"],
                repl_in_port=self.data["repl_in_port"],
                repl_out_port=self.data["repl_out_port"],
                exec_timeout=0,
                client_features=client_features,
            )
        else:
            return await DummyCodeRunner.new(
                self.kernel_id,
                self.session_id,
                event_producer,
                kernel_host=self.data["kernel_host"],
                repl_in_port=self.data["repl_in_port"],
                repl_out_port=self.data["repl_out_port"],
                exec_timeout=0,
                client_features=client_features,
            )

    async def check_status(self):
        delay = self.dummy_kernel_cfg["delay"]["check-status"]
        await asyncio.sleep(delay)
        return {}

    async def get_completions(self, text, opts):
        delay = self.dummy_kernel_cfg["delay"]["get-completions"]
        await asyncio.sleep(delay)
        return {"status": "finished", "completions": []}

    async def get_logs(self):
        delay = self.dummy_kernel_cfg["delay"]["get-logs"]
        await asyncio.sleep(delay)
        return {"logs": "my logs"}

    async def interrupt_kernel(self):
        delay = self.dummy_kernel_cfg["delay"]["interrupt-kernel"]
        await asyncio.sleep(delay)

    async def start_service(self, service, opts):
        delay = self.dummy_kernel_cfg["delay"]["start-service"]
        await asyncio.sleep(delay)

    async def start_model_service(self, model_service: Mapping[str, Any]):
        delay = self.dummy_kernel_cfg["delay"]["start-model-service"]
        await asyncio.sleep(delay)
        return {}

    async def shutdown_service(self, service):
        delay = self.dummy_kernel_cfg["delay"]["shutdown-service"]
        await asyncio.sleep(delay)

    async def check_duplicate_commit(self, kernel_id, subdir) -> CommitStatus:
        if self.is_commiting:
            return CommitStatus.ONGOING
        return CommitStatus.READY

    async def commit(
        self,
        kernel_id,
        subdir,
        *,
        canonical: str | None = None,
        filename: str | None = None,
        extra_labels: dict[str, str] = {},
    ) -> None:
        self.is_commiting = True
        delay = self.dummy_kernel_cfg["delay"]["commit"]
        await asyncio.sleep(delay)
        self.is_commiting = False

    async def get_service_apps(self):
        delay = self.dummy_kernel_cfg["delay"]["get-service-apps"]
        await asyncio.sleep(delay)
        return {
            "status": "done",
            "data": [],
        }

    @override
    async def accept_file(self, container_path: os.PathLike | str, filedata: bytes) -> None:
        delay = self.dummy_kernel_cfg["delay"]["accept-file"]
        await asyncio.sleep(delay)

    @override
    async def download_file(self, container_path: os.PathLike | str) -> bytes:
        delay = self.dummy_kernel_cfg["delay"]["download-file"]
        await asyncio.sleep(delay)
        return b""

    @override
    async def download_single(self, container_path: os.PathLike | str) -> bytes:
        delay = self.dummy_kernel_cfg["delay"]["download-single"]
        await asyncio.sleep(delay)
        return b""

    @override
    async def list_files(self, container_path: os.PathLike | str):
        delay = self.dummy_kernel_cfg["delay"]["list-files"]
        await asyncio.sleep(delay)
        return {"files": "", "errors": "", "abspath": ""}

    async def notify_event(self, evdata: AgentEventData):
        raise NotImplementedError


class DummyCodeRunner(AbstractCodeRunner):
    kernel_host: str
    repl_in_port: int
    repl_out_port: int

    def __init__(
        self,
        kernel_id,
        session_id,
        event_producer,
        *,
        kernel_host,
        repl_in_port,
        repl_out_port,
        exec_timeout=0,
        client_features=None,
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

    async def get_repl_in_addr(self) -> str:
        return f"tcp://{self.kernel_host}:{self.repl_in_port}"

    async def get_repl_out_addr(self) -> str:
        return f"tcp://{self.kernel_host}:{self.repl_out_port}"


class DummyFakeCodeRunner(AbstractCodeRunner):
    kernel_host: str
    repl_in_port: int
    repl_out_port: int

    input_sock: None  # type: ignore[assignment]
    output_sock: None  # type: ignore[assignment]
    zctx: None  # type: ignore[assignment]

    def __init__(
        self,
        kernel_id,
        session_id,
        event_producer,
        *,
        kernel_host,
        repl_in_port,
        repl_out_port,
        exec_timeout=0,
        client_features=None,
    ) -> None:
        self.zctx = None
        self.input_sock = None
        self.output_sock = None

        self.completion_queue = asyncio.Queue(maxsize=128)
        self.service_queue = asyncio.Queue(maxsize=128)
        self.model_service_queue = asyncio.Queue(maxsize=128)
        self.service_apps_info_queue = asyncio.Queue(maxsize=128)
        self.status_queue = asyncio.Queue(maxsize=128)
        self.output_queue = None
        self.pending_queues = OrderedDict()
        self.current_run_id = None
        self.read_task = None
        self.status_task = None
        self.watchdog_task = None
        self._closed = False

        self.kernel_host = kernel_host
        self.repl_in_port = repl_in_port
        self.repl_out_port = repl_out_port

        self.event_producer = event_producer

    async def __ainit__(self) -> None:
        return

    def __setstate__(self, props):
        self.__dict__.update(props)
        self.zctx = None
        self.input_sock = None
        self.output_sock = None

        self.completion_queue = asyncio.Queue(maxsize=128)
        self.service_queue = asyncio.Queue(maxsize=128)
        self.model_service_queue = asyncio.Queue(maxsize=128)
        self.service_apps_info_queue = asyncio.Queue(maxsize=128)
        self.status_queue = asyncio.Queue(maxsize=128)
        self.output_queue = None
        self.pending_queues = OrderedDict()
        self.current_run_id = None
        self.read_task = None
        self.status_task = None
        self.watchdog_task = None
        self._closed = False

    async def get_repl_in_addr(self) -> str:
        return f"tcp://{self.kernel_host}:{self.repl_in_port}"

    async def get_repl_out_addr(self) -> str:
        return f"tcp://{self.kernel_host}:{self.repl_out_port}"

    async def close(self) -> None:
        return None

    async def ping_status(self):
        return None

    async def feed_batch(self, opts):
        return None

    async def feed_code(self, text: str):
        return None

    async def feed_input(self, text: str):
        return None

    async def feed_interrupt(self):
        return None

    async def feed_and_get_status(self):
        return None

    async def feed_and_get_completion(self, code_text, opts):
        return []

    async def feed_start_model_service(self, model_info):
        return {"status": "failed", "error": "not-implemented"}

    async def feed_start_service(self, service_info):
        return {"status": "failed", "error": "not-implemented"}

    async def feed_service_apps(self):
        return {"status": "failed", "error": "not-implemented"}

    @staticmethod
    def aggregate_console(
        result: NextResult, records: Sequence[ResultRecord], api_ver: int
    ) -> None:
        return

    async def get_next_result(self, api_ver=2, flush_timeout=2.0) -> NextResult:
        return {}

    async def attach_output_queue(self, run_id: str | None) -> None:
        return

    def resume_output_queue(self) -> None:
        return

    def next_output_queue(self) -> None:
        return

    async def read_output(self) -> None:
        return


async def prepare_krunner_env(local_config: Mapping[str, Any]) -> Mapping[str, Sequence[str]]:
    return {}
