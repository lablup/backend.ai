import asyncio
import logging
from asyncio import subprocess
from typing import Any, override

from yarl import URL

from ai.backend.appproxy.common.errors import ServerMisconfiguredError
from ai.backend.appproxy.common.types import RouteInfo
from ai.backend.appproxy.worker.errors import InvalidFrontendTypeError, SubprocessPipeError
from ai.backend.appproxy.worker.proxy.backend.h2 import H2Backend
from ai.backend.appproxy.worker.types import Circuit, PortFrontendInfo
from ai.backend.logging.structured import StructuredLogger

from .base import H2Frontend

log = StructuredLogger(logging.getLogger(__spec__.name))


class PortFrontend(H2Frontend[int]):
    processes: list[subprocess.Process]
    healthy: bool
    proc_monitor_tasks: list[asyncio.Task[Any]] = []
    log_monitor_tasks: list[asyncio.Task[Any]] = []

    api_ports: dict[int, int]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.api_endpoint = None
        self.processes = []
        port_proxy_config = self.root_context.local_config.proxy_worker.port_proxy
        if not port_proxy_config:
            raise ServerMisconfiguredError("worker:proxy-worker.port-proxy")
        port_start, port_end = port_proxy_config.bind_port_range
        self.api_ports = {
            listen_port: self.api_port_pool.pop() for listen_port in range(port_start, port_end + 1)
        }

    @override
    async def start(self) -> None:
        worker_config = self.root_context.local_config.proxy_worker
        port_proxy_config = worker_config.port_proxy
        h2_config = worker_config.http2
        if not port_proxy_config:
            raise ServerMisconfiguredError("worker:proxy-worker.port-proxy")
        if not h2_config:
            raise ServerMisconfiguredError("worker:proxy-worker.http2")

        for listen_port, api_port in self.api_ports.items():
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
            log.info(
                "started the nghttpx server",
                bind_host=port_proxy_config.bind_host,
                port=listen_port,
            )
        self._nghttpx_running = True
        await self._send_registered_backend_routes()

    @override
    async def stop(self) -> None:
        self._nghttpx_running = False
        for task in self.proc_monitor_tasks:
            task.cancel()
            await task
        for process in self.processes:
            process.terminate()
            await process.wait()
        for task in self.log_monitor_tasks:
            task.cancel()
            await task

    @override
    async def initialize_backend(self, circuit: Circuit, routes: list[RouteInfo]) -> H2Backend:
        api_port = self.api_ports[self.get_circuit_key(circuit)]
        backend = H2Backend(URL(f"http://localhost:{api_port}"), self.root_context, circuit)
        return await self.update_backend(backend, routes)

    @override
    def get_circuit_key(self, circuit: Circuit) -> int:
        if not isinstance(circuit.frontend, PortFrontendInfo):
            raise InvalidFrontendTypeError(
                f"Expected PortFrontendInfo, got {type(circuit.frontend).__name__}"
            )
        return circuit.frontend.port
