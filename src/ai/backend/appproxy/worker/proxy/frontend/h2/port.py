import asyncio
import logging
from asyncio import subprocess

from yarl import URL

from ai.backend.appproxy.common.exceptions import ServerMisconfiguredError
from ai.backend.appproxy.common.types import RouteInfo
from ai.backend.appproxy.worker.proxy.backend.h2 import BackendConfig, H2Backend
from ai.backend.appproxy.worker.types import Circuit, PortFrontendInfo
from ai.backend.logging import BraceStyleAdapter

from .base import H2Frontend

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class PortFrontend(H2Frontend[int]):
    processes: list[subprocess.Process]
    healthy: bool
    proc_monitor_tasks: list[asyncio.Task] = []
    log_monitor_tasks: list[asyncio.Task] = []

    api_ports: dict[int, int]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.api_endpoint = None
        self.processes = []
        self.api_ports = {}

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
            assert proc.stdout and proc.stderr
            self.processes.append(proc)
            self.log_monitor_tasks.append(
                asyncio.create_task(self._log_monitor_task(proc.stdout, f"stdout #{listen_port}"))
            )
            self.log_monitor_tasks.append(
                asyncio.create_task(self._log_monitor_task(proc.stderr, f"stderr #{listen_port}"))
            )
            self.proc_monitor_tasks.append(asyncio.create_task(self._proc_monitor_task(proc)))
            self.api_ports[listen_port] = api_port
            log.info("started nghttpx server at {}:{}", port_proxy_config.bind_host, listen_port)

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

    async def initialize_backend(self, circuit: Circuit, routes: list[RouteInfo]) -> H2Backend:
        api_port = self.api_ports[self.get_circuit_key(circuit)]
        backend = H2Backend(URL(f"http://localhost:{api_port}"), self.root_context, circuit)
        return await self.update_backend(backend, routes)

    async def update_backend(self, backend: H2Backend, routes: list[RouteInfo]) -> H2Backend:
        backend_configs = [BackendConfig(r.current_kernel_host, r.kernel_port) for r in routes]
        await backend.update_config(backend_configs)
        return backend

    async def terminate_backend(self, backend: H2Backend) -> None:
        await backend.update_config([])

    def get_circuit_key(self, circuit: Circuit) -> int:
        assert isinstance(circuit.frontend, PortFrontendInfo)
        return circuit.frontend.port
