import asyncio
import logging
from asyncio import subprocess
from typing import Generic

from ai.backend.appproxy.common.exceptions import ServerMisconfiguredError
from ai.backend.appproxy.worker.proxy.backend.h2 import H2Backend
from ai.backend.appproxy.worker.types import Circuit, TCircuitKey
from ai.backend.logging import BraceStyleAdapter

from ..base import BaseFrontend

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class H2Frontend(Generic[TCircuitKey], BaseFrontend[H2Backend, TCircuitKey]):
    api_port_pool: set[int]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        h2_config = self.root_context.local_config.proxy_worker.http2
        if not h2_config:
            raise ServerMisconfiguredError("worker:proxy-worker.http2")

        self.api_port_pool = set(range(h2_config.api_port_pool[0], h2_config.api_port_pool[1] + 1))

    async def list_inactive_circuits(self, threshold: int) -> list[Circuit]:
        # We can't measure activeness of HTTP/2 circuits
        return []

    async def _log_monitor_task(self, stream: asyncio.StreamReader, log_header_postfix="") -> None:
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
