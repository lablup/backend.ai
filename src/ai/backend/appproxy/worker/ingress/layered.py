from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.appproxy.worker.errors.ingress import IngressNotFoundError
from ai.backend.appproxy.worker.ingress.abc import IngressReader
from ai.backend.appproxy.worker.ingress.in_memory import InMemoryIngressState
from ai.backend.appproxy.worker.ingress.redis import RedisIngressState
from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress, IngressFrontendKey


class LayeredIngressState(IngressReader):
    """Reads the in-memory layer in front of Redis; a Redis hit is applied to memory.

    A key memory knows missing, or one no layer holds, reads as None.
    """

    _memory: InMemoryIngressState | None
    _redis: RedisIngressState | None

    def __init__(
        self, memory: InMemoryIngressState | None, redis: RedisIngressState | None
    ) -> None:
        self._memory = memory
        self._redis = redis

    @property
    def layers(self) -> Sequence[IngressReader]:
        return tuple(layer for layer in (self._memory, self._redis) if layer is not None)

    @override
    async def get(self, frontend_key: IngressFrontendKey) -> Ingress | None:
        if self._memory is not None:
            try:
                ingress = await self._memory.get(frontend_key)
            except IngressNotFoundError:
                # The key was remembered missing on purpose to skip reading Redis.
                return None
            if ingress is not None:
                return ingress
        return await self._read_redis(frontend_key)

    async def _read_redis(self, frontend_key: IngressFrontendKey) -> Ingress | None:
        """Reads a key memory cannot answer from Redis and records the outcome in memory."""
        if self._redis is None:
            return None
        ingress = await self._redis.get(frontend_key)
        if self._memory is None:
            return ingress
        if ingress is None:
            await self._memory.remember_missing(frontend_key)
        else:
            await self._memory.apply([ingress])
        return ingress

    @override
    async def get_all(self) -> list[Ingress]:
        if self._redis is not None:
            return await self._redis.get_all()
        if self._memory is not None:
            return await self._memory.get_all()
        return []
