from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, final

from aiohttp.streams import AsyncStreamIterator
from multidict import CIMultiDict
from yarl import URL

from ai.backend.appproxy.worker.types import Circuit
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressTarget,
    SessionIngressTarget,
)
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


@dataclass
class HttpRequest:
    method: str
    path: str | URL
    headers: CIMultiDict[str] | dict[str, Any]
    body: AsyncStreamIterator[bytes] | None


@dataclass(frozen=True)
class BaseBackendArgs:
    ingress: Ingress
    circuit: Circuit
    last_used_time_marker_redis_queue: asyncio.Queue[tuple[list[str], float]]
    request_counter_redis_queue: asyncio.Queue[str]


class BaseBackend:
    _ingress: Ingress
    # TODO: Drop the circuit once an ingress carries what is read from it.
    _circuit: Circuit
    _last_used_time_marker_redis_queue: asyncio.Queue[tuple[list[str], float]]
    _request_counter_redis_queue: asyncio.Queue[str]

    def __init__(self, args: BaseBackendArgs) -> None:
        self._ingress = args.ingress
        self._circuit = args.circuit
        self._last_used_time_marker_redis_queue = args.last_used_time_marker_redis_queue
        self._request_counter_redis_queue = args.request_counter_redis_queue

    @property
    def ingress(self) -> Ingress:
        return self._ingress

    @property
    def circuit(self) -> Circuit:
        return self._circuit

    async def close(self) -> None:
        pass

    async def update_ingress(self, ingress: Ingress) -> None:
        self._ingress = ingress

    @final
    async def mark_last_used_time(self, target: IngressTarget) -> None:
        # TODO: Legacy last access of the circuit, which the coordinator reads by circuit id.
        # Use the ingress id once ingresses are stored as their own entity.
        last_access_keys = [f"circuit.{self._circuit.id}.last_access"]
        match target:
            case SessionIngressTarget():
                last_access_keys.append(f"session.{target.session_id}.last_access")
        await self._last_used_time_marker_redis_queue.put((
            last_access_keys,
            time.time(),
        ))

    @final
    async def increase_request_counter(self) -> None:
        # TODO: Use the ingress id once ingresses are stored as their own entity.
        await self._request_counter_redis_queue.put(f"circuit.{self._circuit.id}.requests")
