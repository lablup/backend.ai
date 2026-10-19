from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import override

from ai.backend.appproxy.worker.errors.ingress import (
    IngressAuthorityMismatchError,
    IngressNotFoundError,
    IngressRevisionConflictError,
)
from ai.backend.appproxy.worker.ingress.abc import IngressWriter
from ai.backend.appproxy.worker.ingress.in_memory import InMemoryIngressState
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressAuthority,
    IngressFrontendKey,
    IngressKey,
)


class ValidatingIngressWriter(IngressWriter):
    """Rejects ingresses of another authority and applies older than held, then delegates."""

    _state: InMemoryIngressState
    _authority: IngressAuthority
    _lock: asyncio.Lock

    def __init__(self, state: InMemoryIngressState, authority: IngressAuthority) -> None:
        self._state = state
        self._authority = authority
        self._lock = asyncio.Lock()

    @override
    async def apply(self, ingresses: Sequence[Ingress]) -> list[Ingress]:
        self._check_authority([ingress.authority for ingress in ingresses])
        async with self._lock:
            for ingress in ingresses:
                held = await self._held(ingress.frontend.key())
                if held is not None and ingress.revision < held.revision:
                    raise IngressRevisionConflictError(
                        f"frontend {ingress.frontend.key()} holds revision {held.revision}, "
                        f"got {ingress.revision}"
                    )
            return await self._state.apply(ingresses)

    @override
    async def remove(self, keys: Sequence[IngressKey]) -> None:
        self._check_authority([key.authority for key in keys])
        async with self._lock:
            await self._state.remove(keys)

    @override
    async def replace_all(self, ingresses: Sequence[Ingress]) -> list[Ingress]:
        self._check_authority([ingress.authority for ingress in ingresses])
        async with self._lock:
            return await self._state.replace_all(ingresses)

    async def _held(self, frontend_key: IngressFrontendKey) -> Ingress | None:
        try:
            return await self._state.get(frontend_key)
        except IngressNotFoundError:
            return None

    def _check_authority(self, authorities: Sequence[IngressAuthority]) -> None:
        for authority in authorities:
            if authority != self._authority:
                raise IngressAuthorityMismatchError(
                    f"ingress of {authority} sent to the worker of {self._authority}"
                )
