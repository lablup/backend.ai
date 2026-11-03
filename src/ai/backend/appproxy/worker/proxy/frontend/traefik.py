from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import Mapping
from typing import Final, override

from aiohttp import web

from ai.backend.appproxy.common.config import ContentEncodingConfig, get_default_redis_key_ttl
from ai.backend.appproxy.common.errors import ServerMisconfiguredError
from ai.backend.appproxy.worker.errors import MissingTraefikConfigError
from ai.backend.appproxy.worker.proxy.backend.base import BaseBackendArgs
from ai.backend.appproxy.worker.proxy.backend.traefik import TraefikBackend
from ai.backend.appproxy.worker.types import (
    LAST_USED_MARKER_SOCKET_NAME,
    Circuit,
    RootContext,
)
from ai.backend.common.cron import LocalCron, PeriodicTask
from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress
from ai.backend.logging.structured import StructuredLogger

from .base import BaseFrontend

log = StructuredLogger(logging.getLogger(__spec__.name))
type MSetType = Mapping[str | bytes, bytes | float | int | str]


_LAST_USED_TIME_MARKER_WRITER_INTERVAL: Final[float] = 10.0
_ACTIVE_CIRCUIT_WRITER_INTERVAL: Final[float] = 5.0


class _LastUsedTimeMarkerWriterTask(PeriodicTask):
    """Periodically flush accumulated last-used-time markers to Valkey."""

    _frontend: Final[TraefikFrontend]

    def __init__(self, frontend: TraefikFrontend) -> None:
        self._frontend = frontend

    @property
    @override
    def name(self) -> str:
        return "last_used_time_marker_writer"

    @property
    @override
    def interval(self) -> float:
        return _LAST_USED_TIME_MARKER_WRITER_INTERVAL

    @property
    @override
    def initial_delay(self) -> float:
        return 0.0

    @override
    async def run(self) -> None:
        await self._frontend.last_used_time_marker_writer()


class _ActiveCircuitWriterTask(PeriodicTask):
    """Periodically refresh last-access timestamps for active circuits."""

    _frontend: Final[TraefikFrontend]

    def __init__(self, frontend: TraefikFrontend) -> None:
        self._frontend = frontend

    @property
    @override
    def name(self) -> str:
        return "active_circuit_writer"

    @property
    @override
    def interval(self) -> float:
        return _ACTIVE_CIRCUIT_WRITER_INTERVAL

    @property
    @override
    def initial_delay(self) -> float:
        return 0.0

    @override
    async def run(self) -> None:
        await self._frontend.active_circuit_writer()


class TraefikFrontend(BaseFrontend[TraefikBackend]):
    _runner: web.AppRunner
    _redis_keys: dict[str, float]
    _redis_keys_lock: asyncio.Lock
    _active_circuits: set[uuid.UUID]
    _local_cron: LocalCron

    def __init__(self, root_context: RootContext) -> None:
        super().__init__(root_context)
        config = root_context.local_config.proxy_worker.traefik
        if not config:
            raise ServerMisconfiguredError("proxy_worker.traefik config not prepared")

        self._redis_keys = {}
        self._redis_keys_lock = asyncio.Lock()
        self._active_circuits = set()

        app = web.Application()
        app.router.add_head("/{key}/mark-last-used-time", self.mark_last_used_time)
        app.router.add_head("/{key}/mark-active", self.mark_active)
        app.router.add_head("/{key}/mark-inactive", self.mark_inactive)
        self._runner = web.AppRunner(
            app,
            access_log=None,
            max_field_size=root_context.local_config.proxy_worker.max_header_field_size,
        )

    @override
    def apply_content_encoding_config(self, config: ContentEncodingConfig) -> None:
        # The Go plugin applies the config the coordinator writes to Traefik etcd.
        pass

    @override
    async def start(self) -> None:
        if not self.root_context.local_config.proxy_worker.traefik:
            raise MissingTraefikConfigError("Traefik configuration is required")
        path = (
            self.root_context.local_config.proxy_worker.traefik.last_used_time_marker_directory
            / LAST_USED_MARKER_SOCKET_NAME
        )
        if path.exists():
            path.unlink()

        await self._runner.setup()
        site = web.UnixSite(self._runner, path)
        await site.start()

        self._local_cron = LocalCron([
            _LastUsedTimeMarkerWriterTask(self),
            _ActiveCircuitWriterTask(self),
        ])
        await self._local_cron.start()

    @override
    async def stop(self) -> None:
        if not self.root_context.local_config.proxy_worker.traefik:
            raise MissingTraefikConfigError("Traefik configuration is required")

        await self._runner.cleanup()
        await self._local_cron.stop()

    async def last_used_time_marker_writer(self) -> None:
        async with self._redis_keys_lock:
            if len(self._redis_keys) == 0:
                return
            keys = self._redis_keys
            self._redis_keys = {}

        data = {key: str(value) for key, value in keys.items()}
        ttl = get_default_redis_key_ttl()
        await self.root_context.valkey_live.store_multiple_live_data(data, ex=ttl)

        log.debug("wrote {} last-used-time keys", len(keys))

    async def mark_last_used_time(self, request: web.Request) -> web.StreamResponse:
        key = request.match_info["key"]
        self._redis_keys.update({key: time.time()})

        return web.StreamResponse(status=204)

    async def mark_active(self, request: web.Request) -> web.StreamResponse:
        key = request.match_info["key"]
        self._active_circuits.add(uuid.UUID(key))

        return web.StreamResponse(status=204)

    async def mark_inactive(self, request: web.Request) -> web.StreamResponse:
        key = request.match_info["key"]
        try:
            self._active_circuits.remove(uuid.UUID(key))
        except KeyError:
            log.debug("circuit {} to mark inactive is not active", key)

        return web.StreamResponse(status=204)

    async def active_circuit_writer(self) -> None:
        if len(self._active_circuits) > 0:
            now = time.time()
            keys: dict[str, float] = {}
            for c in self._active_circuits:
                keys[f"circuit.{c}.last_access"] = now
            async with self._redis_keys_lock:
                self._redis_keys.update(keys)

    @override
    async def initialize_backend(self, ingress: Ingress, circuit: Circuit) -> TraefikBackend:
        return TraefikBackend(
            BaseBackendArgs(
                last_used_time_mark_queue=self.root_context.last_used_time_mark_queue,
                request_counter_key_queue=self.root_context.request_counter_key_queue,
                ingress=ingress,
                circuit=circuit,
            )
        )

    @override
    async def terminate_backend(self, backend: TraefikBackend) -> None:
        pass
