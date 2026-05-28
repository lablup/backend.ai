from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Final

from aiohttp import web

from ai.backend.appproxy.common.config import get_default_redis_key_ttl
from ai.backend.appproxy.common.errors import ServerMisconfiguredError
from ai.backend.appproxy.common.types import RouteInfo
from ai.backend.appproxy.worker.errors import InvalidFrontendTypeError, MissingTraefikConfigError
from ai.backend.appproxy.worker.proxy.backend.traefik import TraefikBackend
from ai.backend.appproxy.worker.types import (
    LAST_USED_MARKER_SOCKET_NAME,
    Circuit,
    PortFrontendInfo,
    RootContext,
    SubdomainFrontendInfo,
)
from ai.backend.common.cron import LocalCron, PeriodicTask
from ai.backend.logging import BraceStyleAdapter

from .base import BaseFrontend

if TYPE_CHECKING:
    pass

log = BraceStyleAdapter(logging.getLogger(__spec__.name))
type MSetType = Mapping[str | bytes, bytes | float | int | str]


_LAST_USED_TIME_MARKER_WRITER_INTERVAL: Final[float] = 10.0
_ACTIVE_CIRCUIT_WRITER_INTERVAL: Final[float] = 5.0


class _LastUsedTimeMarkerWriterTask(PeriodicTask):
    """Periodically flush accumulated last-used-time markers to Valkey."""

    _frontend: Final[AbstractTraefikFrontend[Any]]

    def __init__(self, frontend: AbstractTraefikFrontend[Any]) -> None:
        self._frontend = frontend

    @property
    def name(self) -> str:
        return "last_used_time_marker_writer"

    @property
    def interval(self) -> float:
        return _LAST_USED_TIME_MARKER_WRITER_INTERVAL

    @property
    def initial_delay(self) -> float:
        return 0.0

    async def run(self) -> None:
        await self._frontend.last_used_time_marker_writer()


class _ActiveCircuitWriterTask(PeriodicTask):
    """Periodically refresh last-access timestamps for active circuits."""

    _frontend: Final[AbstractTraefikFrontend[Any]]

    def __init__(self, frontend: AbstractTraefikFrontend[Any]) -> None:
        self._frontend = frontend

    @property
    def name(self) -> str:
        return "active_circuit_writer"

    @property
    def interval(self) -> float:
        return _ACTIVE_CIRCUIT_WRITER_INTERVAL

    @property
    def initial_delay(self) -> float:
        return 0.0

    async def run(self) -> None:
        await self._frontend.active_circuit_writer()


class AbstractTraefikFrontend[TCircuitKeyType: (int, str)](
    BaseFrontend[TraefikBackend, TCircuitKeyType]
):
    runner: web.AppRunner
    _local_cron: LocalCron
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
        if not self.root_context.local_config.proxy_worker.traefik:
            raise MissingTraefikConfigError("Traefik configuration is required")
        path = (
            self.root_context.local_config.proxy_worker.traefik.last_used_time_marker_directory
            / LAST_USED_MARKER_SOCKET_NAME
        )
        if path.exists():
            path.unlink()

        await self.runner.setup()
        site = web.UnixSite(self.runner, path)
        await site.start()

        self._local_cron = LocalCron([
            _LastUsedTimeMarkerWriterTask(self),
            _ActiveCircuitWriterTask(self),
        ])
        await self._local_cron.start()

    async def stop(self) -> None:
        if not self.root_context.local_config.proxy_worker.traefik:
            raise MissingTraefikConfigError("Traefik configuration is required")

        await self.runner.cleanup()
        await self._local_cron.stop()

    async def last_used_time_marker_writer(self) -> None:
        async with self.redis_keys_lock:
            if len(self.redis_keys) == 0:
                return
            keys = self.redis_keys
            self.redis_keys = {}

        data = {key: str(value) for key, value in keys.items()}
        ttl = get_default_redis_key_ttl()
        await self.root_context.valkey_live.store_multiple_live_data(data, ex=ttl)

        log.debug("Wrote {} keys", len(keys))

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

    async def active_circuit_writer(self) -> None:
        if len(self.active_circuits) > 0:
            now = time.time()
            keys: dict[str, float] = {}
            for c in self.active_circuits:
                keys[f"circuit.{c}.last_access"] = now
            async with self.redis_keys_lock:
                self.redis_keys.update(keys)

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
        if not isinstance(circuit.frontend, PortFrontendInfo):
            raise InvalidFrontendTypeError(
                f"Expected PortFrontendInfo, got {type(circuit.frontend).__name__}"
            )
        return circuit.frontend.port


class TraefikSubdomainFrontend(AbstractTraefikFrontend[str]):
    def get_circuit_key(self, circuit: Circuit) -> str:
        if not isinstance(circuit.frontend, SubdomainFrontendInfo):
            raise InvalidFrontendTypeError(
                f"Expected SubdomainFrontendInfo, got {type(circuit.frontend).__name__}"
            )
        return circuit.frontend.subdomain


class TraefikTCPFrontend(AbstractTraefikFrontend[int]):
    def get_circuit_key(self, circuit: Circuit) -> int:
        if not isinstance(circuit.frontend, PortFrontendInfo):
            raise InvalidFrontendTypeError(
                f"Expected PortFrontendInfo, got {type(circuit.frontend).__name__}"
            )
        return circuit.frontend.port
