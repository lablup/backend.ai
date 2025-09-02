from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, final

from aiohttp.streams import AsyncStreamIterator
from yarl import URL

from ai.backend.appproxy.common.types import RouteInfo
from ai.backend.appproxy.common.types import SerializableCircuit as Circuit
from ai.backend.appproxy.worker.types import RootContext
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class HttpRequest:
    method: str
    path: str | URL
    headers: dict[str, Any]
    body: AsyncStreamIterator[bytes] | None


class BaseBackend:
    root_context: RootContext
    circuit: Circuit
    last_used: float

    def __init__(self, root_context: RootContext, circuit: Circuit) -> None:
        self.root_context = root_context
        self.circuit = circuit
        self.last_used = time.time()

    async def close(self) -> None:
        pass

    async def update_routes(self, routes: list[RouteInfo]) -> None:
        self.routes = routes

    @final
    async def mark_last_used_time(self, route: RouteInfo) -> None:
        await self.root_context.last_used_time_marker_redis_queue.put((
            [
                f"session.{route.session_id}.last_access",
                f"circuit.{self.circuit.id}.last_access",
            ],
            time.time(),
        ))

    @final
    async def increase_request_counter(self) -> None:
        await self.root_context.request_counter_redis_queue.put(
            f"circuit.{self.circuit.id}.requests"
        )
