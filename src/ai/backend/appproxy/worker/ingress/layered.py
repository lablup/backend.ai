from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.appproxy.worker.ingress.abc import IngressReader
from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress, IngressFrontendKey
from ai.backend.common.exception import GenericNotImplementedError


class LayeredIngressState(IngressReader):
    """Reads the layers in order; a hit is applied to the earlier layers that are writers."""

    _layers: list[IngressReader]

    def __init__(self, layers: Sequence[IngressReader]) -> None:
        self._layers = list(layers)

    @property
    def layers(self) -> Sequence[IngressReader]:
        return tuple(self._layers)

    @override
    async def get(self, frontend_key: IngressFrontendKey) -> Ingress | None:
        # Return the first hit in layer order and apply it to the earlier writer layers. Stop at
        # IngressNotFoundError; a miss in every layer is passed to remember_missing.
        raise GenericNotImplementedError

    @override
    async def get_all(self) -> list[Ingress]:
        # Return the last layer's full set.
        raise GenericNotImplementedError
