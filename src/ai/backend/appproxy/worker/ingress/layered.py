from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.appproxy.worker.errors.ingress import IngressNotFoundError
from ai.backend.appproxy.worker.ingress.abc import IngressReader
from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress, IngressFrontendKey


class LayeredIngressState(IngressReader):
    """Reads the layers in order; a hit is kept by the earlier layers.

    A key a layer knows missing, or one no layer holds, reads as None.
    """

    _layers: list[IngressReader]

    def __init__(self, layers: Sequence[IngressReader]) -> None:
        self._layers = list(layers)

    @property
    def layers(self) -> Sequence[IngressReader]:
        return tuple(self._layers)

    @override
    async def get(self, frontend_key: IngressFrontendKey) -> Ingress | None:
        try:
            for index, layer in enumerate(self._layers):
                ingress = await layer.get(frontend_key)
                if ingress is not None:
                    for earlier_layer in self._layers[:index]:
                        await earlier_layer.keep(ingress)
                    return ingress
            for layer in self._layers:
                await layer.remember_missing(frontend_key)
            return None
        except IngressNotFoundError:
            # The key was remembered missing on purpose to skip reading the later layers.
            return None

    @override
    async def get_all(self) -> list[Ingress]:
        return await self._layers[-1].get_all()
