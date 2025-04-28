import asyncio
from collections.abc import Sequence
from typing import Optional, Protocol


class Resource(Protocol):
    async def open(self) -> None:
        pass

    async def close(self) -> None:
        pass


class Probe(Protocol):
    async def probe(self) -> None:
        pass


class HeartbeatService(Protocol):
    async def heartbeat(self) -> None:
        pass


class ProbeRunner:
    _closed: bool
    _runner_task: Optional[asyncio.Task]

    _interval: float
    _resources: Sequence[Resource]
    _heartbeart_services: Sequence[HeartbeatService]
    _probes: Sequence[Probe]

    def __init__(
        self,
        interval: float,
        probes: Sequence[Probe],
        resources: Sequence[Resource] = tuple(),
        heartbeart_services: Sequence[HeartbeatService] = tuple(),
    ) -> None:
        self._closed = False
        self._runner_task = None

        self._interval = interval
        self._probes = probes
        self._resources = resources
        self._heartbeart_services = heartbeart_services

    @classmethod
    def nop(cls) -> "ProbeRunner":
        obj = cls(0, [])
        obj._closed = True
        return obj

    async def close(self) -> None:
        self._closed = True
        if self._runner_task is not None:
            self._runner_task.cancel()
        await self._close_resources()

    async def _run_probes(self) -> None:
        for probe in self._probes:
            await probe.probe()

    async def _heartbeat(self) -> None:
        for service in self._heartbeart_services:
            await service.heartbeat()

    async def _open_resources(self) -> None:
        for resource in self._resources:
            await resource.open()

    async def _close_resources(self) -> None:
        for resource in self._resources:
            await resource.close()

    async def _task(self) -> None:
        while not self._closed:
            try:
                await self._open_resources()
                await self._run_probes()
                await self._heartbeat()
            finally:
                await self._close_resources()

            await asyncio.sleep(self._interval)

    async def run(self) -> None:
        self._runner_task = asyncio.create_task(self._task())
        # Sleep 0 to allow the event loop to start
        await asyncio.sleep(0)
