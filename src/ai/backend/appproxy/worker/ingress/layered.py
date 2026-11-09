from __future__ import annotations

from collections.abc import Sequence
from typing import override

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

    def __init__(
        self, layers: Sequence[IngressReader], in_memory: InMemoryIngressState | None
    ) -> None:
        self._layers = list(layers)
        self._in_memory = in_memory

    @property
    def layers(self) -> Sequence[IngressReader]:
        return tuple(self._layers)

    @override
    async def get(self, frontend_key: IngressFrontendKey) -> Ingress | None:
        try:
            for layer in self._layers:
                ingress = await layer.get(frontend_key)
                if ingress is None:
                    continue
                if self._in_memory is not None and layer is not self._in_memory:
                    # Cache another layer's hit in memory so the next read stops at memory.
                    await self._in_memory.apply([ingress])
                return ingress
            # Requests keep reaching a key that is gone and no longer remembered; surface it.
            raise IngressNotRegisteredError(f"no layer holds frontend {frontend_key}")
        except IngressNotFoundError:
            # The key was remembered missing on removal to skip reading the later layers.
            return None

    @override
    async def get_all(self) -> list[Ingress]:
        return await self._layers[-1].get_all()
