import logging
import time
from abc import ABCMeta
from dataclasses import dataclass
from typing import Any

import aiohttp
from yarl import URL

from ai.backend.appproxy.common.logging_utils import BraceStyleAdapter
from ai.backend.appproxy.common.types import RouteInfo
from ai.backend.appproxy.common.types import SerializableCircuit as Circuit
from ai.backend.appproxy.worker.types import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


@dataclass
class HttpRequest:
    method: str
    path: str | URL
    headers: dict[str, Any]
    body: aiohttp.StreamReader


class AbstractBackend(metaclass=ABCMeta):
    root_context: RootContext
    circuit: Circuit
    last_used: float

    def __init__(self, root_context: RootContext, circuit: Circuit) -> None:
        self.root_context = root_context
        self.circuit = circuit
        self.last_used = time.time()

    async def mark_last_used_time(self, route: RouteInfo) -> None:
        await self.root_context.last_used_time_marker_redis_queue.put((
            [
                f"session.{route.session_id}.last_access",
                f"circuit.{self.circuit.id}.last_access",
            ],
            time.time(),
        ))

    async def increase_request_counter(self) -> None:
        await self.root_context.request_counter_redis_queue.put(
            f"circuit.{self.circuit.id}.requests"
        )
