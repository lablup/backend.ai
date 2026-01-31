import asyncio
import logging
from asyncio import subprocess
from typing import Any

from ai.backend.appproxy.common.errors import ServerMisconfiguredError
from ai.backend.appproxy.worker.proxy.backend.h2 import H2Backend
from ai.backend.appproxy.worker.proxy.frontend.base import BaseFrontend
from ai.backend.appproxy.worker.types import Circuit
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class H2Frontend[TCircuitKeyType: (int, str)](BaseFrontend[H2Backend, TCircuitKeyType]):
    api_port_pool: set[int]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        h2_config = self.root_context.local_config.proxy_worker.http2
        if not h2_config:
            raise ServerMisconfiguredError("worker:proxy-worker.http2")

        self.api_port_pool = set(range(h2_config.api_port_pool[0], h2_config.api_port_pool[1] + 1))

    async def list_inactive_circuits(self, threshold: int) -> list[Circuit]:
        # We can't measure activeness of HTTP/2 circuits
        return []

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
            log.exception("E20010: nghttpx terminated unexpectedly")
