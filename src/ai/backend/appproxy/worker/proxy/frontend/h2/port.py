import asyncio
import logging
from asyncio import subprocess
from typing import Any, override

from yarl import URL

from ai.backend.appproxy.common.errors import ServerMisconfiguredError
from ai.backend.appproxy.worker.errors import InvalidFrontendTypeError, SubprocessPipeError
from ai.backend.appproxy.worker.proxy.backend.h2 import H2Backend, H2BackendArgs
from ai.backend.appproxy.worker.types import Circuit
from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress
from ai.backend.logging.structured import StructuredLogger

from .base import H2Frontend

log = StructuredLogger(logging.getLogger(__spec__.name))


class PortFrontend(H2Frontend):
    processes: list[subprocess.Process]
    healthy: bool
    proc_monitor_tasks: list[asyncio.Task[Any]] = []
    log_monitor_tasks: list[asyncio.Task[Any]] = []

    api_ports: dict[int, int]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.api_endpoint = None
        self.processes = []
        self.api_ports = {}

    @override
    async def start(self) -> None:
        worker_config = self.root_context.local_config.proxy_worker
        port_proxy_config = worker_config.port_proxy
        h2_config = worker_config.http2
        if not port_proxy_config:
            raise ServerMisconfiguredError("worker:proxy-worker.port-proxy")
        if not h2_config:
            raise ServerMisconfiguredError("worker:proxy-worker.http2")

        port_start, port_end = port_proxy_config.bind_port_range
        for listen_port in range(port_start, port_end + 1):
            api_port = self.api_port_pool.pop()
            nghttpx_args = ["-s", f"--frontend=127.0.0.1,{api_port};api"]
            if worker_config.tls_listen:
                nghttpx_args += [
                    f"--frontend={port_proxy_config.bind_host},{listen_port}",
                    str(worker_config.tls_cert),
                    str(worker_config.tls_privkey),
                ]
            else:
                nghttpx_args.append(f"--frontend=*,{listen_port};no-tls")

            proc = await subprocess.create_subprocess_exec(
                h2_config.nghttpx_path,
                *nghttpx_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if not proc.stdout or not proc.stderr:
                raise SubprocessPipeError("Subprocess stdout or stderr is not available")
            self.processes.append(proc)
            self.log_monitor_tasks.append(
                asyncio.create_task(self._log_monitor_task(proc.stdout, f"stdout #{listen_port}"))
            )
            self.log_monitor_tasks.append(
                asyncio.create_task(self._log_monitor_task(proc.stderr, f"stderr #{listen_port}"))
            )
            self.proc_monitor_tasks.append(asyncio.create_task(self._proc_monitor_task(proc)))
            self.api_ports[listen_port] = api_port
            log.info(
                "started the nghttpx server",
                bind_host=port_proxy_config.bind_host,
                port=listen_port,
            )

    @override
    async def stop(self) -> None:
        for task in self.proc_monitor_tasks:
            task.cancel()
            await task
        for process in self.processes:
            process.terminate()
            await process.wait()
        try:
            for task in self.log_monitor_tasks:
                task.cancel()
                await task
        finally:
            self.api_ports = {}

    @override
    async def initialize_backend(
        self, ingress: Ingress, circuit: Circuit | None = None
    ) -> H2Backend:
        if ingress.frontend.port is None:
            raise InvalidFrontendTypeError(f"Expected a port frontend, got {ingress.frontend.kind}")
        api_port = self.api_ports[ingress.frontend.port.number]
        backend = H2Backend(
            H2BackendArgs(
                last_used_time_mark_queue=self.root_context.last_used_time_mark_queue,
                request_counter_key_queue=self.root_context.request_counter_key_queue,
                ingress=ingress,
                circuit=circuit,
                api_endpoint=URL(f"http://localhost:{api_port}"),
            )
        )
        await backend.update_ingress(ingress)
        return backend

    @override
    async def terminate_backend(self, backend: H2Backend) -> None:
        await backend.update_config([])
