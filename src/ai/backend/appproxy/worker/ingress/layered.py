from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.appproxy.worker.errors.ingress import IngressNotFoundError
from ai.backend.appproxy.worker.ingress.abc import IngressReader, IngressWriter
from ai.backend.appproxy.worker.ingress.in_memory import InMemoryIngressState
from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress, IngressFrontendKey


class LayeredIngressState(IngressReader):
    """Reads the layers in order; a hit is applied to the earlier layers that are writers.

    A key a layer knows missing, or one every layer misses, reads as None.
    """

    _layers: list[IngressReader]

    def __init__(self, layers: Sequence[IngressReader]) -> None:
        self._layers = list(layers)

    @property
    def layers(self) -> Sequence[IngressReader]:
        return tuple(self._layers)

    @override
    async def get(self, frontend_key: IngressFrontendKey) -> Ingress | None:
        for index, layer in enumerate(self._layers):
            try:
                ingress = await layer.get(frontend_key)
            except IngressNotFoundError:
                # The key was remembered missing on purpose to skip reading the later layers.
                return None
            if ingress is None:
                continue
            for earlier_layer in self._layers[:index]:
                if isinstance(earlier_layer, IngressWriter):
                    await earlier_layer.apply([ingress])
            return ingress
        for layer in self._layers:
            if isinstance(layer, InMemoryIngressState):
                await layer.remember_missing(frontend_key)
        return None

    @override
    async def get_all(self) -> list[Ingress]:
        return await self._layers[-1].get_all()
