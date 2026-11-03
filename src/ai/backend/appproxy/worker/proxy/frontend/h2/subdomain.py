import asyncio
import logging
from asyncio import subprocess
from typing import Any, override

from yarl import URL

from ai.backend.appproxy.common.errors import ServerMisconfiguredError
from ai.backend.appproxy.worker.errors import SubprocessPipeError
from ai.backend.appproxy.worker.proxy.backend.h2 import H2Backend, H2BackendArgs
from ai.backend.appproxy.worker.types import Circuit
from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress
from ai.backend.logging.structured import StructuredLogger

from .base import H2Frontend

log = StructuredLogger(logging.getLogger(__spec__.name))


class SubdomainFrontend(H2Frontend):
    process: subprocess.Process | None
    log_monitor_tasks: list[asyncio.Task[Any]]
    proc_monitor_task: asyncio.Task[Any] | None

    api_port: int | None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.process = None
        self.log_monitor_tasks = []
        self.proc_monitor_task = None

    @override
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
        log.info("accepting proxy requests", service_addr=str(service_addr))

    @override
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

    @override
    async def initialize_backend(self, ingress: Ingress, circuit: Circuit) -> H2Backend:
        backend = H2Backend(
            H2BackendArgs(
                last_used_time_marker_redis_queue=self.root_context.last_used_time_marker_redis_queue,
                request_counter_redis_queue=self.root_context.request_counter_redis_queue,
                ingress=ingress,
                circuit=circuit,
                api_endpoint=URL(f"http://localhost:{self.api_port}"),
            )
        )
        await backend.update_ingress(ingress)
        return backend

    @override
    async def terminate_backend(self, backend: H2Backend) -> None:
        await backend.update_config([])
