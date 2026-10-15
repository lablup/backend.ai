from __future__ import annotations

import itertools
from collections.abc import Iterator, Sequence

from ai.backend.appproxy.common.types import RouteInfo
from ai.backend.appproxy.worker.ingress.abc import IngressWriter
from ai.backend.appproxy.worker.types import Circuit
from ai.backend.common.dto.appproxy.v2.ingress.types import IngressAuthority, IngressKey


class CircuitIngressSync:
    """Writes the Ingress of each circuit the existing circuit events carry to the in-memory state.

    A circuit without routes has no target group to carry, so its Ingress is removed instead.
    """

    _writer: IngressWriter
    _authority: IngressAuthority
    _revisions: Iterator[int]

    def __init__(self, writer: IngressWriter, authority: IngressAuthority) -> None:
        self._writer = writer
        self._authority = authority
        # Circuits carry no revision; numbering them in arrival order keeps the last write winning.
        self._revisions = itertools.count()

    async def replace_all(self, circuits: Sequence[Circuit]) -> None:
        await self._writer.replace_all([
            circuit.to_ingress(self._authority, next(self._revisions), circuit.route_info)
            for circuit in circuits
            if circuit.route_info
        ])

    async def apply(self, circuit: Circuit, routes: Sequence[RouteInfo]) -> None:
        if routes:
            await self._writer.apply([
                circuit.to_ingress(self._authority, next(self._revisions), routes)
            ])
        else:
            await self.remove([circuit])

    async def remove(self, circuits: Sequence[Circuit]) -> None:
        await self._writer.remove([
            IngressKey(authority=self._authority, frontend_key=circuit.to_ingress_frontend().key())
            for circuit in circuits
        ])
