from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import override
from weakref import WeakValueDictionary

from ai.backend.appproxy.worker.errors.ingress import (
    IngressNotFoundError,
    IngressNotRegisteredError,
)
from ai.backend.appproxy.worker.ingress.abc import IngressReader
from ai.backend.appproxy.worker.ingress.in_memory import InMemoryIngressState
from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress, IngressFrontendKey


class LayeredIngressState(IngressReader):
    """Reads the layers in order; a hit from another layer is written to the given in-memory state.

    A key removed within negative-ttl reads as None; one no layer holds raises
    IngressNotRegisteredError.
    """

    _layers: list[IngressReader]
    _in_memory: InMemoryIngressState | None
    _memory_fill_locks: WeakValueDictionary[IngressFrontendKey, asyncio.Lock]

    def __init__(
        self, layers: Sequence[IngressReader], in_memory: InMemoryIngressState | None
    ) -> None:
        self._layers = list(layers)
        self._in_memory = in_memory
        self._memory_fill_locks = WeakValueDictionary()

    @property
    def layers(self) -> Sequence[IngressReader]:
        return tuple(self._layers)

    @override
    async def get(self, frontend_key: IngressFrontendKey) -> Ingress | None:
        try:
            for layer in self._layers:
                if self._in_memory is None or layer is self._in_memory:
                    ingress = await layer.get(frontend_key)
                else:
                    ingress = await self._read_layer_into_memory(
                        layer, self._in_memory, frontend_key
                    )
                if ingress is not None:
                    return ingress
            # Requests keep reaching a key that is gone and no longer remembered; surface it.
            raise IngressNotRegisteredError(f"no layer holds frontend {frontend_key}")
        except IngressNotFoundError:
            # The key was remembered missing on removal to skip reading the later layers.
            return None

    @override
    async def get_all(self) -> list[Ingress]:
        return await self._layers[-1].get_all()

    async def invalidate(self, frontend_keys: Sequence[IngressFrontendKey]) -> None:
        if self._in_memory is not None:
            for frontend_key in frontend_keys:
                async with self._memory_fill_lock(frontend_key):
                    await self._in_memory.invalidate([frontend_key])

    async def _read_layer_into_memory(
        self,
        layer: IngressReader,
        in_memory: InMemoryIngressState,
        frontend_key: IngressFrontendKey,
    ) -> Ingress | None:
        # invalidate takes the same lock, so it cannot land between this read and the write of
        # what it read; an invalidation that arrives meanwhile drops the written hit after it.
        async with self._memory_fill_lock(frontend_key):
            # A read that held the lock before may have filled memory with the key already.
            held_ingress = await in_memory.get(frontend_key)
            if held_ingress is not None:
                return held_ingress
            ingress = await layer.get(frontend_key)
            if ingress is not None:
                await in_memory.apply([ingress])
            return ingress

    def _memory_fill_lock(self, frontend_key: IngressFrontendKey) -> asyncio.Lock:
        lock = self._memory_fill_locks.get(frontend_key)
        if lock is None:
            lock = asyncio.Lock()
            self._memory_fill_locks[frontend_key] = lock
        return lock
