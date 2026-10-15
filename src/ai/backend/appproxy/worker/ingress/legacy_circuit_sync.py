from __future__ import annotations

from collections.abc import Sequence

from ai.backend.appproxy.worker.ingress.abc import IngressWriter
from ai.backend.appproxy.worker.types import Circuit
from ai.backend.common.dto.appproxy.v2.ingress.types import IngressAuthority, IngressKey


class LegacyCircuitIngressSync:
    """Writes the Ingress of each circuit the legacy circuit events carry to the in-memory state.

    Temporary: remove it together with the legacy circuit events.
    """

    _writer: IngressWriter
    _authority: IngressAuthority

    def __init__(self, writer: IngressWriter, authority: IngressAuthority) -> None:
        self._writer = writer
        self._authority = authority

    async def upsert_circuits(self, circuits: Sequence[Circuit]) -> None:
        await self._writer.apply([circuit.to_ingress(self._authority) for circuit in circuits])

    async def remove_circuits(self, circuits: Sequence[Circuit]) -> None:
        await self._writer.remove([
            IngressKey(authority=self._authority, frontend_key=circuit.to_ingress_frontend().key())
            for circuit in circuits
        ])
