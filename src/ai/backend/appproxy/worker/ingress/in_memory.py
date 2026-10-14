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

    An apply older than the held revision is skipped, so a late write never undoes a newer one.
    """

    _negative_ttl: float | None
    _held: TTLCache[IngressFrontendKey, Ingress]
    _missing: TTLCache[IngressFrontendKey, bool]

    def __init__(self, ttl: float | None = None, negative_ttl: float | None = None) -> None:
        self._negative_ttl = negative_ttl
        self._held = TTLCache(
            maxsize=math.inf, ttl=ttl if ttl is not None else math.inf, timer=monotonic
        )
        self._missing = TTLCache(
            maxsize=math.inf,
            ttl=negative_ttl if negative_ttl is not None else math.inf,
            timer=monotonic,
        )

    @override
    async def get(self, frontend_key: IngressFrontendKey) -> Ingress | None:
        ingress = self._held.get(frontend_key)
        if ingress is not None:
            return ingress
        if frontend_key in self._missing:
            raise IngressNotFoundError(f"frontend {frontend_key} is remembered missing")
        return None

    @override
    async def get_all(self) -> list[Ingress]:
        return list(self._held.values())

    @override
    async def apply(self, ingresses: Sequence[Ingress]) -> None:
        for ingress in ingresses:
            frontend_key = ingress.frontend.key()
            held = self._held.get(frontend_key)
            if held is not None and ingress.revision < held.revision:
                continue
            self._held[frontend_key] = ingress
            self._missing.pop(frontend_key, None)

    @override
    async def remove(self, keys: Sequence[IngressKey]) -> None:
        for key in keys:
            self._held.pop(key.frontend_key, None)

    async def remember_missing(self, frontend_key: IngressFrontendKey) -> None:
        if self._negative_ttl is None:
            return
        self._missing[frontend_key] = True

    @override
    async def replace_all(self, ingresses: Sequence[Ingress]) -> None:
        self._held.clear()
        self._held.update({ingress.frontend.key(): ingress for ingress in ingresses})
        self._missing.clear()
