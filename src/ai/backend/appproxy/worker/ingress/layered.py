from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.appproxy.worker.errors.ingress import IngressNotFoundError
from ai.backend.appproxy.worker.ingress.abc import IngressReader
from ai.backend.appproxy.worker.ingress.in_memory import InMemoryIngressState
from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress, IngressFrontendKey


class LayeredIngressState(IngressReader):
    """Reads the layers in order; a later layer's hit is cached in the in-memory layer.

    A key memory knows missing, or one no layer holds, reads as None.
    """

    _layers: list[IngressReader]

    def __init__(self, layers: Sequence[IngressReader]) -> None:
        self._layers = list(layers)

    @property
    def layers(self) -> Sequence[IngressReader]:
        return tuple(self._layers)

    @override
    async def get(self, frontend_key: IngressFrontendKey) -> Ingress | None:
        in_memory = self._in_memory()
        try:
            for index, layer in enumerate(self._layers):
                ingress = await layer.get(frontend_key)
                if ingress is None:
                    continue
                if in_memory is not None and index > 0:
                    # Cache a later layer's hit in memory so the next read stops at memory.
                    await in_memory.apply([ingress])
                return ingress
            if in_memory is not None:
                # Remember a key no layer holds so the next read skips the later layers.
                await in_memory.remember_missing(frontend_key)
            return None
        except IngressNotFoundError:
            # The key was remembered missing on purpose to skip reading the later layers.
            return None

    @override
    async def get_all(self) -> list[Ingress]:
        return await self._layers[-1].get_all()

    def _in_memory(self) -> InMemoryIngressState | None:
        # The config puts the in-memory layer first whenever it is configured.
        first_layer = self._layers[0]
        return first_layer if isinstance(first_layer, InMemoryIngressState) else None
