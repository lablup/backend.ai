import asyncio
import logging
import os
import time
import uuid
from typing import Generic, Mapping, TypeAlias, Union, cast

import aiotools
from aiohttp import web

from ai.backend.appproxy.common.exceptions import ServerMisconfiguredError
from ai.backend.appproxy.common.logging_utils import BraceStyleAdapter
from ai.backend.appproxy.common.types import RouteInfo
from ai.backend.appproxy.worker.proxy.backend.traefik import TraefikBackend
from ai.backend.common import redis_helper
from ai.backend.common.defs import REDIS_LIVE_DB, RedisRole
from ai.backend.common.redis_client import RedisConnection
from ai.backend.common.types import RedisProfileTarget

from ...types import (
    LAST_USED_MARKER_SOCKET_NAME,
    Circuit,
    PortFrontendInfo,
    RootContext,
    SubdomainFrontendInfo,
    TCircuitKey,
)
from .abc import AbstractFrontend

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]
MSetType: TypeAlias = Mapping[Union[str, bytes], Union[bytes, float, int, str]]


class AbstractTraefikFrontend(Generic[TCircuitKey], AbstractFrontend[TraefikBackend, TCircuitKey]):
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

        if self.root_context.local_config.proxy_worker.use_experimental_redis_event_dispatcher:
            self.last_used_time_marker_writer_task = aiotools.create_timer(
                self._last_used_time_marker_writer_experimental,
                10.0,
            )
        else:
            self.last_used_time_marker_writer_task = aiotools.create_timer(
                self._last_used_time_marker_writer_redispy,
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

    async def _last_used_time_marker_writer_experimental(self, interval: float) -> None:
        redis_profile_target = RedisProfileTarget.from_dict(
            self.root_context.local_config.redis.to_dict()
        )
        try:
            async with RedisConnection(
                redis_profile_target.profile_target(RedisRole.LIVE),
                db=REDIS_LIVE_DB,
            ) as client:
                async with self.redis_keys_lock:
                    if len(self.redis_keys) == 0:
                        return
                    keys = self.redis_keys
                    self.redis_keys = {}

                command: list[str | float] = ["MSET"]
                for key, value in keys.items():
                    command.extend([key, value])

                await client.execute(command)
                log.debug("Wrote {} keys", len(keys))
        except Exception:
            log.exception("_last_used_time_marker_writer():")
            raise

    async def _last_used_time_marker_writer_redispy(self, interval: float) -> None:
        try:
            async with self.redis_keys_lock:
                if len(self.redis_keys) == 0:
                    return
                keys = self.redis_keys
                self.redis_keys = {}

            await redis_helper.execute(
                self.root_context.redis_live, lambda r: r.mset(cast(MSetType, keys))
            )

            log.debug("Wrote {} keys", len(keys))
        except Exception:
            log.exception("_last_used_time_marker_writer():")
            raise

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
        self.active_circuits.remove(uuid.UUID(key))

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
            raise

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
