from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.appproxy.worker.ingress.abc import IngressReader, IngressWriter
from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress, IngressFrontendKey, IngressKey
from ai.backend.common.exception import GenericNotImplementedError


class InMemoryIngressState(IngressReader, IngressWriter):
    """Ingresses held in the worker process, keyed by frontend key."""

    _ttl: float | None
    _negative_ttl: float | None

    def __init__(self, ttl: float | None = None, negative_ttl: float | None = None) -> None:
        self._ttl = ttl
        self._negative_ttl = negative_ttl

    @override
    async def get(self, frontend_key: IngressFrontendKey) -> Ingress | None:
        # Return the held ingress; one past ttl counts as not held. Raise IngressNotFoundError
        # for a key remembered missing within negative_ttl.
        raise GenericNotImplementedError

    @override
    async def get_all(self) -> list[Ingress]:
        # Return every held ingress not past ttl.
        raise GenericNotImplementedError

    @override
    async def apply(self, ingresses: Sequence[Ingress]) -> None:
        # Store each by frontend key, replacing the held one.
        raise GenericNotImplementedError

    @override
    async def remove(self, keys: Sequence[IngressKey]) -> None:
        # Drop each by frontend key; a missing one is ignored.
        raise GenericNotImplementedError

    async def remember_missing(self, frontend_key: IngressFrontendKey) -> None:
        # Record the key as missing for negative_ttl; a no-op when negative_ttl is unset.
        raise GenericNotImplementedError

    @override
    async def replace_all(self, ingresses: Sequence[Ingress]) -> None:
        # Swap the whole map in one step.
        raise GenericNotImplementedError
