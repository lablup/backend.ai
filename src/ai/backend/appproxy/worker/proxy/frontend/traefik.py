from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from typing import TYPE_CHECKING, Generic, Mapping, TypeAlias, Union

import aiotools
from aiohttp import web

from ai.backend.appproxy.common.config import get_default_redis_key_ttl
from ai.backend.appproxy.common.exceptions import ServerMisconfiguredError
from ai.backend.appproxy.common.types import RouteInfo
from ai.backend.appproxy.worker.proxy.backend.traefik import TraefikBackend
from ai.backend.logging import BraceStyleAdapter

from ...types import (
    LAST_USED_MARKER_SOCKET_NAME,
    Circuit,
    PortFrontendInfo,
    RootContext,
    SubdomainFrontendInfo,
    TCircuitKey,
)
from .base import BaseFrontend

if TYPE_CHECKING:
    pass

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]
MSetType: TypeAlias = Mapping[Union[str, bytes], Union[bytes, float, int, str]]


class AbstractTraefikFrontend(Generic[TCircuitKey], BaseFrontend[TraefikBackend, TCircuitKey]):
    runner: web.AppRunner
    last_used_time_marker_writer_task: asyncio.Task
    active_circuit_writer_task: asyncio.Task
    redis_keys: dict[str, float]
    redis_keys_lock: asyncio.Lock
    active_circuits: set[uuid.UUID]

    def __init__(self, root_context: RootContext) -> None:
        super().__init__(root_context)
        config = root_context.local_config.proxy_worker.traefik
        if not config:
            raise ServerMisconfiguredError("proxy_worker.traefik config not prepared")

        self.redis_keys = {}
        self.redis_keys_lock = asyncio.Lock()
        self.active_circuits = set()

        app = web.Application()
        app.router.add_head("/{key}/mark-last-used-time", self.mark_last_used_time)
        app.router.add_head("/{key}/mark-active", self.mark_active)
        app.router.add_head("/{key}/mark-inactive", self.mark_inactive)
        self.runner = web.AppRunner(app, access_log=None)

    async def start(self) -> None:
        assert self.root_context.local_config.proxy_worker.traefik
        path = (
            self.root_context.local_config.proxy_worker.traefik.last_used_time_marker_directory
            / LAST_USED_MARKER_SOCKET_NAME
        )
        if path.exists():
            os.remove(path)

        await self.runner.setup()
        site = web.UnixSite(self.runner, path)
        await site.start()

        self.last_used_time_marker_writer_task = aiotools.create_timer(
            self._last_used_time_marker_writer,
            10.0,
        )
        self.active_circuit_writer_task = aiotools.create_timer(
            self._active_circuit_writer,
            5.0,
        )

    async def stop(self) -> None:
        assert self.root_context.local_config.proxy_worker.traefik

        await self.runner.cleanup()

        self.last_used_time_marker_writer_task.cancel()
        self.active_circuit_writer_task.cancel()
        await self.last_used_time_marker_writer_task
        await self.active_circuit_writer_task

    async def _last_used_time_marker_writer(self, interval: float) -> None:
        try:
            async with self.redis_keys_lock:
                if len(self.redis_keys) == 0:
                    return
                keys = self.redis_keys
                self.redis_keys = {}

            data = {key: str(value) for key, value in keys.items()}
            ttl = get_default_redis_key_ttl()
            await self.root_context.valkey_live.store_multiple_live_data(data, ex=ttl)

            log.debug("Wrote {} keys", len(keys))
        except Exception:
            log.exception("_last_used_time_marker_writer():")

    async def mark_last_used_time(self, request: web.Request) -> web.StreamResponse:
        key = request.match_info["key"]
        self.redis_keys.update({key: time.time()})

        return web.StreamResponse(status=204)

    async def mark_active(self, request: web.Request) -> web.StreamResponse:
        key = request.match_info["key"]
        self.active_circuits.add(uuid.UUID(key))

        return web.StreamResponse(status=204)

    async def mark_inactive(self, request: web.Request) -> web.StreamResponse:
        key = request.match_info["key"]
        try:
            self.active_circuits.remove(uuid.UUID(key))
        except KeyError:
            log.warning("mark_inactive(): key {!r} not found in active circuits", key)

        return web.StreamResponse(status=204)

    async def _active_circuit_writer(self, interval: float) -> None:
        try:
            if len(self.active_circuits) > 0:
                now = time.time()
                keys: dict[str, float] = {}
                for c in self.active_circuits:
                    keys[f"circuit.{c}.last_access"] = now
                async with self.redis_keys_lock:
                    self.redis_keys.update(keys)
        except Exception:
            log.exception("_active_circuit_writer():")

    async def initialize_backend(self, circuit: Circuit, routes: list[RouteInfo]) -> TraefikBackend:
        return TraefikBackend(self.root_context, circuit, routes)

    async def update_backend(
        self, backend: TraefikBackend, routes: list[RouteInfo]
    ) -> TraefikBackend:
        backend.routes = routes
        return backend

    async def terminate_backend(self, backend: TraefikBackend) -> None:
        pass

    async def list_inactive_circuits(self, threshold: int) -> list[Circuit]:
        # FIXME: implement
        return []


class TraefikPortFrontend(AbstractTraefikFrontend[int]):
    def get_circuit_key(self, circuit: Circuit) -> int:
        assert isinstance(circuit.frontend, PortFrontendInfo)
        return circuit.frontend.port


class TraefikSubdomainFrontend(AbstractTraefikFrontend[str]):
    def get_circuit_key(self, circuit: Circuit) -> str:
        assert isinstance(circuit.frontend, SubdomainFrontendInfo)
        return circuit.frontend.subdomain


class TraefikTCPFrontend(AbstractTraefikFrontend[int]):
    def get_circuit_key(self, circuit: Circuit) -> int:
        assert isinstance(circuit.frontend, PortFrontendInfo)
        return circuit.frontend.port
