import asyncio
from collections.abc import Sequence
from typing import Optional, Protocol


class Probe(Protocol):
    async def probe(self) -> None:
        pass


class HeartbeatService(Protocol):
    async def heartbeat(self) -> None:
        pass


class ProbeRunnerWithNoResourceCtx:
    _closed: bool
    _runner_task: Optional[asyncio.Task]

    _interval: float
    _probes: Sequence[Probe]
    _heartbeart_services: Sequence[HeartbeatService]

    def __init__(
        self,
        interval: float,
        probes: Sequence[Probe],
        heartbeart_services: Sequence[HeartbeatService] = tuple(),
    ) -> None:
        self._closed = False
        self._runner_task = None

        self._interval = interval
        self._probes = probes
        self._heartbeart_services = heartbeart_services

    @classmethod
    def nop(cls) -> "ProbeRunnerWithNoResourceCtx":
        obj = cls(0, [])
        obj._closed = True
        return obj

    async def close(self) -> None:
        self._closed = True
        if self._runner_task is not None:
            self._runner_task.cancel()

    async def _run_probes(self) -> None:
        for probe in self._probes:
            await probe.probe()

    async def _heartbeat(self) -> None:
        for service in self._heartbeart_services:
            await service.heartbeat()

    async def _task(self) -> None:
        while not self._closed:
            await self._run_probes()
            await self._heartbeat()

            if self._closed:
                break
            await asyncio.sleep(self._interval)

    async def run(self) -> None:
        self._runner_task = asyncio.create_task(self._task())
        # Sleep 0 to allow the event loop to start
        await asyncio.sleep(0)
