from __future__ import annotations

from collections.abc import Sequence

from ai.backend.appproxy.worker.ingress.in_memory import InMemoryIngressState
from ai.backend.common.dto.appproxy.v2.ingress.types import IngressAuthority, IngressKey


class InvalidatingIngressWriter:
    """Drops the in-memory copies of invalidated keys so they are read from the later layers again.

    An invalidation carries the keys of every worker; keys of another authority are skipped.
    """

    _state: InMemoryIngressState
    _authority: IngressAuthority

    def __init__(self, state: InMemoryIngressState, authority: IngressAuthority) -> None:
        self._state = state
        self._authority = authority

    async def apply(self, keys: Sequence[IngressKey]) -> None:
        await self._state.invalidate([
            key.frontend_key for key in keys if key.authority == self._authority
        ])
