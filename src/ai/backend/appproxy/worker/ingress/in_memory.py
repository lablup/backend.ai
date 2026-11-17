from __future__ import annotations

import asyncio
import math
from collections.abc import Awaitable, Callable, Sequence
from time import monotonic
from typing import override
from weakref import WeakValueDictionary

from cachetools import TTLCache

from ai.backend.appproxy.worker.errors.ingress import IngressNotFoundError
from ai.backend.appproxy.worker.ingress.abc import IngressReader, IngressWriter
from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress, IngressFrontendKey, IngressKey


class InMemoryIngressState(IngressReader, IngressWriter):
    """Ingresses held in the worker process, keyed by frontend key.

    An apply older than the stored revision is skipped, so a late write never undoes a newer one.
    """

    _negative_ttl: float | None
    _ingresses: TTLCache[IngressFrontendKey, Ingress]
    # get raises IngressNotFoundError for these keys so the layered read skips the later layers.
    _missing_keys: TTLCache[IngressFrontendKey, bool]
    _fill_locks: WeakValueDictionary[IngressFrontendKey, asyncio.Lock]

    def __init__(self, ttl: float | None = None, negative_ttl: float | None = None) -> None:
        self._negative_ttl = negative_ttl
        self._ingresses = TTLCache(
            maxsize=math.inf, ttl=ttl if ttl is not None else math.inf, timer=monotonic
        )
        self._missing_keys = TTLCache(
            maxsize=math.inf,
            ttl=negative_ttl if negative_ttl is not None else math.inf,
            timer=monotonic,
        )
        self._fill_locks = WeakValueDictionary()

    @override
    async def get(self, frontend_key: IngressFrontendKey) -> Ingress | None:
        ingress = self._ingresses.get(frontend_key)
        if ingress is not None:
            return ingress
        if frontend_key in self._missing_keys:
            raise IngressNotFoundError(f"frontend {frontend_key} is remembered missing")
        return None

    @override
    async def get_all(self) -> list[Ingress]:
        return list(self._ingresses.values())

    @override
    async def apply(self, ingresses: Sequence[Ingress]) -> None:
        for ingress in ingresses:
            frontend_key = ingress.frontend.key()
            stored_ingress = self._ingresses.get(frontend_key)
            if stored_ingress is not None and ingress.revision < stored_ingress.revision:
                continue
            self._ingresses[frontend_key] = ingress
            self._missing_keys.pop(frontend_key, None)

    @override
    async def remove(self, keys: Sequence[IngressKey]) -> None:
        for key in keys:
            self._ingresses.pop(key.frontend_key, None)
            # remove assumes the key is deleted from every layer, so it is remembered missing.
            await self.remember_missing(key.frontend_key)

    async def remember_missing(self, frontend_key: IngressFrontendKey) -> None:
        if self._negative_ttl is None:
            return
        self._missing_keys[frontend_key] = True

    async def invalidate(self, frontend_keys: Sequence[IngressFrontendKey]) -> None:
        """Unlike remove, an invalidated key is read from the later layers again.

        A fill of the key in progress finishes first, so what it stores is dropped too.
        """
        for frontend_key in frontend_keys:
            async with self._fill_lock(frontend_key):
                self._ingresses.pop(frontend_key, None)
                self._missing_keys.pop(frontend_key, None)

    async def fill(
        self,
        frontend_key: IngressFrontendKey,
        read_ingress: Callable[[], Awaitable[Ingress | None]],
    ) -> Ingress | None:
        """Stores what read_ingress returns unless the key is held already.

        The read and the store hold the key's lock, which invalidate also takes.
        """
        async with self._fill_lock(frontend_key):
            # A fill that held the lock before may have stored the key already.
            held_ingress = await self.get(frontend_key)
            if held_ingress is not None:
                return held_ingress
            ingress = await read_ingress()
            if ingress is not None:
                await self.apply([ingress])
            return ingress

    @override
    async def replace_all(self, ingresses: Sequence[Ingress]) -> None:
        self._ingresses.clear()
        self._ingresses.update({ingress.frontend.key(): ingress for ingress in ingresses})
        self._missing_keys.clear()

    def _fill_lock(self, frontend_key: IngressFrontendKey) -> asyncio.Lock:
        lock = self._fill_locks.get(frontend_key)
        if lock is None:
            lock = asyncio.Lock()
            self._fill_locks[frontend_key] = lock
        return lock
