import asyncio
import logging
from asyncio import subprocess
from typing import Any, Final, override

import aiohttp
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_delay, wait_fixed

from ai.backend.appproxy.common.config import ContentEncodingConfig
from ai.backend.appproxy.common.errors import ServerMisconfiguredError
from ai.backend.appproxy.common.types import RouteInfo
from ai.backend.appproxy.worker.proxy.backend.h2 import BackendConfig, H2Backend
from ai.backend.appproxy.worker.proxy.frontend.base import BaseFrontend
from ai.backend.appproxy.worker.types import Circuit
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

_NGHTTPX_API_STARTUP_TIMEOUT: Final[float] = 10.0
_NGHTTPX_API_RETRY_INTERVAL: Final[float] = 0.2


class H2Frontend[TCircuitKeyType: (int, str)](BaseFrontend[H2Backend, TCircuitKeyType]):
    api_port_pool: set[int]
    # Backends registered before start() send their routes once nghttpx runs.
    _nghttpx_running: bool

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        h2_config = self.root_context.local_config.proxy_worker.http2
        if not h2_config:
            raise ServerMisconfiguredError("worker:proxy-worker.http2")

        self.api_port_pool = set(range(h2_config.api_port_pool[0], h2_config.api_port_pool[1] + 1))
        self._nghttpx_running = False

    @override
    async def update_backend(self, backend: H2Backend, routes: list[RouteInfo]) -> H2Backend:
        if self._nghttpx_running:
            await backend.update_config([
                BackendConfig(route.current_kernel_host, route.kernel_port) for route in routes
            ])
        return backend

    @override
    async def terminate_backend(self, backend: H2Backend) -> None:
        if self._nghttpx_running:
            await backend.update_config([])

    async def _send_registered_backend_routes(self) -> None:
        for backend in self.backends.values():
            async for attempt in AsyncRetrying(
                wait=wait_fixed(_NGHTTPX_API_RETRY_INTERVAL),
                stop=stop_after_delay(_NGHTTPX_API_STARTUP_TIMEOUT),
                retry=retry_if_exception_type(aiohttp.ClientConnectionError),
                reraise=True,
            ):
                with attempt:
                    await self.update_backend(backend, backend.circuit.route_info)

    @override
    async def list_inactive_circuits(self, threshold: int) -> list[Circuit]:
        # We can't measure activeness of HTTP/2 circuits
        return []

    @override
    def apply_content_encoding_config(self, config: ContentEncodingConfig) -> None:
        # nghttpx forwards request bodies without passing them through the worker.
        pass

    async def _log_monitor_task(
        self, stream: asyncio.StreamReader, log_header_postfix: str = ""
    ) -> None:
        while True:
            line = await stream.readline()
            if len(line) == 0:
                return
            log.debug("nghttpx {}: {}", log_header_postfix, line.decode("utf-8"))

    async def _proc_monitor_task(self, proc: subprocess.Process) -> None:
        try:
            await proc.wait()
        except asyncio.CancelledError:
            raise  # process did not terminate before task cleanup
        else:
            log.error("E20010: nghttpx terminated unexpectedly", exit_code=proc.returncode)
