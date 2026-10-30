import asyncio
import logging
from asyncio import subprocess
from typing import Any, override

from yarl import URL

from ai.backend.appproxy.common.errors import ServerMisconfiguredError
from ai.backend.appproxy.common.types import RouteInfo
from ai.backend.appproxy.worker.errors import InvalidFrontendTypeError, SubprocessPipeError
from ai.backend.appproxy.worker.proxy.backend.h2 import H2Backend
from ai.backend.appproxy.worker.types import Circuit, SubdomainFrontendInfo
from ai.backend.logging.structured import StructuredLogger

from .base import H2Frontend

log = StructuredLogger(logging.getLogger(__spec__.name))


class SubdomainFrontend(H2Frontend[str]):
    process: subprocess.Process | None
    log_monitor_tasks: list[asyncio.Task[Any]]
    proc_monitor_task: asyncio.Task[Any] | None

    api_port: int

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.process = None
        self.log_monitor_tasks = []
        self.proc_monitor_task = None
        self.api_port = self.api_port_pool.pop()

    @override
    async def start(self) -> None:
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
        if not proc.stdout or not proc.stderr:
            raise SubprocessPipeError("Subprocess stdout or stderr is not available")
        self.process = proc
        self.log_monitor_tasks.append(
            asyncio.create_task(self._log_monitor_task(proc.stdout, "stdout"))
        )
        self.log_monitor_tasks.append(
            asyncio.create_task(self._log_monitor_task(proc.stderr, "stderr"))
        )
        self.proc_monitor_task = asyncio.create_task(self._proc_monitor_task(proc))
        self._nghttpx_running = True
        await self._send_registered_backend_routes()
        log.info("accepting proxy requests", service_addr=str(service_addr))

    @override
    async def stop(self) -> None:
        self._nghttpx_running = False
        if not self.proc_monitor_task:
            return
        self.proc_monitor_task.cancel()
        await self.proc_monitor_task
        if not self.process:
            return
        self.process.terminate()
        await self.process.wait()
        for task in self.log_monitor_tasks:
            task.cancel()
            await task

    @override
    async def initialize_backend(self, circuit: Circuit, routes: list[RouteInfo]) -> H2Backend:
        backend = H2Backend(URL(f"http://localhost:{self.api_port}"), self.root_context, circuit)
        return await self.update_backend(backend, routes)

    @override
    def get_circuit_key(self, circuit: Circuit) -> str:
        if not isinstance(circuit.frontend, SubdomainFrontendInfo):
            raise InvalidFrontendTypeError(
                f"Expected SubdomainFrontendInfo, got {type(circuit.frontend).__name__}"
            )
        return circuit.frontend.subdomain.lower()
