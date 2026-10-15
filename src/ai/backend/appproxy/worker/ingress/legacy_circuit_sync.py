from __future__ import annotations

import logging
from collections.abc import Sequence

from ai.backend.appproxy.common.types import RouteInfo
from ai.backend.appproxy.worker.ingress.abc import IngressWriter
from ai.backend.appproxy.worker.types import Circuit
from ai.backend.common.dto.appproxy.v2.ingress.types import IngressAuthority, IngressKey
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


class LegacyCircuitIngressSync:
    """Writes the Ingress of each circuit the legacy circuit events carry to the in-memory state.

    Temporary: remove it together with the legacy circuit events. Nothing serves from the state
    yet, so a failed write is logged and skipped instead of failing the circuit event.
    """

    _writer: IngressWriter
    _authority: IngressAuthority

    def __init__(self, writer: IngressWriter, authority: IngressAuthority) -> None:
        self._writer = writer
        self._authority = authority

    async def apply(self, circuit: Circuit, routes: Sequence[RouteInfo]) -> None:
        try:
            await self._writer.apply([circuit.to_ingress(self._authority, routes)])
        except Exception:
            log.exception("failed to apply the circuit ingress", circuit_id=circuit.id)

    async def remove(self, circuits: Sequence[Circuit]) -> None:
        for circuit in circuits:
            try:
                await self._writer.remove([
                    IngressKey(
                        authority=self._authority,
                        frontend_key=circuit.to_ingress_frontend().key(),
                    )
                ])
            except Exception:
                log.exception("failed to remove the circuit ingress", circuit_id=circuit.id)
