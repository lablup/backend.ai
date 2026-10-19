from __future__ import annotations

import math
from collections.abc import Sequence
from time import monotonic
from typing import override

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
    async def apply(self, ingresses: Sequence[Ingress]) -> list[Ingress]:
        held: list[Ingress] = []
        for ingress in ingresses:
            frontend_key = ingress.frontend.key()
            stored_ingress = self._ingresses.get(frontend_key)
            if stored_ingress is not None and ingress.revision < stored_ingress.revision:
                held.append(stored_ingress)
                continue
            self._ingresses[frontend_key] = ingress
            self._missing_keys.pop(frontend_key, None)
            held.append(ingress)
        return held

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

    @override
    async def replace_all(self, ingresses: Sequence[Ingress]) -> list[Ingress]:
        self._ingresses.clear()
        self._ingresses.update({ingress.frontend.key(): ingress for ingress in ingresses})
        self._missing_keys.clear()
        return list(self._ingresses.values())
