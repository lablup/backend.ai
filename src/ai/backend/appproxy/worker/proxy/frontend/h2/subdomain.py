import asyncio
import logging
from asyncio import subprocess

from yarl import URL

from ai.backend.appproxy.common.exceptions import ServerMisconfiguredError
from ai.backend.appproxy.common.types import RouteInfo
from ai.backend.appproxy.worker.proxy.backend.h2 import BackendConfig, H2Backend
from ai.backend.appproxy.worker.types import Circuit, SubdomainFrontendInfo
from ai.backend.logging import BraceStyleAdapter

from .base import H2Frontend

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class SubdomainFrontend(H2Frontend[str]):
    process: subprocess.Process | None
    log_monitor_tasks: list[asyncio.Task]
    proc_monitor_task: asyncio.Task | None

    api_port: int | None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.process = None
        self.log_monitor_tasks = []
        self.proc_monitor_task = None

    async def start(self) -> None:
        self.api_port = self.api_port_pool.pop()
        worker_config = self.root_context.local_config.proxy_worker
        wildcard_domain_config = worker_config.wildcard_domain
        if not wildcard_domain_config:
            raise ServerMisconfiguredError("worker:proxy-worker.wildcard-domain")

        service_addr = wildcard_domain_config.bind_addr
        nghttpx_args = ["-s", f"--frontend=127.0.0.1,{self.api_port};api"]
        if worker_config.tls_listen:
            nghttpx_args += [
                f"--frontend={service_addr.host},{service_addr.port}",
                str(worker_config.tls_cert),
                str(worker_config.tls_privkey),
            ]
        else:
            nghttpx_args.append(f"--frontend={service_addr.host},{service_addr.port};no-tls")

        if not self.root_context.local_config.proxy_worker.http2:
            raise ServerMisconfiguredError("worker:proxy-worker.http2")
        proc = await subprocess.create_subprocess_exec(
            self.root_context.local_config.proxy_worker.http2.nghttpx_path,
            *nghttpx_args,
        )
        assert proc.stdout and proc.stderr
        self.process = proc
        self.log_monitor_tasks.append(
            asyncio.create_task(self._log_monitor_task(proc.stdout, "stdout"))
        )
        self.log_monitor_tasks.append(
            asyncio.create_task(self._log_monitor_task(proc.stderr, "stderr"))
        )
        self.proc_monitor_task = asyncio.create_task(self._proc_monitor_task(proc))
        log.info("accepting proxy requests at {}:{}", service_addr.host, service_addr.port)

    async def stop(self) -> None:
        if not self.proc_monitor_task:
            return
        self.proc_monitor_task.cancel()
        await self.proc_monitor_task
        if not self.process:
            return
        self.process.terminate()
        await self.process.wait()
        try:
            for task in self.log_monitor_tasks:
                task.cancel()
                await task
        finally:
            if self.api_port:
                self.api_port_pool.add(self.api_port)

    async def initialize_backend(self, circuit: Circuit, routes: list[RouteInfo]) -> H2Backend:
        backend = H2Backend(URL(f"http://localhost:{self.api_port}"), self.root_context, circuit)
        return await self.update_backend(backend, routes)

    async def update_backend(self, backend: H2Backend, routes: list[RouteInfo]) -> H2Backend:
        backend_configs = [BackendConfig(r.current_kernel_host, r.kernel_port) for r in routes]
        await backend.update_config(backend_configs)
        return backend

    async def terminate_backend(self, backend: H2Backend) -> None:
        await backend.update_config([])

    def get_circuit_key(self, circuit: Circuit) -> str:
        assert isinstance(circuit.frontend, SubdomainFrontendInfo)
        return circuit.frontend.subdomain.lower()
