from __future__ import annotations

import itertools
from collections import defaultdict
from collections.abc import Iterator, Sequence

from ai.backend.appproxy.common.types import RouteInfo
from ai.backend.appproxy.worker.ingress.abc import IngressWriter
from ai.backend.appproxy.worker.types import Circuit
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    IngressAuthority,
    IngressFrontendKey,
    IngressKey,
)


class LegacyCircuitIngressSync:
    """Writes the Ingress of each circuit the legacy circuit events carry to the in-memory state.

    Temporary: remove it together with the legacy circuit events.
    """

    _writer: IngressWriter
    _authority: IngressAuthority
    _revisions: defaultdict[IngressFrontendKey, Iterator[int]]

    def __init__(self, writer: IngressWriter, authority: IngressAuthority) -> None:
        self._writer = writer
        self._authority = authority
        # Circuits carry no revision; each frontend numbers its changes in arrival order.
        self._revisions = defaultdict(itertools.count)

    async def replace_all(self, circuits: Sequence[Circuit]) -> None:
        self._revisions.clear()
        await self._writer.replace_all([
            circuit.to_ingress(
                self._authority,
                next(self._revisions[circuit.to_ingress_frontend().key()]),
                circuit.route_info,
            )
            for circuit in circuits
        ])

    async def apply(self, circuit: Circuit, routes: Sequence[RouteInfo]) -> None:
        await self._writer.apply([
            circuit.to_ingress(
                self._authority, next(self._revisions[circuit.to_ingress_frontend().key()]), routes
            )
        ])

    async def remove(self, circuits: Sequence[Circuit]) -> None:
        frontend_keys = [circuit.to_ingress_frontend().key() for circuit in circuits]
        for frontend_key in frontend_keys:
            self._revisions.pop(frontend_key, None)
        await self._writer.remove([
            IngressKey(authority=self._authority, frontend_key=frontend_key)
            for frontend_key in frontend_keys
        ])
