import asyncio
from collections.abc import Sequence
from typing import Generic, Optional, Protocol, TypeVar

TResourceCtx = TypeVar("TResourceCtx")
TResourceCtx_Co = TypeVar("TResourceCtx_Co", covariant=True)
TResourceCtx_Contra = TypeVar("TResourceCtx_Contra", contravariant=True)


class ResourceCtx(Protocol[TResourceCtx_Co]):
    async def open(self) -> TResourceCtx_Co:
        pass

    async def close(self) -> None:
        pass


class NopResourceCtx:
    def __init__(self) -> None:
        pass

    async def open(self) -> None:
        return None

    async def close(self) -> None:
        return None


class Probe(Protocol[TResourceCtx_Contra]):
    async def probe(self, resource_ctx: TResourceCtx_Contra) -> None:
        pass


class HeartbeatService(Protocol[TResourceCtx_Contra]):
    async def heartbeat(self, resource_ctx: TResourceCtx_Contra) -> None:
        pass


class ProbeRunner(Generic[TResourceCtx]):
    _closed: bool
    _runner_task: Optional[asyncio.Task]

    _resource_ctx: ResourceCtx[TResourceCtx]

    _interval: float
    _heartbeart_services: Sequence[HeartbeatService]
    _probes: Sequence[Probe[TResourceCtx]]

    def __init__(
        self,
        interval: float,
        resource_ctx: ResourceCtx[TResourceCtx],
        probes: Sequence[Probe[TResourceCtx]],
        heartbeart_services: Sequence[HeartbeatService[TResourceCtx]] = tuple(),
    ) -> None:
        self._closed = False
        self._runner_task = None

        self._resource_ctx = resource_ctx

        self._interval = interval
        self._probes = probes
        self._heartbeart_services = heartbeart_services

    @classmethod
    def nop(cls) -> "ProbeRunner[None]":
        obj = ProbeRunner[None](0, NopResourceCtx(), [])
        obj._closed = True
        return obj

    async def close(self) -> None:
        self._closed = True
        if self._runner_task is not None:
            self._runner_task.cancel()
        await self._resource_ctx.close()

    async def _run_probes(self, resource: TResourceCtx) -> None:
        for probe in self._probes:
            await probe.probe(resource)

    async def _heartbeat(self, resource: TResourceCtx) -> None:
        for service in self._heartbeart_services:
            await service.heartbeat(resource)

    async def _task(self) -> None:
        while not self._closed:
            try:
                resource = await self._resource_ctx.open()
                await self._run_probes(resource)
                await self._heartbeat(resource)
            finally:
                await self._resource_ctx.close()

            await asyncio.sleep(self._interval)

    async def run(self) -> None:
        self._runner_task = asyncio.create_task(self._task())
        # Sleep 0 to allow the event loop to start
        await asyncio.sleep(0)
